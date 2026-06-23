import httpx
import pytest

from app.core.http import TransientHTTPError, raise_for_transient, transient_retry


def test_raise_for_transient_5xx():
    req = httpx.Request("GET", "https://x/y")
    resp = httpx.Response(503, request=req)
    with pytest.raises(TransientHTTPError):
        raise_for_transient(resp)


def test_raise_for_transient_ok():
    req = httpx.Request("GET", "https://x/y")
    resp = httpx.Response(200, request=req)
    raise_for_transient(resp)  # não levanta


def test_transient_retry_eventually_raises():
    calls = {"n": 0}

    @transient_retry
    def always_fail():
        calls["n"] += 1
        raise TransientHTTPError("boom")

    with pytest.raises(TransientHTTPError):
        always_fail()
    assert calls["n"] == 4  # stop_after_attempt(4)


def test_transient_retry_recovers():
    calls = {"n": 0}

    @transient_retry
    def fail_then_ok():
        calls["n"] += 1
        if calls["n"] < 2:
            raise TransientHTTPError("boom")
        return "ok"

    assert fail_then_ok() == "ok"
    assert calls["n"] == 2
