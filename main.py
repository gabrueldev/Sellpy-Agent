from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from database.connect import engine
from database.models import Base
from routes import whatsapp, demo
from workers.remind_worker import remind_loop

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    worker = None
    if os.getenv("SELLPY_REMINDERS", "true") == "true":
        worker = asyncio.create_task(remind_loop())
    yield
    if worker:
        worker.cancel()

app = FastAPI(title="Sellpy", lifespan=lifespan)

app.include_router(whatsapp.router)
app.include_router(demo.router)

@app.get("/health")
def root():
    return {"Server": "Ok"}
