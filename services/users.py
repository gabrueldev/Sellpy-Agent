import os

from database import models
from tools.dates import now_brasilia

DAILY_LIMIT = int(os.getenv("SELLPY_DAILY_LIMIT", "40"))
DEMO_DAILY_LIMIT_PER_VISITOR = int(os.getenv("SELLPY_DEMO_LIMIT_PER_VISITOR", "20"))

def get_or_create_user(db, external_id):
    user = db.query(models.User).filter_by(external_id=external_id).first()
    if not user:
        user = models.User(external_id=external_id)
        db.add(user)
        db.commit()
    return user

def try_to_consume_daily_message(db, user):
    hoje = now_brasilia().date()
    if user.messages_date != hoje:
        user.messages_date = hoje
        user.messages_today = 0

    limit = DAILY_LIMIT if user.is_whatsapp else DEMO_DAILY_LIMIT_PER_VISITOR
    if user.messages_today >= limit:
        return False

    user.messages_today += 1
    db.commit()
    return True

LIMIT_MESSAGE = "Você chegou no limite de mensagens de hoje 😅 Amanhã a gente continua!"
