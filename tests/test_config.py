from app.core.config import get_settings


def test_cors_origins_parsing():
    s = get_settings()
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_authority_url():
    s = get_settings()
    assert s.authority == "https://login.microsoftonline.com/tenant"
