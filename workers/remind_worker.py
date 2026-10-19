import asyncio
import logging

from database import models
from database.connect import Sessionlocal
from database.models import utcnow
from services import whatsapp
from tools.tasks import format_task

logger = logging.getLogger("sellpy")

def send_due_reminders():
    db = Sessionlocal()
    try:
        tasks = db.query(models.Tasks)\
            .join(models.User, models.User.id == models.Tasks.user_id)\
            .filter(models.Tasks.remind_at <= utcnow())\
            .filter(models.Tasks.status == "pendente")\
            .all()

        for task in tasks:
            user = db.get(models.User, task.user_id)
            if user.is_whatsapp:
                whatsapp.send_message(user.phone, format_task(task))
            else:
                # Na demo não há para onde mandar; o lembrete aparece na próxima resposta do chat
                db.add(models.ChatMessage(user_id=user.id, role="assistant", content=format_task(task)))
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
