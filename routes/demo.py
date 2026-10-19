import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

import agents.sellpy_agent as agent
from database import models
from database.connect import get_db
from services.users import get_or_create_user, use_message_quota, LIMIT_MESSAGE
from tools.dates import now_local

router = APIRouter(tags=["demo"])

# Limite somado de todos os visitantes da demo por dia, para a conta da IA nunca passar disso
DEMO_GLOBAL_LIMIT = int(os.getenv("SELLPY_DEMO_GLOBAL_LIMIT", "300"))

class DemoMessage(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=500)

@router.get("/", include_in_schema=False)
def demo_page():
    return FileResponse("static/index.html")

def demo_messages_today(db):
    return db.query(func.coalesce(func.sum(models.User.messages_today), 0)).filter(
        models.User.external_id.like("demo:%"),
        models.User.messages_date == now_local().date()
    ).scalar()

@router.post("/demo/chat")
def demo_chat(data: DemoMessage, db: Session = Depends(get_db)):
    if os.getenv("SELLPY_DEMO_ENABLED", "true") != "true":
        raise HTTPException(status_code=404, detail="Demo desativada")

    if demo_messages_today(db) >= DEMO_GLOBAL_LIMIT:
        return {"response": "A demo atingiu o limite de hoje. Volta amanhã! 🙏"}

    user = get_or_create_user(db, f"demo:{data.session_id}")
    if not use_message_quota(db, user):
        return {"response": LIMIT_MESSAGE}

    return {"response": agent.sellpy_agent(db, user, data.message)}
