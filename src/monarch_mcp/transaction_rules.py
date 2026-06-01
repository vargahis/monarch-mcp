# pylint: disable=too-few-public-methods
"""GraphQL operations, typed input models, and helpers for transaction rules.

The community ``monarchmoneycommunity`` library does not currently wrap
the transaction-rules GraphQL surface, so we drive the operations
directly via ``client.gql_call`` using documents sniffed from the
official Monarch Money web app.

What this module exposes for the MCP server:

* The GraphQL documents (``GET_RULES_QUERY``, ``CREATE_RULE_MUTATION``,
  ``UPDATE_RULE_MUTATION``, ``DELETE_RULE_MUTATION``).
* Pydantic input models — :class:`CreateTransactionRuleInput` and
  :class:`UpdateTransactionRuleInput` — that capture the full rule
  surface (criteria + actions). FastMCP expands these into the tool's
  JSON schema, so an agent sees every field/type, and Pydantic
  validates input before it ever reaches the API. Snake-case Python
  fields serialise to Monarch's camelCase via ``to_camel`` aliases.
* :func:`rule_to_update_input` — merges caller overrides onto an
  existing rule. Necessary because the update mutation has *replace*
  semantics: any field omitted from the payload is reset to ``null``
  server-side.
* :func:`normalize_rule` — flattens a rule from ``GetTransactionRules``
  into a clean ``__typename``-free dict (a superset of the original
  slim shape) for the read tool.
* :func:`extract_payload_errors` — normalises a mutation's ``errors``
  payload (``None`` / dict / list) to a list.
"""

from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel


# ── GraphQL documents ──────────────────────────────────────────────────


GET_RULES_QUERY = """
query GetTransactionRules {
  transactionRules {
    id
    order
    ...TransactionRuleFields
    __typename
  }
}

fragment TransactionRuleFields on TransactionRuleV2 {
  id
  merchantCriteriaUseOriginalStatement
  merchantCriteria { operator value __typename }
  originalStatementCriteria { operator value __typename }
  merchantNameCriteria { operator value __typename }
  amountCriteria {
    operator isExpense value
    valueRange { lower upper __typename }
    __typename
  }
  categoryIds
  accountIds
  categories { id name icon __typename }
  accounts { id displayName icon logoUrl __typename }
  criteriaOwnerIsJoint
  criteriaOwnerUserIds
  criteriaOwnerUsers { id displayName profilePictureUrl __typename }
  criteriaBusinessEntityIds
  criteriaBusinessEntityIsUnassigned
  criteriaBusinessEntities { id name logoUrl color __typename }
  setMerchantAction { id name __typename }
  setCategoryAction { id name icon __typename }
  addTagsAction { id name color __typename }
  linkGoalAction { id name imageStorageProvider imageStorageProviderId __typename }
  linkSavingsGoalAction { id name imageStorageProvider imageStorageProviderId __typename }
  needsReviewByUserAction { id displayName __typename }
  unassignNeedsReviewByUserAction
  sendNotificationAction
  setHideFromReportsAction
  reviewStatusAction
  actionSetOwnerIsJoint
  actionSetOwner { id displayName profilePictureUrl __typename }
  actionSetBusinessEntity { id name logoUrl color __typename }
  actionSetBusinessEntityIsUnassigned
  recentApplicationCount
  lastAppliedAt
  splitTransactionsAction {
    amountType
    splitsInfo {
      categoryId merchantName amount goalId savingsGoalId tags
      hideFromReports reviewStatus needsReviewByUserId ownerUserId
      ownerIsJoint businessEntityId businessEntityIsUnassigned
      __typename
    }
    __typename
  }
  __typename
}
"""


CREATE_RULE_MUTATION = """
mutation Common_CreateTransactionRuleMutationV2($input: CreateTransactionRuleInput!) {
  createTransactionRuleV2(input: $input) {
    errors { ...PayloadErrorFields __typename }
    __typename
  }
}

fragment PayloadErrorFields on PayloadError {
  fieldErrors { field messages __typename }
  message code __typename
}
"""


UPDATE_RULE_MUTATION = """
mutation Common_UpdateTransactionRuleMutationV2($input: UpdateTransactionRuleInput!) {
  updateTransactionRuleV2(input: $input) {
    errors {
      fieldErrors { field messages __typename }
      message code __typename
    }
    __typename
  }
}
"""


DELETE_RULE_MUTATION = """
mutation Common_DeleteTransactionRule($id: ID!) {
  deleteTransactionRule(id: $id) {
    deleted
    errors {
      fieldErrors { field messages __typename }
      message code __typename
    }
    __typename
  }
}
"""


# ── Typed input models ─────────────────────────────────────────────────


class _RuleModel(BaseModel):
    """Base config for rule input models.

    Snake-case Python fields map to Monarch's camelCase wire names via
    ``to_camel`` aliases; ``populate_by_name`` lets callers use either
    spelling; ``extra="allow"`` lets exotic/future Monarch fields pass
    through untouched (forward-compatible).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )


class Criterion(_RuleModel):
    """A merchant-name / original-statement / merchant match criterion."""

    operator: Literal["contains", "eq"]
    value: str


class ValueRange(_RuleModel):
    """Lower/upper bounds for a ``between`` amount criterion."""

    lower: Optional[float] = None
    upper: Optional[float] = None


class AmountCriteria(_RuleModel):
    """Match on transaction amount."""

    operator: str
    is_expense: Optional[bool] = None
    value: Optional[float] = None
    value_range: Optional[ValueRange] = None


class SplitInfo(_RuleModel):
    """One leg of a ``splitTransactionsAction`` split."""

    category_id: Optional[str] = None
    merchant_name: Optional[str] = None
    amount: Optional[float] = None
    goal_id: Optional[str] = None
    savings_goal_id: Optional[str] = None
    tags: Optional[List[str]] = None
    hide_from_reports: Optional[bool] = None
    review_status: Optional[str] = None
    needs_review_by_user_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    owner_is_joint: Optional[bool] = None
    business_entity_id: Optional[str] = None
    business_entity_is_unassigned: Optional[bool] = None


class SplitTransactionsAction(_RuleModel):
    """Split a matched transaction into multiple legs.

    ``amount_type`` must be one of Monarch's ``SplitAmountType`` values —
    ``ABSOLUTE`` (per-leg dollar amounts) or ``PERCENTAGE`` (per-leg fractions
    that sum to 1). Monarch's API silently *stores* an out-of-set value and then
    fails to serialize it on read, so we validate it here rather than mint an
    unreadable rule. At least two splits are required.
    """

    amount_type: Literal["ABSOLUTE", "PERCENTAGE"]
    splits_info: List[SplitInfo]


class _RuleInputFields(_RuleModel):
    """Shared field set for create/update rule inputs."""

    # ── criteria ──
    merchant_criteria_use_original_statement: Optional[bool] = None
    merchant_criteria: Optional[List[Criterion]] = None
    original_statement_criteria: Optional[List[Criterion]] = None
    merchant_name_criteria: Optional[List[Criterion]] = None
    amount_criteria: Optional[AmountCriteria] = None
    category_ids: Optional[List[str]] = None
    account_ids: Optional[List[str]] = None
    # ── actions ──
    set_merchant_action: Optional[str] = None
    set_category_action: Optional[str] = None
    add_tags_action: Optional[List[str]] = None
    link_goal_action: Optional[str] = None
    link_savings_goal_action: Optional[str] = None
    review_status_action: Optional[str] = None
    split_transactions_action: Optional[SplitTransactionsAction] = None
    # ── behaviour ──
    apply_to_existing_transactions: Optional[bool] = None


_ACTION_FIELDS: Tuple[str, ...] = (
    "set_merchant_action",
    "set_category_action",
    "add_tags_action",
    "link_goal_action",
    "link_savings_goal_action",
    "review_status_action",
    "split_transactions_action",
)


class CreateTransactionRuleInput(_RuleInputFields):
    """Input for ``create_transaction_rule``.

    Supply at least one criterion and at least one action. For example,
    a category rule needs ``merchant_name_criteria`` + ``set_category_action``;
    a tagging rule adds ``add_tags_action``; a split rule uses
    ``split_transactions_action``.
    """

    @model_validator(mode="after")
    def _require_action(self) -> "CreateTransactionRuleInput":
        has_action = any(getattr(self, name) is not None for name in _ACTION_FIELDS)
        if not has_action and not self.__pydantic_extra__:
            raise ValueError(
                "a transaction rule needs at least one action, e.g. "
                "set_category_action, add_tags_action, set_merchant_action, "
                "or split_transactions_action"
            )
        return self


class UpdateTransactionRuleInput(_RuleInputFields):
    """Partial overrides for ``update_transaction_rule``.

    Only the fields you set are applied; the rest of the rule is
    preserved by merging onto the current rule (see
    :func:`rule_to_update_input`).
    """


# ── Helpers ────────────────────────────────────────────────────────────


RULE_INPUT_FIELDS: Tuple[str, ...] = (
    "merchantCriteriaUseOriginalStatement",
    "merchantCriteria",
    "originalStatementCriteria",
    "merchantNameCriteria",
    "amountCriteria",
    "categoryIds",
    "accountIds",
    "setMerchantAction",
    "setCategoryAction",
    "addTagsAction",
    "linkGoalAction",
    "linkSavingsGoalAction",
    "reviewStatusAction",
    "splitTransactionsAction",
    "applyToExistingTransactions",
)


def _strip_meta(obj: Any) -> Any:
    """Recursively strip ``__typename`` keys from any nested mappings/lists."""
    if isinstance(obj, dict):
        return {k: _strip_meta(v) for k, v in obj.items() if k != "__typename"}
    if isinstance(obj, list):
        return [_strip_meta(item) for item in obj]
    return obj


def _extract_id(value: Any) -> Any:
    """Return ``value['id']`` when value is a dict, else value untouched."""
    if isinstance(value, dict):
        return value.get("id", value)
    return value


def _extract_ids(value: Any) -> Any:
    """Map a list of ``{id, ...}`` dicts to a list of plain ids."""
    if isinstance(value, list):
        return [_extract_id(item) for item in value]
    return value


def rule_to_update_input(
    rule: Dict[str, Any],
    overrides: Dict[str, Any],
) -> Dict[str, Any]:
    """Build an ``UpdateTransactionRuleInput`` payload.

    The ``updateTransactionRuleV2`` mutation has *replace* semantics:
    any input field omitted is reset to ``null``.  This helper preserves
    the existing rule by copying every input-shaped field from the
    fetched rule, layering ``overrides`` on top, and normalising the
    nested action shapes (which the read fragment expands into objects
    but the input expects as plain ids / strings).

    Args:
        rule: The rule as returned by ``GetTransactionRules`` (a single
            entry from ``transactionRules``).
        overrides: User-supplied field overrides (camelCase keys). Any
            key in :data:`RULE_INPUT_FIELDS` wins over the existing value.

    Returns:
        A dict suitable as the ``input`` variable of the update
        mutation, including the rule's ``id``.
    """
    payload: Dict[str, Any] = {"id": rule["id"]}

    for field in RULE_INPUT_FIELDS:
        if field in overrides:
            payload[field] = _strip_meta(overrides[field])
            continue
        if field not in rule:
            continue
        value = _strip_meta(rule[field])
        if field == "setMerchantAction" and isinstance(value, dict):
            # Input expects the merchant *name* string, not the object.
            payload[field] = value.get("name")
        elif field in (
            "setCategoryAction",
            "linkGoalAction",
            "linkSavingsGoalAction",
        ):
            payload[field] = _extract_id(value)
        elif field == "addTagsAction":
            payload[field] = _extract_ids(value)
        else:
            payload[field] = value

    return payload


def _criteria_list(items: Any) -> List[Dict[str, Any]]:
    """Flatten a criteria array to ``[{operator, value}, ...]``."""
    return [
        {"operator": c.get("operator"), "value": c.get("value")}
        for c in (items or [])
        if isinstance(c, dict)
    ]


def normalize_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a rule from ``GetTransactionRules`` into a clean dict.

    Strips ``__typename`` and exposes a snake-case shape that is a
    *superset* of the original slim read tool (``id`` + category +
    merchant/statement criteria), adding the richer criteria, actions,
    and application stats.
    """
    rule = _strip_meta(rule)
    category = rule.get("setCategoryAction") or {}
    merchant = rule.get("setMerchantAction") or {}
    goal = rule.get("linkGoalAction") or {}
    savings_goal = rule.get("linkSavingsGoalAction") or {}
    tags = rule.get("addTagsAction") or []
    return {
        "id": rule.get("id"),
        "order": rule.get("order"),
        # ── slim shape preserved (backwards-compatible keys) ──
        "set_category_id": _extract_id(category),
        "set_category_name": category.get("name") if isinstance(category, dict) else None,
        "merchant_name_criteria": _criteria_list(rule.get("merchantNameCriteria")),
        "original_statement_criteria": _criteria_list(rule.get("originalStatementCriteria")),
        # ── richer criteria ──
        "merchant_criteria": _criteria_list(rule.get("merchantCriteria")),
        "merchant_criteria_use_original_statement": rule.get(
            "merchantCriteriaUseOriginalStatement"
        ),
        "amount_criteria": rule.get("amountCriteria"),
        "category_ids": rule.get("categoryIds"),
        "account_ids": rule.get("accountIds"),
        # ── richer actions ──
        "set_merchant_name": merchant.get("name") if isinstance(merchant, dict) else merchant,
        "add_tag_ids": [t.get("id") for t in tags if isinstance(t, dict)],
        "add_tag_names": [t.get("name") for t in tags if isinstance(t, dict)],
        "link_goal_id": _extract_id(goal),
        "link_savings_goal_id": _extract_id(savings_goal),
        "review_status_action": rule.get("reviewStatusAction"),
        "set_hide_from_reports_action": rule.get("setHideFromReportsAction"),
        "split_transactions_action": rule.get("splitTransactionsAction"),
        # ── stats ──
        "recent_application_count": rule.get("recentApplicationCount"),
        "last_applied_at": rule.get("lastAppliedAt"),
    }


def extract_payload_errors(result: Any, field: str) -> List[Dict[str, Any]]:
    """Normalise a mutation payload's ``errors`` to a list.

    ``errors`` may be ``None`` (success), a bare dict, or a list.

    Args:
        result: The raw ``gql_call`` result.
        field: The mutation field name (e.g. ``createTransactionRuleV2``).
    """
    payload = result.get(field, {}) if isinstance(result, dict) else {}
    raw = payload.get("errors") if isinstance(payload, dict) else None
    if isinstance(raw, dict):
        raw = [raw]
    return raw or []


__all__: Iterable[str] = (
    "GET_RULES_QUERY",
    "CREATE_RULE_MUTATION",
    "UPDATE_RULE_MUTATION",
    "DELETE_RULE_MUTATION",
    "Criterion",
    "ValueRange",
    "AmountCriteria",
    "SplitInfo",
    "SplitTransactionsAction",
    "CreateTransactionRuleInput",
    "UpdateTransactionRuleInput",
    "RULE_INPUT_FIELDS",
    "rule_to_update_input",
    "normalize_rule",
    "extract_payload_errors",
)
