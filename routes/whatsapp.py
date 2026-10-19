import logging
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from sqlalchemy.exc import IntegrityError

import agents.sellpy_agent as agent
from database import models
from database.connect import Sessionlocal
from services import whatsapp
from services.users import get_or_create_user, use_message_quota, LIMIT_MESSAGE

logger = logging.getLogger("sellpy")

router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

@router.get("")
def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    # A Meta chama essa rota uma vez, quando você cadastra o webhook no painel
    if mode == "subscribe" and token and token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Token de verificação inválido")

def handle_message(message_id, phone, text):
    db = Sessionlocal()
    try:
        # Se a Meta reenviar a mesma mensagem, o id repetido quebra a chave primária e paramos aqui
        try:
            db.add(models.ProcessedMessage(id=message_id))
            db.commit()
        except IntegrityError:
            db.rollback()
            return

        user = get_or_create_user(db, f"wa:{phone}")
        if not use_message_quota(db, user):
            whatsapp.send_message(phone, LIMIT_MESSAGE)
            return

        reply = agent.sellpy_agent(db, user, text)
        whatsapp.send_message(phone, reply)
    except Exception:
        logger.exception("Erro ao processar mensagem %s", message_id)
    finally:
        db.close()

@router.post("")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    if not whatsapp.valid_signature(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    # Responde 200 na hora e processa depois; se demorar, a Meta acha que falhou e reenvia
    for message_id, phone, text in whatsapp.extract_text_messages(await request.json()):
        background_tasks.add_task(handle_message, message_id, phone, text)
    return {"status": "ok"}
