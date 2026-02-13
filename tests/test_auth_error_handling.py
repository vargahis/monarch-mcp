"""is_auth_error unit tests (5 tests)."""
# pylint: disable=missing-function-docstring

from gql.transport.exceptions import TransportServerError
from monarchmoney import LoginFailedException

from monarch_mcp_server.secure_session import is_auth_error


# ===================================================================
# is_auth_error unit tests
# ===================================================================


def test_transport_401():
    exc = TransportServerError("Unauthorized", code=401)
    assert is_auth_error(exc) is True


def test_transport_403_json():
    cause = Exception("403 Forbidden")
    cause.headers = {"content-type": "application/json"}
    exc = TransportServerError("Forbidden", code=403)
    exc.__cause__ = cause
    assert is_auth_error(exc) is True


def test_transport_403_html_waf():
    cause = Exception("403 Forbidden")
    cause.headers = {"content-type": "text/html"}
    exc = TransportServerError("Forbidden", code=403)
    exc.__cause__ = cause
    assert is_auth_error(exc) is False


def test_login_failed():
    exc = LoginFailedException()
    assert is_auth_error(exc) is True


def test_generic_exception():
    assert is_auth_error(Exception("random error")) is False
