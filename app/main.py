from app.schemas import GaiaRequest, GaiaResponse
from app.router import router_message
from app.agents.welcome_agent import handle_welcome
from app.agents.schedule_agent import handle_schedule
from app.agents.exchange_agent import handle_exchange
from app.config import settings
from app.utils import build_metadata
from app.logger import logger
from app.services.pending_action_handler import handle_pending_action
from fastapi import FastAPI

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "python-gaia"
    }


@app.post("/agent", response_model=GaiaResponse)
def process_message(payload: GaiaRequest):

    try:
        pending_response = handle_pending_action(payload)

        if pending_response:
            return pending_response

        logger.info(
            f"Mensagem recebida | sessionId={payload.sessionId} | "
            f"message={payload.mensagem_usuario}"
        )

        router_result = router_message(payload.mensagem_usuario)
        agent = router_result.agent

        if agent == "ScheduleAgent":
            agent_result = handle_schedule(
                message=payload.mensagem_usuario,
                intent=router_result.intent,
                session_id=payload.sessionId,
                access_token=payload.access_token
            )

        elif agent == "ExchangeAgent":
            agent_result = handle_exchange(
                message=payload.mensagem_usuario,
                intent=router_result.intent
            )

        else:
            agent_result = handle_welcome(
                message=payload.mensagem_usuario,
                intent=router_result.intent
            )

        logger.info(
            f"Resposta gerada | sessionId={payload.sessionId} | "
            f"agent={agent} | intent={agent_result.intent}"
        )

        return GaiaResponse(
            agent=agent,
            response=agent_result.response,
            sessionId=payload.sessionId,
            status="success",
            metadata={
                **build_metadata(
                    route=agent,
                    intent=router_result.intent
                ),
                "data": agent_result.data
            }
        )

    except Exception as error:
        logger.exception(
            f"Erro ao processar mensagem | sessionId={payload.sessionId}"
        )

        return GaiaResponse(
            agent="System",
            response="Deu erro ao processar sua solicitação.",
            sessionId=payload.sessionId,
            status="error",
            metadata=build_metadata(
                route=None,
                intent=None,
                error_type=type(error).__name__
            )
        )