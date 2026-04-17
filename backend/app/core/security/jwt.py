"""JWT token utilities."""

import base64

import jwt

from app.core.config import get_settings

settings = get_settings()

DEFAULT_REQUIRE = ["exp", "iat", "jti", "iss", "aud"]


def jwt_encode(payload: dict) -> str:
    """Encode a JWT token."""
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def jwt_decode(
    token: str,
    *,
    require: list[str] | None = None,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict:
    """Decode a JWT token."""
    header = jwt.get_unverified_header(token)
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise ValueError("invalid header")
    options = {"require": require or DEFAULT_REQUIRE}
    kwargs: dict = {
        "key": settings.jwt_secret_key,
        "algorithms": ["HS256"],
        "options": options,
    }
    if issuer:
        kwargs["issuer"] = issuer
    if audience:
        kwargs["audience"] = audience
    return jwt.decode(token, **kwargs)


def _decode_app_token(token: str, app_client: str, issuer: str | None = None) -> dict:
    """Decode an app token."""
    claims = jwt_decode(
        token,
        require=DEFAULT_REQUIRE,
        issuer=issuer or settings.app_name,
        audience=app_client,
    )
    aud = claims.get("aud")
    if not isinstance(aud, str) or aud != app_client:
        raise ValueError("invalid audience")
    app_client_claim = claims.get("appClient")
    if app_client_claim and app_client_claim != app_client:
        raise ValueError("audience mismatch")
    return claims


def decode_access_token(token: str, app_client: str, issuer: str | None = None) -> dict:
    """Decode an access token."""
    claims = _decode_app_token(token, app_client, issuer)
    if claims.get("type") != "access":
        raise ValueError("invalid token type")
    return claims


def decode_refresh_token(token: str, app_client: str, issuer: str | None = None) -> dict:
    """Decode a refresh token."""
    claims = _decode_app_token(token, app_client, issuer)
    if claims.get("type") != "refresh":
        raise ValueError("invalid token type")
    return claims


def generate_access_token(payload: dict) -> str:
    """Generate an access token."""
    return jwt_encode({**payload, "type": "access"})


def generate_refresh_token(payload: dict) -> str:
    """Generate a refresh token."""
    return jwt_encode({**payload, "type": "refresh"})


def normalize_password(password: str) -> str:
    """Normalize a password (handle base64 encoded passwords)."""
    if not password.startswith("b64:"):
        return password
    raw = password[4:]
    try:
        decoded = base64.b64decode(raw, validate=True)
        text = decoded.decode("utf-8")
        if text:
            return text
    except Exception:
        return password
    return password
