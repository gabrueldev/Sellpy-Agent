import hashlib
import hmac
import logging
import os
import httpx

logger = logging.getLogger("sellpy")

GRAPH_URL = "https://graph.facebook.com/v21.0"

def send_message(phone, text):
    """Envia uma mensagem de texto pela WhatsApp Cloud API da Meta."""
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

def valid_signature(body: bytes, signature: str | None):
    """Confere se a requisição veio mesmo da Meta (header X-Hub-Signature-256)."""
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    if not app_secret:
        # Sem o segredo configurado não dá para validar; só aceitável em desenvolvimento
        return os.getenv("SELLPY_ENV", "dev") == "dev"
    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix("sha256="))

def extract_text_messages(payload):
    """Tira do webhook da Meta só as mensagens de texto: [(id, telefone, texto)]."""
    found = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                if message.get("type") == "text":
                    found.append((message["id"], message["from"], message["text"]["body"]))
    return found
