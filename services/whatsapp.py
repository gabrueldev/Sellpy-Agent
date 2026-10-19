import hashlib
import hmac
import logging
import os
import httpx

logger = logging.getLogger("sellpy")

GRAPH_URL = "https://graph.facebook.com/v21.0"

def send_message(phone, text):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_number_id:
        logger.warning("WhatsApp não configurado, mensagem para %s não enviada", phone)
        return False

    response = httpx.post(
        f"{GRAPH_URL}/{phone_number_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": text[:4096]},
        },
        timeout=15,
    )
    if response.status_code >= 400:
        logger.error("Erro ao enviar WhatsApp para %s: %s", phone, response.text)
        return False
    return True

def running_in_development():
    return os.getenv("SELLPY_ENV", "dev") == "dev"

def is_signed_by_meta(body: bytes, signature: str | None):
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    if not app_secret:
        return running_in_development()
    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix("sha256="))

def extract_text_messages(payload):
    found = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                if message.get("type") == "text":
                    found.append((message["id"], message["from"], message["text"]["body"]))
    return found
