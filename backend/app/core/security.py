from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import get_settings


@dataclass
class TokenPayload:
    user_id: str
    email: str | None


@lru_cache
def _jwks_client() -> PyJWKClient:
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured")
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True)


def verify_access_token(token: str) -> TokenPayload:
    """Verify a Supabase-issued access token against Supabase's public JWKS.

    Supabase signs tokens with an asymmetric key (ES256) by default, so verification
    only needs the public key fetched from the project's JWKS endpoint — no shared
    secret is stored anywhere in this backend.
    """
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            # Tolerate small clock differences between this server and Supabase's —
            # without this, a token can fail "not valid yet" for a moment right after
            # it's issued, since PyJWT checks nbf/iat with zero leeway by default.
            leeway=10,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        ) from exc

    return TokenPayload(user_id=payload["sub"], email=payload.get("email"))
