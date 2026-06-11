from app.schemas import RouterResult


def router_message(message: str) -> RouterResult:
    
    message_lower = message.lower()

    calendar_create_keywords = [
        "marcar",
    "marque",
    "agenda uma",
    "agende",
    "agendar",
    "agende uma reunião",
    "agende uma reuniao",
    "criar reunião",
    "criar reuniao",
    "crie reunião",
    "crie reuniao",
    "criar evento",
    "crie evento",
    "crie o evento",
    "crie",
    "reservar horário",
    "reservar horario",
    "reserve horário",
    "reserve horario",
    "colocar na agenda",
    ]

    calendar_query_keywords = [
        "consultar agenda",
        "ver agenda",
        "minha agenda",
        "compromissos",
        "tenho reunião",
        "tenho reuniao",
        "horários livres",
        "horarios livres",
        "disponibilidade",
    ]

    calendar_update_keywords = [
        "alterar reunião",
        "alterar reuniao",
        "altere",
        "troque",
        "mude",
        "mudar",
        "reagendar",
        "remarcar",
        "mudar horário",
        "mudar horario",
        "editar evento",
    ]

    calendar_delete_keywords = [
        "cancelar",
        "cancele",
        "cancelar reunião",
        "cancelar reuniao",
        "cancele a reunião",
        "cancele a reuniao",
        "cancelar evento",
        "cancele o evento",
        "excluir reunião",
        "excluir reuniao",
        "exclua reunião",
        "exclua reuniao",
        "deletar evento",
        "delete o evento",
        "remover da agenda",
    ]

    exchange_rate_keywords = [
        "cotação",
        "cotacao",
        "taxa",
        "câmbio",
        "cambio",
        "valor do dólar",
        "valor do dolar",
        "valor do euro",
    ]

    exchange_conversion_keywords = [
        "converter",
        "conversão",
        "conversao",
        "quanto dá",
        "quanto da",
        "transformar",
    ]

    exchange_general_keywords = [
        "moeda",
        "dólar",
        "dolar",
        "euro",
        "usd",
        "brl",
        "eur",
        "gbp",
    ]

    if any(keyword in message_lower for keyword in calendar_create_keywords):
        return RouterResult(
            agent="ScheduleAgent",
            intent="calendar_create"
        )

    if any(keyword in message_lower for keyword in calendar_query_keywords):
        return RouterResult(
            agent="ScheduleAgent",
            intent="calendar_query"
        )

    if any(keyword in message_lower for keyword in calendar_update_keywords):
        return RouterResult(
            agent="ScheduleAgent",
            intent="calendar_update"
        )

    if any(keyword in message_lower for keyword in calendar_delete_keywords):
        return RouterResult(
            agent="ScheduleAgent",
            intent="calendar_delete"
        )

    if any(keyword in message_lower for keyword in exchange_conversion_keywords):
        return RouterResult(
            agent="ExchangeAgent",
            intent="exchange_conversion"
        )

    if any(keyword in message_lower for keyword in exchange_rate_keywords):
        return RouterResult(
            agent="ExchangeAgent",
            intent="exchange_rate"
        )

    if any(keyword in message_lower for keyword in exchange_general_keywords):
        return RouterResult(
            agent="ExchangeAgent",
            intent="exchange_request"
        )

    return RouterResult(
        agent="WelcomeAgent",
        intent="welcome"
    )