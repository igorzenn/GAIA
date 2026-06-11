from datetime import datetime, timedelta, time
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
        
        if intent == "calendar_query":
         if not date_reference:
             return AgentResult(
                response="Informe o período da consulta. Exemplo: hoje ou amanhã.",
                intent=intent,
                data=data
        )
         
        if intent == "calendar_delete":
            if not date_reference:
             return AgentResult(
                response="Informe a data do compromisso que deseja cancelar. Exemplo: hoje ou amanhã.",
                intent=intent,
                data=data
        )
            
        if intent == "calendar_update":
            if not date_reference:
                return AgentResult(
                    response="Informe a data do compromisso que deseja alterar. Exemplo: hoje ou amanhã.",
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

def build_calendar_query_response(data: dict) -> str:  # função responsavel por montar a resposta de cancelamento
    events = data.get("events") or []
    events_count = data.get("events_count", 0)

    if events_count == 0:
        return "Não encontrei compromissos nesse período."

    response = f"Encontrei {events_count} compromisso(s) nesse período:"

    for event in events:
        subject = event.get("subject") or "Sem título"

        start = event.get("start") or {}
        end = event.get("end") or {}

        start_datetime = start.get("dateTime")
        end_datetime = end.get("dateTime")

        join_url = event.get("joinUrl")
        web_link = event.get("webLink")

        meeting_link = join_url or web_link

        if start_datetime and end_datetime:
            start_obj = datetime.fromisoformat(start_datetime)
            end_obj = datetime.fromisoformat(end_datetime)

            start_time_text = start_obj.strftime("%H:%M")
            end_time_text = end_obj.strftime("%H:%M")

            response += f"\n- {start_time_text} às {end_time_text} — {subject}"

        else:
            response += f"\n- {subject}"

        if meeting_link:
            response += f" --- [Link da reunião]({meeting_link})"

    return response

def build_calendar_delete_candidate_response(data: dict) -> str:
    events = data.get("events") or []
    events_count = data.get("events_count", 0)

    if events_count == 0:
        return "Não encontrei compromisso compatível para cancelamento nesse período."

    if events_count == 1:
        event = events[0]
        subject = event.get("subject") or "Sem título"

        start = event.get("start") or {}
        end = event.get("end") or {}

        start_datetime = start.get("dateTime")
        end_datetime = end.get("dateTime")

        if start_datetime and end_datetime:
            start_obj = datetime.fromisoformat(start_datetime)
            end_obj = datetime.fromisoformat(end_datetime)

            start_time_text = start_obj.strftime("%H:%M")
            end_time_text = end_obj.strftime("%H:%M")

            return (
                f'Encontrei o compromisso "{subject}" '
                f"das {start_time_text} às {end_time_text}. "
                "Confirma o cancelamento?."
            )

        return (
            f'Encontrei o compromisso "{subject}". '
            "Confirma o cancelamento?"
        )

    response = f"Encontrei {events_count} compromissos compatíveis:"

    for index, event in enumerate(events, start=1):
        subject = event.get("subject") or "Sem título"

        start = event.get("start") or {}
        end = event.get("end") or {}

        start_datetime = start.get("dateTime")
        end_datetime = end.get("dateTime")

        if start_datetime and end_datetime:
            start_obj = datetime.fromisoformat(start_datetime)
            end_obj = datetime.fromisoformat(end_datetime)

            start_time_text = start_obj.strftime("%H:%M")
            end_time_text = end_obj.strftime("%H:%M")

            response += f"\n{index}. {start_time_text} às {end_time_text} — {subject}"
        else:
            response += f"\n{index}. {subject}"

    response += "\n\nInforme qual deseja cancelar."

    return response

def normalize_calendar_delete_candidates(data: dict) -> dict:
    events = data.get("events") or []

    normalized_events = []

    for event in events:
        normalized_events.append({
            "id": event.get("id"),
            "subject": event.get("subject"),
            "start": event.get("start"),
            "end": event.get("end"),
            "webLink": event.get("webLink"),
            "joinUrl": event.get("joinUrl")
        })

    return {
        "title": data.get("title"),
        "date_reference": data.get("date_reference"),
        "query_start_datetime": data.get("query_start_datetime"),
        "query_end_datetime": data.get("query_end_datetime"),
        "events_count": len(normalized_events),
        "events": normalized_events
    }

def build_calendar_update_candidate_response(data: dict) -> str: # Cria resposta para candidato de alteração
    events = data.get("events") or []
    events_count = data.get("events_count", 0)

    if events_count == 0:
        return "Não encontrei compromisso compatível para alteração nesse período."

    if events_count == 1:
        event = events[0]
        subject = event.get("subject") or "Sem título"

        start = event.get("start") or {}
        end = event.get("end") or {}

        start_datetime = start.get("dateTime")
        end_datetime = end.get("dateTime")

        if start_datetime and end_datetime:
            start_obj = datetime.fromisoformat(start_datetime)
            end_obj = datetime.fromisoformat(end_datetime)

            start_time_text = start_obj.strftime("%H:%M")
            end_time_text = end_obj.strftime("%H:%M")

            return (
                f'Encontrei o compromisso "{subject}" '
                f"das {start_time_text} às {end_time_text}. "
                "O que deseja alterar? Você pode informar um novo horário, por exemplo: mudar para 10h às 11h."
            )

        return (
            f'Encontrei o compromisso "{subject}". '
            "O que deseja alterar? Você pode informar um novo horário, por exemplo: mudar para 10h às 11h."
        )

    response = f"Encontrei {events_count} compromissos compatíveis:"

    for index, event in enumerate(events, start=1):
        subject = event.get("subject") or "Sem título"

        start = event.get("start") or {}
        end = event.get("end") or {}

        start_datetime = start.get("dateTime")
        end_datetime = end.get("dateTime")

        if start_datetime and end_datetime:
            start_obj = datetime.fromisoformat(start_datetime)
            end_obj = datetime.fromisoformat(end_datetime)

            start_time_text = start_obj.strftime("%H:%M")
            end_time_text = end_obj.strftime("%H:%M")

            response += f"\n{index}. {start_time_text} às {end_time_text} — {subject}"
        else:
            response += f"\n{index}. {subject}"

    response += "\n\nInforme qual deseja alterar."

    return response

def normalize_calendar_update_candidates(data: dict) -> dict: # Normalização dos candidatos de alteração
    events = data.get("events") or []

    normalized_events = []

    for event in events:
        normalized_events.append({
            "id": event.get("id"),
            "subject": event.get("subject"),
            "start": event.get("start"),
            "end": event.get("end"),
            "webLink": event.get("webLink"),
            "joinUrl": event.get("joinUrl")
        })

    return {
        "title": data.get("title"),
        "date_reference": data.get("date_reference"),
        "query_start_datetime": data.get("query_start_datetime"),
        "query_end_datetime": data.get("query_end_datetime"),
        "events_count": len(normalized_events),
        "events": normalized_events
    }

def build_calendar_update_payload(data: dict) -> dict:
    payload = {}

    new_title = data.get("new_title")
    start_datetime = data.get("new_start_datetime")
    end_datetime = data.get("new_end_datetime")

    if new_title:
        payload["subject"] = new_title

    if start_datetime and end_datetime:
        payload["start"] = {
            "dateTime": start_datetime,
            "timeZone": settings.timezone
        }

        payload["end"] = {
            "dateTime": end_datetime,
            "timeZone": settings.timezone
        }

    if not payload:
        raise ValueError("Nenhuma alteração válida foi informada")

    return payload

def parse_hour_value(hour_value: str) -> tuple[int, int]:
    if not hour_value:
        raise ValueError("Horário não informado")

    hour_text = hour_value.lower().strip()

    if "h" in hour_text:
        parts = hour_text.split("h")

        hour = int(parts[0])

        minute = 0

        if len(parts) > 1 and parts[1]:
            minute = int(parts[1])

        return hour, minute

    if ":" in hour_text:
        hour, minute = hour_text.split(":", 1)

        return int(hour), int(minute)

    return int(hour_text), 0

def build_calendar_update_datetime_data(pending_action: dict, update_changes: dict) -> dict:
    event_start = pending_action.get("event_start") or {}
    event_end = pending_action.get("event_end") or {}

    original_start_datetime = event_start.get("dateTime")
    original_end_datetime = event_end.get("dateTime")

    if not original_start_datetime or not original_end_datetime:
        raise ValueError("Datas originais do evento não encontradas para alteração")

    original_start = datetime.fromisoformat(original_start_datetime)
    original_end = datetime.fromisoformat(original_end_datetime)

    new_date_reference = update_changes.get("new_date_reference")
    new_start_hour = update_changes.get("new_start_hour")
    new_end_hour = update_changes.get("new_end_hour")

    if new_date_reference:
        date_data = {
            "date_reference": new_date_reference,
            "start_hour": new_start_hour or original_start.strftime("%Hh"),
            "end_hour": new_end_hour or original_end.strftime("%Hh")
        }

        datetime_data = build_schedule_datetimes(date_data)

        return {
            "new_start_datetime": datetime_data["start_datetime"],
            "new_end_datetime": datetime_data["end_datetime"]
        }

    start_hour = new_start_hour or original_start.strftime("%Hh")
    end_hour = new_end_hour or original_end.strftime("%Hh")

    start_hour_number, start_minute_number = parse_hour_value(start_hour)
    end_hour_number, end_minute_number = parse_hour_value(end_hour)

    timezone = ZoneInfo(settings.timezone)

    new_start = original_start.replace(
        hour=start_hour_number,
        minute=start_minute_number,
        second=0,
        microsecond=0,
        tzinfo=timezone
    )

    new_end = original_end.replace(
        hour=end_hour_number,
        minute=end_minute_number,
        second=0,
        microsecond=0,
        tzinfo=timezone
    )

    return {
        "new_start_datetime": new_start.isoformat(),
        "new_end_datetime": new_end.isoformat()
    }

