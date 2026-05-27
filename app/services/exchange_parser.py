import re 

def normalize_currency(text: str) -> str | None:
    text = text.lower().strip()

    currency_map = {
        "real": "BRL",
        "reais": "BRL",
        "brl": "BRL",
        "r$": "BRL",

        "dolar": "USD",
        "dólar": "USD",
        "dolares": "USD",
        "dólares": "USD",
        "usd": "USD",
        "$": "USD",

        "euro": "EUR",
        "euros": "EUR",
        "eur": "EUR",

        "libra": "GBP",
        "libras": "GBP",
        "gbp": "GBP",
    }

    return currency_map.get(text)

def extract_amount(message: str) -> float | None:
    match = re.search(r"\d+(?:[.,]\d+)?", message)

    if not match:
        return None
    
    value = match.group().replace(",",".")
    return float(value)

def extract_currencies(message: str) -> tuple[str | None, str | None]:
    message_lower = message.lower()

    currency_words = [
        "real", "reais", "brl", "r$",
        "dolar", "dólar", "dolares", "dólares", "usd", "$",
        "euro", "euros", "eur",
        "libra", "libras", "gbp",
    ]

    found = []

    for word in currency_words:
        start_index = message_lower.find(word)

        if start_index != -1:
            currency = normalize_currency(word)

            if currency:
                found.append({
                    "currency": currency,
                    "position": start_index
                })

    found = sorted(found, key=lambda item: item["position"])

    unique_currencies = []

    for item in found:
        if item["currency"] not in unique_currencies:
            unique_currencies.append(item["currency"])

    from_currency = unique_currencies[0] if len(unique_currencies) >= 1 else None
    to_currency = unique_currencies[1] if len(unique_currencies) >= 2 else None

    return from_currency, to_currency

def parse_exchange_message(message: str) -> dict:
    amount = extract_amount(message)
    from_currency, to_currency = extract_currencies(message)

    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency
    }