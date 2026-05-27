from app.schemas import AgentResult
from app.services.exchange_parser import parse_exchange_message
from app.services.exchange_service import (validate_exchange_data, get_exchange_rate, convert_currency, normalize_conversion_response, normalize_rate_response)

def handle_exchange(message: str, intent: str) -> AgentResult:
    exchange_data = parse_exchange_message(message)

    validation_error = validate_exchange_data(intent=intent, data=exchange_data)

    if validation_error:
        return validation_error
   
    if intent == "exchange_rate":
        api_result = get_exchange_rate(from_currency=exchange_data["from_currency"], to_currency=exchange_data["to_currency"])

        rate = api_result.get("conversion_rate")

        return AgentResult(
            response=(
                f"A cotação de {exchange_data['from_currency']} para "
                f"{exchange_data['to_currency']} é {rate}."
            ),
            intent=intent,
            data=normalize_rate_response(
                api_result=api_result,
                data=exchange_data
            )
        )
    
    if intent == "exchange_conversion":
        api_result = convert_currency(from_currency=exchange_data["from_currency"],
                                      to_currency=exchange_data["to_currency"],
                                      amount=exchange_data["amount"])
        
        converted_value = api_result.get("conversion_result")

        return AgentResult(
            response=(
                f"{exchange_data['amount']} {exchange_data['from_currency']} "
                f"equivalem a {converted_value} {exchange_data['to_currency']}."
            ),
            intent=intent,
            data=normalize_conversion_response(api_result=api_result, data=exchange_data)
        )
    
    return AgentResult(
        response="Entendi que sua solicitação é sobre câmbio.",
        intent=intent,
        data=exchange_data
    )
        

