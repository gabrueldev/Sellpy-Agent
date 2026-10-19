from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Sem DATABASE_URL o projeto roda com SQLite local, bom para testar sem Docker
URL_DATABASE = os.getenv("DATABASE_URL", "sqlite:///./sellpy.db")

# Render/Neon entregam "postgres://", o SQLAlchemy só aceita "postgresql://"
if URL_DATABASE.startswith("postgres://"):
    URL_DATABASE = URL_DATABASE.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if URL_DATABASE.startswith("sqlite") else {}

engine = create_engine(URL_DATABASE, connect_args=connect_args, pool_pre_ping=True)

Sessionlocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
