import ambiente_de_teste

import os
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

import agents.sellpy_agent as agent
from database.connect import engine, Sessionlocal
from database.models import Base
from main import app
from services.users import get_or_create_user

@pytest.fixture(autouse=True)
def banco_limpo():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    session = Sessionlocal()
    yield session
    session.close()

@pytest.fixture
def user(db):
    return get_or_create_user(db, "wa:5512999999999")

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def text(value):
    return SimpleNamespace(type="text", text=value)

def tool_use(name, tool_input, id="toolu_1"):
    return SimpleNamespace(type="tool_use", name=name, input=tool_input, id=id)

def response(*blocks, stop_reason=None):
    if stop_reason is None:
        stop_reason = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason)

class FakeAnthropicClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)

@pytest.fixture
def fake_claude(monkeypatch):
    def install(*responses):
        fake = FakeAnthropicClient(*responses)
        monkeypatch.setattr(agent, "client", fake)
        return fake
    return install

def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    if os.path.exists("test_sellpy.db"):
        os.remove("test_sellpy.db")
