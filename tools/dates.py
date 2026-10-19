from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

def now_local():
    return datetime.now(TZ)

def local_to_utc(value: str):
    """Converte "AAAA-MM-DDTHH:MM" no horário de Brasília para UTC sem fuso (como fica no banco)."""
    local = datetime.fromisoformat(value)
    if local.tzinfo is None:
        local = local.replace(tzinfo=TZ)
    return local.astimezone(timezone.utc).replace(tzinfo=None)

def utc_to_local(value: datetime):
    return value.replace(tzinfo=timezone.utc).astimezone(TZ)

def format_local(value: datetime):
    return utc_to_local(value).strftime("%d/%m às %H:%M")

def brl(value: float):
    texto = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"
