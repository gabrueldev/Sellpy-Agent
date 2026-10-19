from conftest import text, tool_use, response

import agents.sellpy_agent as agent
from database import models

def test_agente_registra_gasto_com_ferramenta(db, user, fake_claude):
    fake = fake_claude(
        response(tool_use("registrar_transacao",
                          {"type": "gasto", "value": 16, "description": "salgado", "category": "alimentação"})),
        response(text("Anotado! Gasto de *R$ 16,00* em alimentação 🥟")),
    )

    reply = agent.sellpy_agent(db, user, "gastei 16 em salgado")

    assert reply == "Anotado! Gasto de *R$ 16,00* em alimentação 🥟"
    assert db.query(models.Transaction).first().value == 16

    # Segunda chamada leva o resultado da ferramenta de volta para a IA
    resultado = fake.calls[1]["messages"][-1]["content"][0]
    assert resultado["type"] == "tool_result"
    assert "R$ 16,00" in resultado["content"]
    assert resultado["is_error"] is False

def test_usa_modelo_barato_e_esforco_baixo(db, user, fake_claude):
    fake = fake_claude(response(text("Oi!")))
    agent.sellpy_agent(db, user, "oi")

    chamada = fake.calls[0]
    assert chamada["model"] == "claude-haiku-5-5"
    assert chamada["output_config"] == {"effort": "low"}
    assert all(tool["strict"] for tool in chamada["tools"])
    assert "Agora:" in chamada["messages"][-1]["content"]

def test_historico_entra_na_proxima_conversa(db, user, fake_claude):
    fake_claude(response(text("Prazer, Ana!")))
    agent.sellpy_agent(db, user, "meu nome é Ana")

    fake = fake_claude(response(text("Seu nome é Ana.")))
    agent.sellpy_agent(db, user, "qual meu nome?")

    mensagens = fake.calls[0]["messages"]
    assert mensagens[0] == {"role": "user", "content": "meu nome é Ana"}
    assert mensagens[1] == {"role": "assistant", "content": "Prazer, Ana!"}

def test_recusa(db, user, fake_claude):
    fake_claude(response(text(""), stop_reason="refusal"))
    assert "não consigo ajudar" in agent.sellpy_agent(db, user, "...")

def test_para_depois_de_muitas_rodadas(db, user, fake_claude):
    fake = fake_claude(*[response(tool_use("listar_notas", {})) for _ in range(agent.MAX_TOOL_ROUNDS)])
    reply = agent.sellpy_agent(db, user, "lista minhas notas")
    assert reply == "Feito! ✅"
    assert len(fake.calls) == agent.MAX_TOOL_ROUNDS

def test_sem_chave_explica_o_que_falta(db, user, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert "ANTHROPIC_API_KEY" in agent.sellpy_agent(db, user, "oi")
