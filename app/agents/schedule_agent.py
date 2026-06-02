from app.schemas import AgentResult
from app.services.schedule_parser import parser_schedule_message
from app.services.schedule_service import (validate_schedule_date, build_schedule_datetimes, build_calendar_event_payload, normalize_schedule_create_response, 
                                           build_schedule_create_response, build_calendar_query_range, build_calendar_query_response)
from app.services.graph_service import (create_calendar_event_delegated, list_calendar_events_delegated)


def handle_schedule(message: str, intent: str, access_token: str | None = None) -> AgentResult:
    
    schedule_data = parser_schedule_message(message)

    validation_error = validate_schedule_date(
        intent=intent,                      # Valida os dados extraidos 
        data=schedule_data
    )

    if validation_error: 
        return validation_error      # Se faltar algo obrigatorio, pare o fluxo retorne uma resposta pedindo a informação faltante
    
    schedule_data = build_schedule_datetimes(schedule_data)
    if intent == "calendar_create":
        event_payload = build_calendar_event_payload(schedule_data)
        schedule_data["event_payload"] = event_payload

        graph_result = create_calendar_event_delegated(event_payload)
        schedule_data["graph_result"] = graph_result # Adiciona o resultado da criação do evento dentro do dicionario schedule_data

        schedule_data = normalize_schedule_create_response(schedule_data)
        
        response = build_schedule_create_response(schedule_data)
        
    elif intent == "calendar_query":
        schedule_data = build_calendar_query_range(schedule_data)

        events = list_calendar_events_delegated(
            start_datetime=schedule_data["query_start_datetime"],
            end_datetime=schedule_data["query_end_datetime"]
        )

        schedule_data["events"] = events
        schedule_data["events_count"] = len(events)

        response = build_calendar_query_response(schedule_data)

    elif intent == "calendar_update":
        response = (
            "Entendi que você quer alterar um compromisso da agenda. "
            "Ainda não estou consultando o Microsoft Graph."
        )

    elif intent == "calendar_delete":
        
        schedule_data = build_calendar_query_range(schedule_data)

        events = list_calendar_events_delegated(
            start_datetime=schedule_data["query_start_datetime"],
            end_datetime=schedule_data["query_end_datetime"]
        )

        title = schedule_data.get("title")

        if title:
            matching_events = [
                event for event in events
                if title.lower() in (event.get("subject") or "").lower()
            ]
        else:
            matching_events = events

        schedule_data["events"] = matching_events
        schedule_data["events_count"] = len(matching_events)

        if not matching_events:
            response = "Não encontrei compromisso compatível para cancelamento nesse período."

        elif len(matching_events) == 1:
            event = matching_events[0]
            response = (
                f'Encontrei o compromisso "{event.get("subject")}". '
                "Ainda não excluí o evento. A próxima etapa será adicionar confirmação antes de cancelar."
            )

        else:
            response = (
                f"Encontrei {len(matching_events)} compromissos compatíveis. "
                "Preciso que você especifique melhor qual deseja cancelar."
            )

    return AgentResult(
        response=response,
        intent=intent,
        data=schedule_data
    )