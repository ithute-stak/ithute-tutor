from __future__ import annotations

from starlette.requests import Request

from database.config.config import settings
from routes import auth


def make_request(*, refresh_token: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if refresh_token is not None:
        cookie = f"{settings.REFRESH_COOKIE_NAME}={refresh_token}".encode("latin-1")
        headers.append((b"cookie", cookie))

    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/auth/refresh",
            "raw_path": b"/auth/refresh",
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


def set_cookie_headers(response) -> list[str]:
    return [value.decode("latin-1") for key, value in response.raw_headers if key.lower() == b"set-cookie"]


def test_refresh_without_cookie_ends_and_clears_tutor_session():
    response = auth.refresh(make_request(), db=None)

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    cookies = "\n".join(set_cookie_headers(response))
    assert settings.ACCESS_COOKIE_NAME in cookies
    assert settings.REFRESH_COOKIE_NAME in cookies
    assert "Max-Age=0" in cookies


def test_invalid_local_refresh_token_clears_tutor_session(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "test-secret-key-that-is-long-enough-for-tutor-only")

    response = auth.refresh(make_request(refresh_token="not-a-valid-jwt"), db=None)

    assert response.status_code == 401
    cookies = "\n".join(set_cookie_headers(response))
    assert settings.ACCESS_COOKIE_NAME in cookies
    assert settings.REFRESH_COOKIE_NAME in cookies
    assert "Max-Age=0" in cookies
