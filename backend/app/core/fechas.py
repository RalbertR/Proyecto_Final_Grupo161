from datetime import date, datetime, timedelta, timezone

ARGENTINA = timezone(timedelta(hours=-3))


def hoy_en_argentina() -> date:
    return datetime.now(ARGENTINA).date()
