from datetime import datetime, timezone


def parse_date(date: str):
    return datetime.fromisoformat(date[:-1]).replace(tzinfo=timezone.utc)
