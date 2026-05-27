import re # biblioteca p o regex

def extract_title(message: str) -> str | None:
    message_lower = message.lower()

    title_patterns = [
        r"t[íi]tulo\s+(.+)",
        r"com o t[íi]tulo\s+(.+)",
        r"chamado\s+(.+)",
        r"chamada\s+(.+)",
    ]

    for pattern in title_patterns:
        match = re.search(pattern, message_lower)

        if match:
            return match.group(1).strip().capitalize()
        
    return None

def extract_hours(message: str) -> tuple[str | None, str | None]:
    message_lower = message.lower()

    pattern = r"(\d{1,2})h?\s*(?:-|às|as|até|ate)\s*(\d{1,2})h?"

    match = re.search(pattern, message_lower)

    if not match:
        return None, None
    
    start_hour = int(match.group(1))
    end_hour = int(match.group(2))

    return f"{start_hour:02d}:00", f"{end_hour:02d}:00"

def extract_date_reference(message: str) -> str | None:
    message_lower = message.lower()

    if "amanhã" in message_lower or "amanha" in message_lower:
        return "amanha"

    if "hoje" in message_lower:
        return "hoje"

    return None


def parser_schedule_message(message: str) -> dict:
    title = extract_title(message)
    start_hour, end_hour = extract_hours(message)
    date_reference = extract_date_reference(message)

    return {
        "title": title,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "date_reference": date_reference
    }