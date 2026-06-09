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

def normalize_calendar_event_response(graph_result: dict) -> list[dict]:
    events = []

    for event in graph_result.get("value", []):
        online_meeting = graph_result.get("online_meeting") or {}
        organizer = graph_result.get("organizer") or {}
        organizer_email = organizer.get("emailAddress") or {}

    

        events.append({
            "id": event.get("id"),
            "subject": event.get("subject"),
            "start": event.get("start"),
            "end": event.get("end"),
            "location": event.get("location"),
            "webLink": event.get("webLink"),
            "joinUrl": online_meeting.get("joinUrl"),
            "organizer": {
                "name": organizer_email.get("name"),
                "address": organizer_email.get("address")
            },
            "isOnlineMeeting": event.get("isOnlineMeeting")
        })

    return events 


def list_calendar_events_delegated(start_datetime: str, end_datetime: str) -> list[dict]: 
    access_token = get_graph_delegated_access_token()

    url = f"{settings.microsoft_graph_base_url}/me/calendarView"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": f'outlook.timezone="{settings.timezone}"'
    }

    params = {
        "startDateTime": start_datetime,
        "endDateTime": end_datetime,
        "$orderby": "start/dateTime",
        "$top": "50",
        "$select": "id,subject,start,end,location,webLink,isOnlineMeeting,onlineMeeting,organizer"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    return normalize_calendar_event_response(response.json())

def delete_calendar_event_delegated(event_id: str) -> dict:
    if not event_id:
        raise ValueError("ID do evento não informado para cancelamento")

    access_token = get_graph_delegated_access_token()

    url = f"{settings.microsoft_graph_base_url}/me/events/{event_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.delete(
        url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    return {
        "deleted": True,
        "event_id": event_id
    }

def update_calendar_event_delegated(event_id: str, payload: dict) -> dict: # função de update
    if not event_id:
        raise ValueError("ID do evento não informado para alteração")

    access_token = get_graph_delegated_access_token()

    url = f"{settings.microsoft_graph_base_url}/me/events/{event_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": f'outlook.timezone="{settings.timezone}"'
    }

    response = requests.patch(
        url,
        headers=headers,
        json=payload,
        timeout=15
    )

    response.raise_for_status()

    return normalize_calendar_event_response(response.json())