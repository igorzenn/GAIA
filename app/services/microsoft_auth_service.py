import msal 
from app.config import settings
from datetime import datetime, timedelta, timezone

_cached_access_token: str | None = None
_cached_expires_at: datetime | None = None 

def get_graph_delegated_access_token() -> str:
    global _cached_access_token
    global _cached_expires_at

    if _cached_access_token and _cached_expires_at: 
        if datetime.now(timezone.utc) < _cached_expires_at:
            return _cached_access_token

    if not settings.microsoft_tenant_id:
        raise ValueError("MICROSOFT_TENANT_ID não configurado")

    if not settings.microsoft_client_id:
        raise ValueError("MICROSOFT_CLIENT_ID não configurado")

    authority = (
        f"https://login.microsoftonline.com/"
        f"{settings.microsoft_tenant_id}"
    )

    app = msal.PublicClientApplication(
        client_id=settings.microsoft_client_id,
        authority=authority
    )

    scopes = [
        "User.Read",
        "Calendars.ReadWrite"
    ]

    flow = app.initiate_device_flow(scopes=scopes)

    if "user_code" not in flow:
        error_description = flow.get(
            "error_description",
            str(flow)
        )
        raise ValueError(
            f"Não foi possível iniciar o Device Code Flow: {error_description}"
        )

    print(flow["message"])

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        error_description = result.get(
            "error_description",
            "Erro desconhecido ao obter token delegado"
        )

        raise ValueError(
            f"Erro ao obter token delegado Microsoft Graph: {error_description}"
        )
    
    expires_in = result.get("experies_in", 3600)

    _cached_access_token = result["access_token"]
    _cached_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=expires_in - 60
    )

    return _cached_access_token