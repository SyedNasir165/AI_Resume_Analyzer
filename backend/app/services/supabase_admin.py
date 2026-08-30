"""Supabase Auth Admin operations that need the service-role key (backend only)."""

import httpx

from app.core.config import get_settings

REQUEST_TIMEOUT_SECONDS = 30


class SupabaseAdminError(Exception):
    """Raised when a Supabase admin operation cannot be completed."""


def delete_user(user_id: str) -> None:
    """Permanently delete a Supabase auth user.

    Deleting the auth user cascades through the database foreign keys (auth.users -> profiles ->
    resumes -> analyses), so this removes all of the user's data.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SupabaseAdminError("Account deletion is not configured on the server.")

    url = f"{settings.supabase_url}/auth/v1/admin/users/{user_id}"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    try:
        response = httpx.delete(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        raise SupabaseAdminError("Could not reach the authentication service.") from exc

    if response.status_code not in (200, 204):
        raise SupabaseAdminError(f"Account deletion failed (status {response.status_code}).")
