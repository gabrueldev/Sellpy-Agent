from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_SQLITE_URL = "sqlite:///./sellpy.db"

def url_accepted_by_sqlalchemy(url):
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

URL_DATABASE = url_accepted_by_sqlalchemy(os.getenv("DATABASE_URL") or LOCAL_SQLITE_URL)

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
