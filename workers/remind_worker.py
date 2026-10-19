import asyncio
import logging

from database import models
from database.connect import Sessionlocal
from database.models import utcnow_without_timezone
from services import whatsapp
from tools.tasks import format_task

logger = logging.getLogger("sellpy")

def deliver_reminder(db, user, task):
    if user.is_whatsapp:
        whatsapp.send_message(user.phone, format_task(task))
    else:
        show_reminder_in_demo_chat(db, user, task)

def show_reminder_in_demo_chat(db, user, task):
    db.add(models.ChatHistoryMessage(user_id=user.id, role="assistant", content=format_task(task)))

def send_due_reminders():
    db = Sessionlocal()
    try:
        tasks = db.query(models.Tasks)\
            .filter(models.Tasks.remind_at <= utcnow_without_timezone())\
            .filter(models.Tasks.status == "pendente")\
            .all()

        for task in tasks:
            deliver_reminder(db, user=db.get(models.User, task.user_id), task=task)
            task.remind_at = None

        db.commit()
        return len(tasks)
    finally:
        db.close()

async def remind_loop(interval=60):
    while True:
        try:
            await asyncio.to_thread(send_due_reminders)
        except Exception:
            logger.exception("Erro no worker de lembretes")
        await asyncio.sleep(interval)
