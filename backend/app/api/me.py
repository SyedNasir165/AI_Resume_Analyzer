from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.security import TokenPayload

router = APIRouter(tags=["me"])


@router.get("/api/me")
def read_current_user(current_user: TokenPayload = Depends(get_current_user)) -> dict[str, str]:
    return {"id": current_user.user_id, "email": current_user.email or ""}
