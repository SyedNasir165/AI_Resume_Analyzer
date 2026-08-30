from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.security import TokenPayload, verify_access_token

bearer_scheme = HTTPBearer(auto_error=False)

# Shared per-process limiter for the AI-calling endpoints (analysis + coach).
ai_rate_limiter = RateLimiter(get_settings().ai_rate_limit_per_minute, 60.0)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    return verify_access_token(credentials.credentials)


def enforce_ai_rate_limit(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """Authenticate, then enforce the per-user AI request budget (429 when exceeded)."""
    if not ai_rate_limiter.allow(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You've made too many analysis requests. Please wait a minute and try again.",
        )
    return current_user
