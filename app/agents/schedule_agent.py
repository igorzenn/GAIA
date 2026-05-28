from app.schemas import AgentResult
from app.services.schedule_parser import parser_schedule_message
from app.services.schedule_service import (validate_schedule_date, build_schedule_datetimes, build_calendar_event_payload, normalize_schedule_create_response)
from app.services.graph_service import create_calendar_event_delegated


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
        
        response = ("Evento criado com sucesso no Microsoft Graph.")
        
    elif intent == "calendar_query":
        response = (
            "Entendi que você quer consultar sua agenda. "
            "Ainda não estou consultando o Microsoft Graph."
        )

    elif intent == "calendar_update":
        response = (
            "Entendi que você quer alterar um compromisso da agenda. "
            "Ainda não estou consultando o Microsoft Graph."
        )

    elif intent == "calendar_delete":
        response = (
            "Entendi que você quer excluir ou cancelar um compromisso. "
            "Ainda não estou consultando o Microsoft Graph."
        )

    else:
        response = (
            "Entendi que sua solicitação é sobre agenda. "
            "Ainda não estou consultando o Microsoft Graph."
        )

    return AgentResult(
        response=response,
        intent=intent,
        data=schedule_data
    )