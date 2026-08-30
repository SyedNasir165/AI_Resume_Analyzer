from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.services.supabase_admin import SupabaseAdminError, delete_user

router = APIRouter(tags=["me"])


@router.get("/api/me")
def read_current_user(current_user: TokenPayload = Depends(get_current_user)) -> dict[str, str]:
    return {"id": current_user.user_id, "email": current_user.email or ""}


@router.delete("/api/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user: TokenPayload = Depends(get_current_user)) -> None:
    """Permanently delete the current user's account and all of their data."""
    try:
        delete_user(current_user.user_id)
    except SupabaseAdminError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
