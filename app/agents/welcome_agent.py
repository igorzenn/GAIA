from app.schemas import AgentResult

def handle_welcome(message: str, intent: str) -> AgentResult: # o parametro message define que tem que ser uma string, o -> define que a função deve retornar agent result
    return AgentResult(
        response=(
            "Olá! Eu sou a GAIA. Posso te ajudar com agenda, reuniões, "
            "consultas sobre câmbio e moeda e informações sobre a ZEN SA!"
        ),
        intent=intent
    )