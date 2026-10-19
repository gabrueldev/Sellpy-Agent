from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

def utcnow():
    # Tudo é salvo em UTC sem fuso; a conversão para o horário de Brasília é feita na hora de mostrar
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Cada número de WhatsApp (ou visitante da demo) é um usuário com seus próprios dados
class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    external_id    = Column(String, unique=True, index=True)  # "wa:5511..." ou "demo:<uuid>"
    created_at     = Column(DateTime, default=utcnow)
    messages_today = Column(Integer, default=0)
    messages_date  = Column(Date, nullable=True)

    @property
    def is_whatsapp(self):
        return self.external_id.startswith("wa:")

    @property
    def phone(self):
        return self.external_id.removeprefix("wa:")

class Transaction(Base):
    __tablename__ = "transactions"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    description = Column(String)
    category    = Column(String)
    type        = Column(String)  # "ganho" ou "gasto"
    value       = Column(Float)
    created_at  = Column(DateTime, default=utcnow)

class Tasks(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title       = Column(String)
    description = Column(String, default="")
    status      = Column(String, default="pendente")  # "pendente" ou "concluida"
    remind_at   = Column(DateTime, nullable=True)
    created_at  = Column(DateTime, default=utcnow)

class Notes(Base):
    __tablename__ = "notes"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title       = Column(String)
    content     = Column(Text)
    created_at  = Column(DateTime, default=utcnow)

class EarningsTarget(Base):
    __tablename__ = "earnings_targets"
    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title          = Column(String)
    amount         = Column(Float)
    current_amount = Column(Float, default=0)
    until_date     = Column(Date, nullable=True)
    created_at     = Column(DateTime, default=utcnow)

# Histórico curto da conversa, para a IA lembrar do contexto
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role       = Column(String)  # "user" ou "assistant"
    content    = Column(Text)
    created_at = Column(DateTime, default=utcnow)

# O WhatsApp reenvia a mesma mensagem se a resposta demorar; isso evita responder duas vezes
class ProcessedMessage(Base):
    __tablename__ = "processed_messages"
    id         = Column(String, primary_key=True)
    created_at = Column(DateTime, default=utcnow)
