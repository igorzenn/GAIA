from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.schemas import AgentResult

def validate_schedule_date(
    intent: str,
    data: dict
) -> AgentResult | None:
    title = data.get("title")
    start_hour = data.get("start_hour")
    end_hour = data.get("end_hour")
    date_reference = data.get("date_reference")


    if intent == "calendar_create":
        if not title:
            return AgentResult(
                response="Informe o título do compromisso.",
                intent=intent,
                data=data
            )

        if not date_reference:
            return AgentResult(
                response="Informe a data do compromisso. Exemplo: hoje ou amanhã.",
                intent=intent,
                data=data
            )

        if not start_hour:
            return AgentResult(
                response="Informe o horário inicial do compromisso.",
                intent=intent,
                data=data
            )

        if not end_hour:
            return AgentResult(
                response="Informe o horário final do compromisso.",
                intent=intent,
                data=data
            )

    return None

def build_schedule_datetimes(data: dict) -> dict:
    date_reference = data.get("date_reference")
    start_hour = data.get("start_hour")
    end_hour = data.get("end_hour")

    if not date_reference or not start_hour or not end_hour: # Proteção caso falte alguma data, não tenta montar data completa
        return data
    
    now = datetime.now(ZoneInfo(settings.timezone)) # Pega data e hora atual considerando o q foi configurado com timezone do .env

    if date_reference == "hoje":
        event_date = now.date()

    elif date_reference =="amanha":
        event_date = (now + timedelta(days=1)).date()

    else: 
        return data

    start_datetime = datetime.fromisoformat(f"{event_date}T{start_hour}:00").replace(tzinfo=ZoneInfo(settings.timezone))
    end_datetime = datetime.fromisoformat(f"{event_date}T{end_hour}:00").replace(tzinfo=ZoneInfo(settings.timezone))  # converte data incial e final para o formato iso adicionando timezone e etc

    return {
        **data,
        "start_datetime": start_datetime.isoformat(),
        "end_datetime": end_datetime.isoformat() 
    }

def build_calendar_event_payload(data: dict) -> dict: # formatação que o microsoft graph espera receber'
    return {
        "subject": data.get("title"),
        "start": {
            "dateTime": data.get("start_datetime"),
            "timeZone": settings.timezone
        },
        "end": {
            "dateTime": data.get("end_datetime"),
            "timeZone": settings.timezone
        },
        "body": {
            "contentType": "HTML",
            "content": ""
        },
        "location": {
            "displayName": ""
        },
        "attendees": [],
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }

def normalize_schedule_create_response(data: dict) -> dict:
    graph_result = data.get("graph_result") or {}

    return {
        "title": data.get("title"),
        "start_datetime": data.get("start_datetime"),
        "end_datetime": data.get("end_datetime"),
        "event_id": graph_result.get("id"),
        "webLink": graph_result.get("webLink"),
        "joinUrl": graph_result.get("joinUrl"),
        "organizer": graph_result.get("organizer"),
        "attendees": graph_result.get("attendees"),
        "isOnlineMeeting": graph_result.get("isOnlineMeeting"),
        "onlineMeetingProvider": graph_result.get("onlineMeetingProvider")
    }