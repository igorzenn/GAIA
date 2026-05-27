from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings 

def build_metadata(route: str | None = None, intent: str | None = None, error_type: str | None = None) -> dict: # | significa OU, então route: str | None = None, significa que route pode ser str ou none
    metadata = {
        "route": route,
        "intent": intent,
        "source": settings.app_source,
        "environment": settings.environment,
        "request_timestamp": datetime.now(ZoneInfo(settings.timezone)).isoformat(),"timezone": settings.timezone
    }

    if error_type:
        metadata["error_type"] = error_type

    return metadata 

    