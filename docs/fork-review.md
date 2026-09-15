# Fork Review — upstream `vargahis/monarch-mcp`

Review date: 2026-09-15. Base reviewed: `origin/main` @ `7299fdc`.
All 9 forks inspected, every branch on each (not just `main`).

Baseline quality gates before any change: **294 passed, pylint 10.00/10**.

---

## 1. Executive summary

Of the 9 forks, **6 contain no original work at all** — their "ahead" branches are
byte-identical mirrors of upstream's own feature branches, copied at fork time. Only
**4 forks carry commits that do not exist upstream**, and they cluster on two themes:
**authentication** and **client robustness**.

The single most important finding did not come from any one fork wholesale — it came
from cross-reading two of them: **upstream `main` today has an arbitrary-code-execution
path in its environment-credential login** (§4.1). Both `somanshreddy` and
`kylegrantlucas` fixed it independently, by different means, and neither ever reported
it upstream.

Recommended actions, in priority order:

| # | Change | Source | Risk | Effort |
|---|---|---|---|---|
| 1 | Pin off the pickle session flags (RCE fix) | synthesis | low | ~10 min |
| 2 | Configurable client timeout (10s → 30s) | `jimmyjoy43` | very low | merge as-is |
| 3 | CSRF state-token nonce (defence in depth) | `bryanhull` | low | ~1 hr |
| 4 | Headless TOTP MFA via `MONARCH_MFA_SECRET` | `kylegrantlucas` | medium | ~2 hr |
| 5 | Bump `monarchmoneycommunity` 1.3.2 → 1.5.2 | 3 forks | medium | needs live test |
| 6 | Investigate cookie auth as fallback | `josh-devcloud` | high | spike first |
| — | Google OAuth via Playwright / Gmail IMAP MFA | `bryanhull` | high | **decline** |

---

## 2. Fork-by-fork inventory

| Fork | Last push | Original work? | Verdict |
|---|---|---|---|
| `josh-devcloud` | 2026-08-16 | **Yes** — 4 commits on `main` | Cookie auth rewrite — §4.6 |
| `jimmyjoy43` | 2026-07-25 | **Yes** — 2 commits | **Merge as-is** — §4.2 |
| `somanshreddy` | 2026-07-11 | **Yes** — 4 commits on `main` | Security + CLI — §4.1, §4.4 |
| `kylegrantlucas` | 2026-09-09 | **Yes** — 3 commits on `headless-mfa-login` | Headless MFA — §4.5 |
| `bryanhull` | 2026-03-08 | **Yes** — 4 branches | Mixed — §4.3, §4.7 |
| `GilbertoAbrao` | 2026-06-01 | No (all merged) | Already upstream via PRs #33/#34/#35 |
| `MDJ07853` | 2026-06-12 | No | Pure mirror |
| `therealdeadfwd` | 2026-06-12 | No | Pure mirror, 0 ahead / 0 behind |
| `tonloc69-ops` | 2026-03-28 | No | Pure mirror, 21 behind |

### Note on false positives

A naive `git log origin/main..<fork>/<branch>` reports ~6 "ahead" branches on most
forks. These are **not** fork contributions. Verified by SHA comparison — e.g.
`chore/bump-actions-node24` is `46cc1d0` on origin *and* on josh-devcloud,
kylegrantlucas and somanshreddy. Same for `claude/auto-trigger-auth-on-startup-dZlyN`,
`feature/auth-server-csrf-hardening`, `feature/pypi-release`, `feature/wsl2-auth` and
`feature/transaction-rule-management`. They look "ahead" only because those upstream
branches were squash-merged (or, for `feature/wsl2-auth`, PR #17, closed unmerged).

`GilbertoAbrao/fix/native-async-tools` likewise looks ahead by 2, but it is PR #33,
already merged.

---

## 3. What the underlying library actually supports

Several fork claims needed checking against the real library rather than taken on
trust. Downloaded and inspected `monarchmoneycommunity` **1.5.2**
(upstream currently pins `~=1.3.2`, i.e. `>=1.3.2,<1.4.0` — two minor versions behind):

- `MonarchMoney.__init__(..., timeout: int = 10, ...)` — **exists**, so §4.2 is valid.
- `set_cookies()` + `REQUIRED_COOKIES = ("session_id", "csrftoken")` — **exists**, so
  §4.6's cookie auth is grounded in a real library API, not invented.
- `login(..., mfa_secret_key=...)` → `oathtool.generate_otp(...)` — **exists**, so
  §4.5's headless TOTP is real.
- `SESSION_DIR = ".mm"` / `SESSION_FILE = ".mm/mm_session.pickle"`, with
  `login(use_saved_session=True, save_session=True)` by default, `pickle.dump` on save
  and `pickle.load` on use — **confirmed**, which is what makes §4.1 a live bug.

---

## 4. Findings

### 4.1 🔴 Arbitrary code execution in the env-credential login path

**Sources:** `somanshreddy` (`7b55f72`), and independently `kylegrantlucas` (`73da0fe`).
**Status: affects `origin/main` right now.**

`src/monarch_mcp/server.py` calls:

```python
await client.login(email, password)
```

That takes the library defaults `use_saved_session=True, save_session=True`, which means:

1. On success the session token is written as an **unencrypted pickle** to
   `.mm/mm_session.pickle`, resolved against the **process CWD** — under Claude Desktop
   that is not a directory the user picked.
2. On the *next* login the library does
   `if use_saved_session and os.path.exists(...): self.load_session(...)` →
   `pickle.load(fh)`, **before any credential check**. `pickle.load()` on a file an
   attacker can drop into CWD is arbitrary code execution, in a process holding a live
   Monarch session.

The existing `_cleanup_old_session_files()` does **not** save us: it deletes
`.mm/mm_session.pickle` *after* login returns, whereas the dangerous `pickle.load`
happens *during* it. The browser flow already avoids this (it passes both flags
`False`); only the env-credential path is exposed.

The two forks diverge on the remedy:

- **`somanshreddy`** removes the `MONARCH_EMAIL`/`MONARCH_PASSWORD` path entirely,
  making the keyring the only credential store, and adds a regression test asserting
  env credentials no longer authenticate. Thorough, but it deletes a documented feature.
- **`kylegrantlucas`** keeps the feature and just pins the flags off.

**Recommendation — take neither verbatim; apply the minimal fix:**

```python
await client.login(
    email,
    password,
    use_saved_session=False,
    save_session=False,
)
```

**Verified:** applied to `origin/main`, pylint stays **10.00/10**. One test,
`tests/test_server_edge_cases.py::test_get_client_env_credentials`, fails purely
because it asserts the old call signature:

```
Expected: login('user@test.com', 'secret123')
  Actual: login('user@test.com', 'secret123', use_saved_session=False, save_session=False)
```

So the merge is: the 4-line source change plus that one mock assertion, then add a
regression test pinning both flags to `False`. Worth also borrowing somanshreddy's
fix to `tests/integration/conftest.py`, which has the same defaulted `login()` call.

---

### 4.2 🟢 Configurable client timeout — merge as-is

**Source:** `jimmyjoy43/main` (`9b614e3`, `399f303`) — **the cleanest contribution across all 9 forks.**

The library's default GraphQL timeout is 10s, which is too short for slower mutations
(reported symptom: `TimeoutError` on transaction updates). Adds
`MONARCH_MCP_TIMEOUT_SECS`, defaulting to 30, with invalid/zero/negative values logged
and falling back to the default.

Why it stands out — it already follows CLAUDE.md conventions without being asked:
documents the env var in README, adds 4 mocked unit tests (correctly routed to the
mocked tier, since this is deterministic validation logic), and even updates the test
module's docstring count from 17 → 21.

**Verified:** `git cherry-pick 9b614e3 399f303` onto current `main` applies with **zero
conflicts** → **298 passed, pylint 10.00/10**.

**Recommendation: merge as-is.** Credit jimmy joy <jimmy@jimmyjoy.in>.

---

### 4.3 🟡 CSRF state-token nonce — genuine gap in our own hardening

**Source:** `bryanhull/security/csrf-origin-state` (`67409f4`)

This overlaps our merged PR #37, and at first glance looks superseded. It is not, quite.
Our `_validate_request_origin()` does:

```python
origin = self.headers.get("Origin")
if origin is not None and origin not in self._allowed_origins():
```

— i.e. a request with **no `Origin` header at all is accepted**. bryanhull additionally
mints a `secrets`-generated nonce per auth session, embeds it in the served page,
requires it back as an `X-Auth-State` header, and compares with `hmac.compare_digest`.
That closes the Origin-absent case our check leaves open.

**Recommendation:** port just the state-token mechanism onto our existing
Host+Origin validation. Don't take the branch wholesale — it is based on pre-#37 code
and would regress our other hardening.

---

### 4.4 🟡 Login decoupled from MCP server lifecycle

**Source:** `somanshreddy` (`d60f226`), new `src/monarch_mcp/login.py` + `monarch-mcp-login` script

Identifies a real design bug: our auth server runs on a **daemon thread**, so it lives
only as long as the MCP server process. An MCP client that stops the server between
tool calls (Claude Code does exactly this) takes the login page down with it — the
browser tab points at a dead port, submitting gives a bare "Connection error", and
because each restart picks a **fresh random port**, reloading never recovers.

Their fix runs the same flow in the foreground as a standalone console command,
blocking until the token lands in the keyring.

**Recommendation:** adopt the concept. Worth confirming the symptom reproduces under
Claude Code first, then decide between their standalone-command approach and giving the
auth server a stable port.

---

### 4.5 🟡 Headless TOTP MFA

**Source:** `kylegrantlucas/headless-mfa-login` (`73da0fe`, `19a90e1`, `ed07d4e`)

Adds `MONARCH_MFA_SECRET` for non-interactive TOTP (library-supported, §3), avoids
opening a browser nobody can see when env credentials are configured, and caches the
authenticated client in-process so tools stop re-logging-in on every call.

**Caveats to fix before merging:**

- It **drops** `secure_session.save_authenticated_session(client)` from the env path, so
  the token is no longer persisted to the keyring — an in-process cache only. That is a
  behaviour regression for desktop users; the caching and the non-persistence should be
  decoupled.
- `get_runtime_client()` uses `getattr(self, "_runtime_client", None)` with the attribute
  never declared in `__init__` — likely `attribute-defined-outside-init` under our
  10.00/10 pylint gate. Declare it in `__init__`.
- Ships **no tests**. Our gate requires mocked unit tests for this.

**Recommendation:** worth taking for the headless/CI use case, but as a reworked PR, not
a cherry-pick.

---

### 4.6 🟠 Cookie-based auth — treat as intelligence, not a merge

**Source:** `josh-devcloud/main` (4 commits, most recently pushed fork at 2026-08-16)

The most consequential *claim* of the review: that Monarch **no longer permits
programmatic email/password login**, it being gated behind a browser-only
Cloudflare + client-version check. If true, our entire browser login flow is dead and
every auth path in §4.1–§4.5 is moot.

Their response is a rewrite: delete the loopback login server, have the user paste
`session_id` + `csrftoken` from DevTools into `login_setup.py`, store them in the
keyring, and override the library's hardcoded stale `monarch-client-version` header
(the library ships `"2025.05"`) with the live web app's current value.

The code is more careful than the diff size suggests — cookies are read via `getpass`
so they never echo or reach shell history, they are verified with a live `get_accounts()`
call before being kept, and deleted again if verification fails.

**Recommendation: do not merge, but act on it.** It is a 365-line rewrite that removes
working code on the strength of an unverified claim, and it pins a
`MONARCH_CLIENT_VERSION` constant that will need bumping by hand forever. But the
underlying question — *does password login still work today?* — needs an answer against
a live account, because everything else depends on it. Test that first; if password
login is indeed dead, revisit this as the basis for a **fallback** auth path rather than
a replacement.

---

### 4.7 🔴 Decline: Google OAuth via Playwright, and Gmail IMAP MFA

**Source:** `bryanhull` — `feature/google-oauth-authentication` (PR #26, still open),
`feature/zo-auth-runtime-hardening`, `feature/gmail-mfa-auto-submit`

These address a real gap — Google SSO users cannot get a token, since Monarch mints
tokens only in exchange for email+password — but the means are disproportionate:

- **Playwright browser automation.** Adds `playwright>=1.40.0` (a ~300MB browser
  download) as a hard dependency, launches a headful Chromium with
  `--disable-blink-features=AutomationControlled` and a spoofed desktop user-agent to
  evade bot detection, then sniffs the `Authorization: Token` header off in-flight
  requests. Heavyweight, fragile against Monarch UI changes, and the evasion flags
  invite terms-of-service problems.
- **Gmail IMAP MFA auto-submit.** `mfa_email.py` connects to `imap.gmail.com` with the
  user's credentials to scrape 6-digit codes out of their inbox. Asking a personal
  finance MCP server to also hold mailbox access is a large, poorly-contained expansion
  of the trust boundary.

**Recommendation: decline all three,** and say so on PR #26 so it can be closed. If
Google SSO support is wanted, §4.6's cookie-paste approach reaches the same users with
no new dependencies and no credential scraping — a much better trade.

---

## 5. Suggested sequencing

1. **Now, independently of everything else:** §4.1 (RCE) and §4.2 (timeout). Both are
   small, both are verified against the gates, neither depends on the auth question.
2. **Answer the §4.6 question next** — test password login against a live account. It
   gates how much of the rest is worth doing.
3. **Then, as separate PRs:** §4.3 (state token), §4.4 (login lifecycle), §4.5
   (headless MFA, reworked with tests).
4. **Separately:** evaluate the `monarchmoneycommunity` 1.3.2 → 1.5.2 bump that
   `josh-devcloud`, `kylegrantlucas` and (partially) others all made. Three independent
   forks converging on it is a signal, but it spans two minor versions and needs a live
   integration run.
5. **Close out:** decline PR #26 with a note pointing at §4.6 as the lighter alternative.

## 6. Reproducing this review

```bash
for f in josh-devcloud MDJ07853 jimmyjoy43 therealdeadfwd somanshreddy \
         kylegrantlucas GilbertoAbrao tonloc69-ops bryanhull; do
  git remote add "$f" "https://github.com/$f/monarch-mcp" 2>/dev/null
done
git fetch --multiple josh-devcloud MDJ07853 jimmyjoy43 therealdeadfwd \
  somanshreddy kylegrantlucas GilbertoAbrao tonloc69-ops bryanhull origin
```

Then, per branch, `git rev-list --count origin/main..<ref>` for the ahead count and
`git rev-parse origin/<branch> <fork>/<branch>` to filter out the mirror false
positives described in §2.
