from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

def now_brasilia():
    return datetime.now(TZ)

def brasilia_iso_to_utc_without_timezone(value: str):
    local = datetime.fromisoformat(value)
    if local.tzinfo is None:
        local = local.replace(tzinfo=TZ)
    return local.astimezone(timezone.utc).replace(tzinfo=None)

def utc_to_brasilia(value: datetime):
    return value.replace(tzinfo=timezone.utc).astimezone(TZ)

def format_in_brasilia(value: datetime):
    return utc_to_brasilia(value).strftime("%d/%m às %H:%M")

def brl(value: float):
    texto = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"
