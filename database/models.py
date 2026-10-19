from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

WHATSAPP_PREFIX = "wa:"
DEMO_PREFIX = "demo:"

TRANSACTION_TYPES = ("ganho", "gasto")
TASK_STATUSES = ("pendente", "concluida")

def utcnow_without_timezone():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    external_id    = Column(String, unique=True, index=True)
    created_at     = Column(DateTime, default=utcnow_without_timezone)
    messages_today = Column(Integer, default=0)
    messages_date  = Column(Date, nullable=True)

    @property
    def is_whatsapp(self):
        return self.external_id.startswith(WHATSAPP_PREFIX)

    @property
    def phone(self):
        return self.external_id.removeprefix(WHATSAPP_PREFIX)

class Transaction(Base):
    __tablename__ = "transactions"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    description = Column(String)
    category    = Column(String)
    type        = Column(String)
    value       = Column(Float)
    created_at  = Column(DateTime, default=utcnow_without_timezone)

class Tasks(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title       = Column(String)
    description = Column(String, default="")
    status      = Column(String, default="pendente")
    remind_at   = Column(DateTime, nullable=True)
    created_at  = Column(DateTime, default=utcnow_without_timezone)

class Notes(Base):
    __tablename__ = "notes"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title       = Column(String)
    content     = Column(Text)
    created_at  = Column(DateTime, default=utcnow_without_timezone)

class EarningsTarget(Base):
    __tablename__ = "earnings_targets"
    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title          = Column(String)
    amount         = Column(Float)
    current_amount = Column(Float, default=0)
    until_date     = Column(Date, nullable=True)
    created_at     = Column(DateTime, default=utcnow_without_timezone)

class ChatHistoryMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role       = Column(String)
    content    = Column(Text)
    created_at = Column(DateTime, default=utcnow_without_timezone)

class AnsweredWhatsAppMessage(Base):
    __tablename__ = "processed_messages"
    id         = Column(String, primary_key=True)
    created_at = Column(DateTime, default=utcnow_without_timezone)
