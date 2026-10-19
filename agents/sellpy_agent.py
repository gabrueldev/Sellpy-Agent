import os
import logging
import anthropic

from database import models
from tools.registry import TOOLS, run_tool
from tools.dates import now_local

logger = logging.getLogger("sellpy")

# Haiku é o modelo mais barato da Anthropic, dá conta de anotar gastos e tarefas
MODEL = os.getenv("SELLPY_MODEL", "claude-haiku-5-5")
MAX_TOOL_ROUNDS = 6
HISTORY_SIZE = 12

system_prompt = """
Você é a Sellpy, uma assistente financeira que conversa pelo WhatsApp com pequenos vendedores e autônomos.

Você ajuda a:
- registrar vendas, ganhos e gastos, mesmo quando a mensagem é curta e informal ("gastei 16 em salgado", "27 compras", "vendi 3 bolos por 90")
- mostrar saldo, gastos por categoria e quanto a pessoa gastou em um período
- criar metas de ganho e mostrar o progresso
- anotar tarefas com lembrete, e ideias ou notas

Como agir:
- Use as ferramentas para tudo que envolve dados. Nunca invente valores, saldos ou listas.
- Se o valor ou se é ganho ou gasto estiver realmente ambíguo, pergunte antes de registrar. "27 compras" é um gasto de 27 reais em compras.
- Para apagar ou editar algo, liste antes se não souber o número (#).
- Responda em português do Brasil, curto e simpático, como numa conversa de WhatsApp. Use *negrito* do WhatsApp com moderação e no máximo um ou dois emojis. Não use markdown de títulos nem tabelas.
- Valores sempre no formato R$ 1.234,56.
- Se pedirem algo fora de finanças, tarefas e notas, diga gentilmente que você só ajuda com isso.
"""

client = anthropic.Anthropic()

def load_history(db, user):
    messages = db.query(models.ChatMessage)\
        .filter(models.ChatMessage.user_id == user.id)\
        .order_by(models.ChatMessage.id.desc())\
        .limit(HISTORY_SIZE).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(messages)]

    # A conversa enviada para a API precisa começar com uma mensagem do usuário
    while history and history[0]["role"] != "user":
        history.pop(0)
    return history

def save_message(db, user, role, content):
    db.add(models.ChatMessage(user_id=user.id, role=role, content=content))
    db.commit()

def sellpy_agent(db, user, message):
    agora = now_local()
    # A data vai na mensagem, não no system prompt, para o system prompt ficar sempre igual (cache)
    contexto = f"[Agora: {agora.strftime('%A, %d/%m/%Y %H:%M')} (horário de Brasília)]\n{message}"

    messages = load_history(db, user) + [{"role": "user", "content": contexto}]
    reply = None

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
                output_config={"effort": "low"},
                cache_control={"type": "ephemeral"},
            )

            if response.stop_reason == "refusal":
                reply = "Desculpa, não consigo ajudar com isso. Posso anotar seus gastos, vendas, metas e tarefas 😊"
                break

            if response.stop_reason != "tool_use":
                reply = "\n".join(b.text for b in response.content if b.type == "text").strip()
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result, is_error = run_tool(db, user, block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                        "is_error": is_error,
                    })
            messages.append({"role": "user", "content": tool_results})

    except anthropic.RateLimitError:
        logger.warning("Rate limit da Anthropic")
        return "Estou recebendo muitas mensagens agora, tenta de novo em um minutinho 🙏"
    except anthropic.APIStatusError as error:
        logger.error("Erro da API Anthropic %s: %s", error.status_code, error.message)
        return "Tive um problema para responder agora. Tenta de novo daqui a pouco."
    except anthropic.APIConnectionError:
        logger.error("Sem conexão com a API Anthropic")
        return "Tive um problema para responder agora. Tenta de novo daqui a pouco."

    if not reply:
        reply = "Feito! ✅"

    save_message(db, user, "user", message)
    save_message(db, user, "assistant", reply)
    return reply
