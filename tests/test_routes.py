import hashlib
import hmac
import json
import uuid
from datetime import timedelta

from conftest import text, response
import routes.whatsapp as whatsapp_route
from database import models
from database.models import utcnow
from services import whatsapp
from workers.remind_worker import send_due_reminders

def payload(message_id="wamid.1", phone="5512999999999", body="gastei 10 em café"):
    return {"entry": [{"changes": [{"value": {"messages": [
        {"id": message_id, "from": phone, "type": "text", "text": {"body": body}}
    ]}}]}]}

def assinatura(body):
    return "sha256=" + hmac.new(b"segredo-de-teste", body, hashlib.sha256).hexdigest()

def test_verificacao_do_webhook(client):
    ok = client.get("/webhook/whatsapp", params={
        "hub.mode": "subscribe", "hub.verify_token": "token-de-teste", "hub.challenge": "123"})
    assert ok.status_code == 200 and ok.text == "123"

    errado = client.get("/webhook/whatsapp", params={
        "hub.mode": "subscribe", "hub.verify_token": "outro", "hub.challenge": "123"})
    assert errado.status_code == 403

def test_assinatura_invalida(client):
    body = json.dumps(payload()).encode()
    response_http = client.post("/webhook/whatsapp", content=body,
                                headers={"X-Hub-Signature-256": "sha256=errada", "Content-Type": "application/json"})
    assert response_http.status_code == 401

def test_mensagem_do_whatsapp_e_respondida(client, fake_claude, monkeypatch):
    enviados = []
    monkeypatch.setattr(whatsapp, "send_message", lambda phone, text: enviados.append((phone, text)))
    fake_claude(response(text("Anotado ☕")))

    body = json.dumps(payload()).encode()
    headers = {"X-Hub-Signature-256": assinatura(body), "Content-Type": "application/json"}
    assert client.post("/webhook/whatsapp", content=body, headers=headers).status_code == 200

    assert enviados == [("5512999999999", "Anotado ☕")]

    # A Meta reenviou a mesma mensagem: não responde de novo
    client.post("/webhook/whatsapp", content=body, headers=headers)
    assert len(enviados) == 1

def test_limite_diario(db, monkeypatch, fake_claude):
    enviados = []
    monkeypatch.setattr(whatsapp, "send_message", lambda phone, text: enviados.append(text))
    monkeypatch.setattr("services.users.DAILY_LIMIT", 1)
    fake_claude(response(text("ok")))

    whatsapp_route.handle_message("wamid.a", "5512999999999", "oi")
    whatsapp_route.handle_message("wamid.b", "5512999999999", "oi de novo")

    assert enviados[0] == "ok"
    assert "limite" in enviados[1]

def test_demo(client, fake_claude):
    fake_claude(response(text("Oi! Sou a Sellpy.")))
    session = str(uuid.uuid4())

    assert client.get("/").status_code == 200
    resposta = client.post("/demo/chat", json={"session_id": session, "message": "oi"})
    assert resposta.json() == {"response": "Oi! Sou a Sellpy."}

def test_demo_valida_entrada(client):
    assert client.post("/demo/chat", json={"session_id": "nao-e-uuid", "message": "oi"}).status_code == 422
    assert client.post("/demo/chat", json={"session_id": str(uuid.uuid4()), "message": ""}).status_code == 422

def test_demo_limite_global(client, monkeypatch, fake_claude):
    monkeypatch.setattr("routes.demo.DEMO_GLOBAL_LIMIT", 1)
    fake_claude(response(text("primeira")))

    client.post("/demo/chat", json={"session_id": str(uuid.uuid4()), "message": "oi"})
    segunda = client.post("/demo/chat", json={"session_id": str(uuid.uuid4()), "message": "oi"})
    assert "limite de hoje" in segunda.json()["response"]

def test_lembrete_vencido_e_enviado(db, user, monkeypatch):
    enviados = []
    monkeypatch.setattr(whatsapp, "send_message", lambda phone, text: enviados.append((phone, text)))

    db.add(models.Tasks(user_id=user.id, title="pagar fornecedor", remind_at=utcnow() - timedelta(minutes=1)))
    db.add(models.Tasks(user_id=user.id, title="futuro", remind_at=utcnow() + timedelta(days=1)))
    db.commit()

    assert send_due_reminders() == 1
    assert enviados[0][0] == "5512999999999"
    assert "pagar fornecedor" in enviados[0][1]
    assert send_due_reminders() == 0  # não manda duas vezes
