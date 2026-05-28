import requests

from app.config import settings
from app.services.microsoft_auth_service import get_graph_delegated_access_token


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


def create_calendar_event_delegated(payload: dict) -> dict:
    validate_event_payload(payload)

    access_token = get_graph_delegated_access_token()

    url = f"{settings.microsoft_graph_base_url}/me/events"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": f'outlook.timezone="{settings.timezone}"'
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=15
    )

    response.raise_for_status()

    graph_result = response.json()

    return normalize_calendar_event_response(graph_result)

def normalize_calendar_event_response(graph_result: dict) -> dict:
    online_meeting = graph_result.get("online_meeting") or {}
    organizer = graph_result.get("organizer") or {}
    organizer_email = organizer.get("emailAddress") or {}

    attendees = []

    for attendee in graph_result.get("attendees", []):
        email_address = attendee.get("emailAddress") or {}

        attendees.append({
            "name": email_address.get("name"),
            "address": email_address.get("address"),
            "type": attendee.get("type"),
            "status": attendee.get("status")
        })

    return {
        "id":  graph_result.get("id"),
        "subject":  graph_result.get("subject"),
        "joinUrl":  online_meeting.get("joinUrl"),
        "start":  graph_result.get("start"),
        "end":  graph_result.get("end"),
        "organizer": {
            "name": organizer_email.get("name"),
            "address": organizer_email.get("address")
        },
        "attendees": attendees,
        "isOnlineMeeting": graph_result.get("isOnlineMeeting"),
        "onlineMeetingProvider": graph_result.get("onlineMeetingProvider"),
        "createdDateTime": graph_result.get("createdDateTime")
    }