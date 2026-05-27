import requests

from app.schemas import AgentResult 
from app.config import settings

def validate_exchange_data(
        intent: str,
        data: dict
) -> AgentResult | None: 
    amount = data.get("amount")
    from_currency = data.get("from_currency")
    to_currency = data.get("to_currency")

    if not from_currency:
        return AgentResult(
            response="Informe a moeda de origem. Ex: dólar, euro ou USD",
            intent=intent,
            data=data
        )
    if not to_currency:
        return AgentResult(
            response="Informe a moeda de destino. Ex: real, euro ou BRL",
            intent=intent,
            data=data
        )
    
    if intent == "exchange_conversion" and amount is None:
        return AgentResult(
            response="Informe o valor que deseja converter.",
            intent=intent,
            data=data
        )
    return None

def get_exchange_rate(from_currency: str, to_currency: str) -> dict:
    if not settings.exchange_api_key:
        raise ValueError("Chave de API não configurada")
    
    url = (
        f"{settings.exchange_api_base_url}/"
        f"{settings.exchange_api_key}/pair/"
        f"{from_currency}/{to_currency}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()

def normalize_rate_response(api_result: dict, data: dict) -> dict:

    return{
        "amount": data.get("amount"),
        "from_currency": data.get("from_currency"),
        "to_currency": data.get("to_currency"),
        "conversion_rate": api_result.get("conversion_rate"),
        "conversion_result": None,
        "last_update": api_result.get("time_last_update_utc")
    }

def normalize_conversion_response(api_result: dict, data: dict) -> dict:
    return {
        "amount": data.get("amount"),
        "from_currency": data.get("from_currency"),
        "to_currency": data.get("to_currency"),
        "conversion_rate": api_result.get("conversion_rate"),
        "conversion_result": api_result.get("conversion_result"),
        "last_update": api_result.get("time_last_update_utc")
    }


def convert_currency(
    from_currency: str,
    to_currency: str,
    amount: float
) -> dict: 
    if not settings.exchange_api_key:
        raise ValueError("EXCHANGE_API_KEY não configurada")
    
    url = (
        f"{settings.exchange_api_base_url}/"
        f"{settings.exchange_api_key}/pair/"
        f"{from_currency}/{to_currency}/{amount}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()