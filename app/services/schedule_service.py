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

def normalize_schedule_create_response(data: dict) -> dict: # O que gostariamos que viesse na resposta
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

def build_schedule_create_response(data: dict) -> str: # formatação da resposta do schedule para o usuário
    title = data.get("title")
    start_datetime = data.get("start_datetime")
    end_datetime = data.get("end_datetime")
    join_url = data.get("joinUrl")

    datetime_text = format_schedule_datetime_range(
        start_datetime=start_datetime,
        end_datetime=end_datetime
    )

    response = (
        f'Evento "{title}" criado com sucesso '
    )

    if datetime_text:
        response += f"para {datetime_text}"

    response += "."

    if join_url: 
        response += f" Link da reunião: {join_url}"

    return response

def format_schedule_datetime_range(   # formatar hora da resposta
        start_datetime: str | None,
        end_datetime: str | None
) -> str:
    if not start_datetime or not end_datetime:
        return ""
    
    start = datetime.fromisoformat(start_datetime)
    end = datetime.fromisoformat(end_datetime)

    date_text = start.strftime("%d/%m/%Y")
    start_time_text = start.strftime("%H:%M")
    end_time_text = end.strftime("%H:%M")

    return f"{date_text}, das {start_time_text} as {end_time_text}" 

def build_calendar_query_range(data: dict) -> dict: # transforma o pedido do usuário de hoje para o real dia atual 
    date_reference = data.get("date_reference")

    if not date_reference:
        return data

    now = datetime.now(ZoneInfo(settings.timezone))

    if date_reference == "hoje":
        query_date = now.date()

    elif date_reference == "amanha":
        query_date = (now + timedelta(days=1)).date()

    else:
        return data

    start_datetime = datetime.fromisoformat(
        f"{query_date}T00:00:00"
    ).replace(tzinfo=ZoneInfo(settings.timezone))

    end_datetime = datetime.fromisoformat(
        f"{query_date}T23:59:59"
    ).replace(tzinfo=ZoneInfo(settings.timezone))

    return {
        **data,
        "query_start_datetime": start_datetime.isoformat(),
        "query_end_datetime": end_datetime.isoformat()
    }
