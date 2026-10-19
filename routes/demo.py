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
from services.users import get_or_create_user, try_to_consume_daily_message, LIMIT_MESSAGE
from tools.dates import now_brasilia

router = APIRouter(tags=["demo"])

DEMO_DAILY_LIMIT_ALL_VISITORS = int(os.getenv("SELLPY_DEMO_LIMIT_ALL_VISITORS", "300"))

class DemoMessage(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=500)

@router.get("/", include_in_schema=False)
def demo_page():
    return FileResponse("static/index.html")

def demo_messages_today(db):
    return db.query(func.coalesce(func.sum(models.User.messages_today), 0)).filter(
        models.User.external_id.like(f"{models.DEMO_PREFIX}%"),
        models.User.messages_date == now_brasilia().date()
    ).scalar()

@router.post("/demo/chat")
def demo_chat(data: DemoMessage, db: Session = Depends(get_db)):
    if os.getenv("SELLPY_DEMO_ENABLED", "true") != "true":
        raise HTTPException(status_code=404, detail="Demo desativada")

    if demo_messages_today(db) >= DEMO_DAILY_LIMIT_ALL_VISITORS:
        return {"response": "A demo atingiu o limite de hoje. Volta amanhã! 🙏"}

    user = get_or_create_user(db, f"{models.DEMO_PREFIX}{data.session_id}")
    if not try_to_consume_daily_message(db, user):
        return {"response": LIMIT_MESSAGE}

    return {"response": agent.sellpy_agent(db, user, data.message)}
