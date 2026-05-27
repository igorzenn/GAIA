from app.config import settings


def validate_event_payload(payload: dict) -> None:
    required_fields = [
        "subject",
        "start",
        "end"
    ]

    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"Campo obrigatório ausente no payload: {field}")

    if not payload["start"].get("dateTime"):
        raise ValueError("Campo obrigatório ausente no payload: start.dateTime")

    if not payload["end"].get("dateTime"):
        raise ValueError("Campo obrigatório ausente no payload: end.dateTime")


def simulate_create_calendar_event(payload: dict) -> dict:
    validate_event_payload(payload)

    return {
        "simulated": True,
        "graph_url": f"{settings.microsoft_graph_base_url}/me/events",
        "event": {
            "id": "simulated-event-id",
            "subject": payload.get("subject"),
            "start": payload.get("start"),
            "end": payload.get("end"),
            "webLink": None
        }
    }