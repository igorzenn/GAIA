_conversation_state: dict[str, dict] = {}   # arquivo responsavel por criar uma memoria simples em RAm para guardar contexto


def set_pending_action(session_id: str, state: dict) -> None: # salva uma pendencia
    _conversation_state[session_id] = state


def get_pending_action(session_id: str) -> dict | None: # consulta pendencia existente 
    return _conversation_state.get(session_id)


def clear_pending_action(session_id: str) -> None: # remove pendencia depois de concluir/cancelar
    _conversation_state.pop(session_id, None)

def is_confirmation_message(message: str) -> bool: # identificar confirmação
    message_lower = message.lower().strip()

    confirmation_words = [
        "sim",
        "s",
        "yes",
        "confirmo",
        "confirmar",
        "pode cancelar",
        "pode excluir",
        "cancele",
        "excluir",
        "isso",
        "esse",
        "essa"
    ]

    return message_lower in confirmation_words

def is_cancel_message(message: str) -> bool:
    message_lower = message.lower().strip()

    cancel_words = [
        "não",
        "nao",
        "no",
        
        "cancelar",
        "não cancele",
        "nao cancele",
        "deixa",
        "deixa pra lá",
        "deixa pra la"
    ]

    return message_lower in cancel_words