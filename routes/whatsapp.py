import logging
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from sqlalchemy.exc import IntegrityError

import agents.sellpy_agent as agent
from database import models
from database.connect import Sessionlocal
from services import whatsapp
from services.users import get_or_create_user, try_to_consume_daily_message, LIMIT_MESSAGE

logger = logging.getLogger("sellpy")

router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])

@router.get("")
def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    if mode == "subscribe" and token and token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Token de verificação inválido")

def is_first_delivery(db, message_id):
    try:
        db.add(models.AnsweredWhatsAppMessage(id=message_id))
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False

def handle_message(message_id, phone, text):
    db = Sessionlocal()
    try:
        if not is_first_delivery(db, message_id):
            return

        user = get_or_create_user(db, f"{models.WHATSAPP_PREFIX}{phone}")
        if not try_to_consume_daily_message(db, user):
            whatsapp.send_message(phone, LIMIT_MESSAGE)
            return

        reply = agent.sellpy_agent(db, user, text)
        whatsapp.send_message(phone, reply)
    except Exception:
        logger.exception("Erro ao processar mensagem %s", message_id)
    finally:
        db.close()

@router.post("")
async def receive_webhook_and_answer_in_background(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    if not whatsapp.is_signed_by_meta(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    for message_id, phone, text in whatsapp.extract_text_messages(await request.json()):
        background_tasks.add_task(handle_message, message_id, phone, text)
    return {"status": "ok"}
