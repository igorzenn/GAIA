from app.schemas import GaiaRequest, GaiaResponse, AgentResult # Traz as classes de schemas
from app.router import router_message
from app.agents.welcome_agent import handle_welcome
from app.agents.schedule_agent import handle_schedule
from app.agents.exchange_agent import handle_exchange
from app.config import settings
from app.utils import build_metadata
from app.logger import logger

from app.services.conversation_state import (
    get_pending_action,
    clear_pending_action,
    is_confirmation_message,
    is_cancel_message,
    set_pending_action
)
from app.services.graph_service import delete_calendar_event_delegated, update_calendar_event_delegated
from app.services.schedule_parser import parser_schedule_message
from app.services.schedule_service import (
    build_schedule_datetimes,
    build_calendar_update_payload
)

from fastapi import FastAPI # Criar endpoints HTTP

app = FastAPI(title=settings.app_name) # Traz para o código a ferramenta que cria o servidor da API e cria a aplicação 

@app.get("/health") # Cria um endpoint do tipo get
def health_check():
    return {
        "status": "ok",
        "service": "python-gaia"
    }

@app.post("/agent", response_model=GaiaResponse) # Cria um endpoint POST chamado /agent 
def process_message(payload: GaiaRequest): # O corpo da requisição precisa seguir o schema Gaia request

    try:  

        pending_action = get_pending_action(payload.sessionId)

        if pending_action:
            if pending_action.get("pending_action") == "confirm_calendar_delete":
                if is_confirmation_message(payload.mensagem_usuario):
                    delete_result = delete_calendar_event_delegated(
                        pending_action["event_id"]
                    )

                    clear_pending_action(payload.sessionId)

                    agent_result = AgentResult(
                        response=(
                            f'Compromisso "{pending_action["event_subject"]}" '
                            "cancelado com sucesso."
                        ),
                        intent="calendar_delete_confirmed",
                        data=delete_result
                    )

                    return GaiaResponse(
                        agent="ScheduleAgent",
                        response=agent_result.response,
                        sessionId=payload.sessionId,
                        status="success",
                        metadata=build_metadata(
                            route="ScheduleAgent",
                            intent=agent_result.intent
                        ) | {
                            "data": agent_result.data
                        }
                    )

                if is_cancel_message(payload.mensagem_usuario):
                    clear_pending_action(payload.sessionId)

                    agent_result = AgentResult(
                        response="Cancelamento interrompido. Nenhum compromisso foi excluído.",
                        intent="calendar_delete_cancelled",
                        data=pending_action
                    )

                    return GaiaResponse(
                        agent="ScheduleAgent",
                        response=agent_result.response,
                        sessionId=payload.sessionId,
                        status="success",
                        metadata=build_metadata(
                            route="ScheduleAgent",
                            intent=agent_result.intent
                        ) | {
                            "data": agent_result.data
                        }
                    )

            if pending_action.get("pending_action") == "calendar_update_waiting_changes":
                update_data = parser_schedule_message(payload.mensagem_usuario)

                start_hour = update_data.get("start_hour")
                end_hour = update_data.get("end_hour")

                if not start_hour or not end_hour:
                    agent_result = AgentResult(
                        response=(
                            "Entendi que você quer alterar esse compromisso, "
                            "mas ainda preciso do novo horário. "
                            "Exemplo: mudar para 10h às 11h."
                        ),
                        intent="calendar_update_waiting_changes",
                        data=pending_action
                    )

                    return GaiaResponse(
                        agent="ScheduleAgent",
                        response=agent_result.response,
                        sessionId=payload.sessionId,
                        status="success",
                        metadata=build_metadata(
                            route="ScheduleAgent",
                            intent=agent_result.intent
                        ) | {
                            "data": agent_result.data
                        }
                    )

                set_pending_action(
                    session_id=payload.sessionId,
                    state={
                        "pending_action": "confirm_calendar_update",
                        "event_id": pending_action.get("event_id"),
                        "event_subject": pending_action.get("event_subject"),
                        "event_start": pending_action.get("event_start"),
                        "event_end": pending_action.get("event_end"),
                        "date_reference": pending_action.get("date_reference"),
                        "new_start_hour": start_hour,
                        "new_end_hour": end_hour
                    }
                )

                agent_result = AgentResult(
                    response=(
                        f'Confirma alterar o compromisso "{pending_action.get("event_subject")}" '
                        f"para {start_hour} às {end_hour}?"
                    ),
                    intent="calendar_update_confirmation_requested",
                    data={
                        "event_id": pending_action.get("event_id"),
                        "event_subject": pending_action.get("event_subject"),
                        "new_start_hour": start_hour,
                        "new_end_hour": end_hour
                    }
                )

                return GaiaResponse(
                    agent="ScheduleAgent",
                    response=agent_result.response,
                    sessionId=payload.sessionId,
                    status="success",
                    metadata=build_metadata(
                        route="ScheduleAgent",
                        intent=agent_result.intent
                    ) | {
                        "data": agent_result.data
                    }
                )
            
            if pending_action.get("pending_action") == "confirm_calendar_update":
                if is_confirmation_message(payload.mensagem_usuario):
                    update_data = {
                        "date_reference": pending_action.get("date_reference"),
                        "start_hour": pending_action.get("new_start_hour"),
                        "end_hour": pending_action.get("new_end_hour")
                    }

                    update_data = build_schedule_datetimes(update_data)
                    update_payload = build_calendar_update_payload({
                        "new_start_datetime": update_data["start_datetime"],
                        "new_end_datetime": update_data["end_datetime"]
                    })

                    graph_result = update_calendar_event_delegated(
                        event_id=pending_action["event_id"],
                        payload=update_payload
                    )

                    clear_pending_action(payload.sessionId)

                    agent_result = AgentResult(
                        response=(
                            f'Compromisso "{pending_action.get("event_subject")}" '
                            f'alterado para o horário das {pending_action.get("new_start_hour")} '
                            f'às {pending_action.get("new_end_hour")} com sucesso.'
                        ),
                        intent="calendar_update_confirmed",
                        data={
                            "updated": True,
                            "event_id": pending_action.get("event_id"),
                            "event_subject": pending_action.get("event_subject"),
                            "new_start_hour": pending_action.get("new_start_hour"),
                            "new_end_hour": pending_action.get("new_end_hour"),
                            "graph_result": graph_result
                        }
                    )

                    return GaiaResponse(
                        agent="ScheduleAgent",
                        response=agent_result.response,
                        sessionId=payload.sessionId,
                        status="success",
                        metadata=build_metadata(
                            route="ScheduleAgent",
                            intent=agent_result.intent
                        ) | {
                            "data": agent_result.data
                        }
                    )

                if is_cancel_message(payload.mensagem_usuario):
                    clear_pending_action(payload.sessionId)

                    agent_result = AgentResult(
                        response="Alteração interrompida. Nenhum compromisso foi modificado.",
                        intent="calendar_update_cancelled",
                        data=pending_action
                    )

                    return GaiaResponse(
                        agent="ScheduleAgent",
                        response=agent_result.response,
                        sessionId=payload.sessionId,
                        status="success",
                        metadata=build_metadata(
                            route="ScheduleAgent",
                            intent=agent_result.intent
                        ) | {
                            "data": agent_result.data
                        }
                    )
                

        logger.info(f"Mensagem recebida | sessionId={payload.sessionId} | message={payload.mensagem_usuario}")
        router_result = router_message(payload.mensagem_usuario)
        agent = router_result.agent

        if agent == "ScheduleAgent":
            agent_result = handle_schedule(message=payload.mensagem_usuario, intent=router_result.intent, session_id=payload.sessionId, access_token=payload.access_token) # payload.mensagem_usuario pega a mensagem enviada pelo usuário e passa para o agente escolhidoe 

        elif agent == "ExchangeAgent":
            agent_result = handle_exchange(message=payload.mensagem_usuario, intent=router_result.intent)

        else:
            agent_result = handle_welcome(message=payload.mensagem_usuario, intent=router_result.intent)

        logger.info(f"Resposta gerada | sessionId={payload.sessionId} | agent={agent} | intent={agent_result.intent}"
        )
        
        return GaiaResponse(
            agent=agent,
            response=agent_result.response,  
            sessionId=payload.sessionId,
            status="success",
            metadata={**build_metadata(route=agent,intent=router_result.intent,),"data": agent_result.data})
   
    except Exception as error:
        
        logger.exception(f"Erro ao processor mensagem | sessioId = {payload.sessionId}")
        return GaiaResponse(
             agent="System",
             response="Deu erro ai na parada",
             sessionId=payload.sessionId,
             status="error",
             metadata=build_metadata(
                 route=None,
                 intent=None,
                 error_type=type(error).__name__
             )
        )