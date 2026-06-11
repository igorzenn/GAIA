from app.schemas import GaiaRequest, GaiaResponse, AgentResult
from app.utils import build_metadata

from app.services.conversation_state import (
    get_pending_action,
    clear_pending_action,
    is_confirmation_message,
    is_cancel_message,
    set_pending_action
)

from app.services.graph_service import (
    delete_calendar_event_delegated,
    update_calendar_event_delegated
)

from app.services.schedule_parser import parser_schedule_update_message

from app.services.schedule_service import (
    build_calendar_update_datetime_data,
    build_calendar_update_payload
)


def build_schedule_response(
    response: str,
    session_id: str,
    intent: str,
    data: dict | None = None
) -> GaiaResponse:
    return GaiaResponse(
        agent="ScheduleAgent",
        response=response,
        sessionId=session_id,
        status="success",
        metadata=build_metadata(
            route="ScheduleAgent",
            intent=intent
        ) | {
            "data": data
        }
    )


def handle_pending_action(payload: GaiaRequest) -> GaiaResponse | None:
    pending_action = get_pending_action(payload.sessionId)

    if not pending_action:
        return None

    action_type = pending_action.get("pending_action")

    if action_type == "confirm_calendar_delete":
        return handle_confirm_calendar_delete(
            payload=payload,
            pending_action=pending_action
        )

    if action_type == "calendar_update_waiting_changes":
        return handle_calendar_update_waiting_changes(
            payload=payload,
            pending_action=pending_action
        )

    if action_type == "confirm_calendar_update":
        return handle_confirm_calendar_update(
            payload=payload,
            pending_action=pending_action
        )

    return None


def handle_confirm_calendar_delete(
    payload: GaiaRequest,
    pending_action: dict
) -> GaiaResponse:
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

        return build_schedule_response(
            response=agent_result.response,
            session_id=payload.sessionId,
            intent=agent_result.intent,
            data=agent_result.data
        )

    if is_cancel_message(payload.mensagem_usuario):
        clear_pending_action(payload.sessionId)

        agent_result = AgentResult(
            response="Cancelamento interrompido. Nenhum compromisso foi excluído.",
            intent="calendar_delete_cancelled",
            data=pending_action
        )

        return build_schedule_response(
            response=agent_result.response,
            session_id=payload.sessionId,
            intent=agent_result.intent,
            data=agent_result.data
        )

    agent_result = AgentResult(
        response=(
            "Ainda estou aguardando sua confirmação. "
            "Responda \"sim\" para cancelar o compromisso ou \"não\" para manter."
        ),
        intent="calendar_delete_confirmation_pending",
        data=pending_action
    )

    return build_schedule_response(
        response=agent_result.response,
        session_id=payload.sessionId,
        intent=agent_result.intent,
        data=agent_result.data
    )


def handle_calendar_update_waiting_changes(
    payload: GaiaRequest,
    pending_action: dict
) -> GaiaResponse:
    update_changes = parser_schedule_update_message(payload.mensagem_usuario)

    new_title = update_changes.get("new_title")
    new_date_reference = update_changes.get("new_date_reference")
    new_start_hour = update_changes.get("new_start_hour")
    new_end_hour = update_changes.get("new_end_hour")

    has_time_change = new_start_hour and new_end_hour
    has_date_change = new_date_reference is not None
    has_title_change = new_title is not None

    if not has_time_change and not has_date_change and not has_title_change:
        agent_result = AgentResult(
            response=(
                "Entendi que você quer alterar esse compromisso, "
                "mas ainda preciso saber o que mudar. "
                "Exemplos: mudar para 10h às 11h, mudar para amanhã, "
                "ou mudar o título para Reunião Comercial."
            ),
            intent="calendar_update_waiting_changes",
            data=pending_action
        )

        return build_schedule_response(
            response=agent_result.response,
            session_id=payload.sessionId,
            intent=agent_result.intent,
            data=agent_result.data
        )

    set_pending_action(
        session_id=payload.sessionId,
        state={
            "pending_action": "confirm_calendar_update",
            "event_id": pending_action.get("event_id"),
            "event_subject": pending_action.get("event_subject"),
            "event_start": pending_action.get("event_start"),
            "event_end": pending_action.get("event_end"),
            "new_title": new_title,
            "new_date_reference": new_date_reference,
            "new_start_hour": new_start_hour,
            "new_end_hour": new_end_hour
        }
    )

    change_descriptions = []

    if new_title:
        change_descriptions.append(f'título para "{new_title}"')

    if new_date_reference:
        change_descriptions.append(f"data para {new_date_reference}")

    if new_start_hour and new_end_hour:
        change_descriptions.append(
            f"horário para {new_start_hour} às {new_end_hour}"
        )

    changes_text = ", ".join(change_descriptions)

    agent_result = AgentResult(
        response=(
            f'Confirma alterar o compromisso "{pending_action.get("event_subject")}" '
            f"com a seguinte mudança: {changes_text}?"
        ),
        intent="calendar_update_confirmation_requested",
        data={
            "event_id": pending_action.get("event_id"),
            "event_subject": pending_action.get("event_subject"),
            "new_title": new_title,
            "new_date_reference": new_date_reference,
            "new_start_hour": new_start_hour,
            "new_end_hour": new_end_hour
        }
    )

    return build_schedule_response(
        response=agent_result.response,
        session_id=payload.sessionId,
        intent=agent_result.intent,
        data=agent_result.data
    )


def handle_confirm_calendar_update(
    payload: GaiaRequest,
    pending_action: dict
) -> GaiaResponse:
    if is_confirmation_message(payload.mensagem_usuario):
        update_changes = {
            "new_title": pending_action.get("new_title"),
            "new_date_reference": pending_action.get("new_date_reference"),
            "new_start_hour": pending_action.get("new_start_hour"),
            "new_end_hour": pending_action.get("new_end_hour")
        }

        update_payload_data = {
            "new_title": update_changes.get("new_title")
        }

        if update_changes.get("new_date_reference") or (
            update_changes.get("new_start_hour")
            and update_changes.get("new_end_hour")
        ):
            datetime_data = build_calendar_update_datetime_data(
                pending_action=pending_action,
                update_changes=update_changes
            )

            update_payload_data["new_start_datetime"] = datetime_data[
                "new_start_datetime"
            ]
            update_payload_data["new_end_datetime"] = datetime_data[
                "new_end_datetime"
            ]

        update_payload = build_calendar_update_payload(update_payload_data)

        graph_result = update_calendar_event_delegated(
            event_id=pending_action["event_id"],
            payload=update_payload
        )

        clear_pending_action(payload.sessionId)

        agent_result = AgentResult(
            response=(
                f'Compromisso "{pending_action.get("event_subject")}" '
                "alterado com sucesso."
            ),
            intent="calendar_update_confirmed",
            data={
                "updated": True,
                "event_id": pending_action.get("event_id"),
                "event_subject": pending_action.get("event_subject"),
                "new_title": pending_action.get("new_title"),
                "new_date_reference": pending_action.get("new_date_reference"),
                "new_start_hour": pending_action.get("new_start_hour"),
                "new_end_hour": pending_action.get("new_end_hour"),
                "graph_result": graph_result
            }
        )

        return build_schedule_response(
            response=agent_result.response,
            session_id=payload.sessionId,
            intent=agent_result.intent,
            data=agent_result.data
        )

    if is_cancel_message(payload.mensagem_usuario):
        clear_pending_action(payload.sessionId)

        agent_result = AgentResult(
            response="Alteração interrompida. Nenhum compromisso foi modificado.",
            intent="calendar_update_cancelled",
            data=pending_action
        )

        return build_schedule_response(
            response=agent_result.response,
            session_id=payload.sessionId,
            intent=agent_result.intent,
            data=agent_result.data
        )

    agent_result = AgentResult(
        response=(
            "Ainda estou aguardando sua confirmação. "
            "Responda \"sim\" para alterar o compromisso ou \"não\" para cancelar a alteração."
        ),
        intent="calendar_update_confirmation_pending",
        data=pending_action
    )

    return build_schedule_response(
        response=agent_result.response,
        session_id=payload.sessionId,
        intent=agent_result.intent,
        data=agent_result.data
    )