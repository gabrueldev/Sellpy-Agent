from database.models import TRANSACTION_TYPES, TASK_STATUSES
from . import transactions, goals, tasks, notes

def schema(properties, required=None):
    return {
        "type": "object",
        "properties": properties,
        "required": required or list(properties),
        "additionalProperties": False,
    }

def nullable(type, description=""):
    return {"anyOf": [{"type": type}, {"type": "null"}], "description": description}

ID = {"type": "integer", "description": "Número que aparece com # nas listagens"}
DATETIME = {"type": "string", "description": "Data e hora no horário de Brasília, formato AAAA-MM-DDTHH:MM"}

TOOLS = [
    {
        "name": "registrar_transacao",
        "description": "Registra um ganho (venda, pagamento recebido) ou um gasto. Use sempre que o usuário mencionar dinheiro que entrou ou saiu, mesmo informalmente, como 'gastei 16 em salgado' ou '27 compras'.",
        "input_schema": schema({
            "type": {"type": "string", "enum": list(TRANSACTION_TYPES)},
            "value": {"type": "number", "description": "Valor em reais"},
            "description": {"type": "string", "description": "O que foi, ex: 'salgado'"},
            "category": {"type": "string", "description": "Categoria curta em minúsculas, ex: alimentação, transporte, vendas, compras, contas, lazer"},
        }),
    },
    {
        "name": "resumo_financeiro",
        "description": "Mostra ganhos, gastos, saldo e porcentagem de gastos por categoria em um período.",
        "input_schema": schema({"period": {"type": "string", "enum": ["hoje", "semana", "mes", "tudo"]}}),
    },
    {
        "name": "listar_transacoes",
        "description": "Lista as últimas movimentações com seus números (#), para consultar ou apagar alguma.",
        "input_schema": schema({"limit": {"type": "integer", "description": "Quantas mostrar, até 30"}}),
    },
    {
        "name": "apagar_transacao",
        "description": "Apaga uma movimentação registrada errada. Liste antes para saber o número.",
        "input_schema": schema({"transaction_id": ID}),
    },
    {
        "name": "criar_meta",
        "description": "Cria uma meta de ganhos. Os ganhos registrados depois disso somam automaticamente na meta.",
        "input_schema": schema({
            "title": {"type": "string"},
            "amount": {"type": "number", "description": "Valor da meta em reais"},
            "until_date": nullable("string", "Prazo AAAA-MM-DD, ou null se não houver"),
        }),
    },
    {
        "name": "ver_metas",
        "description": "Mostra o progresso das metas e a previsão de quando cada uma será alcançada no ritmo atual.",
        "input_schema": schema({}),
    },
    {
        "name": "apagar_meta",
        "description": "Apaga uma meta.",
        "input_schema": schema({"goal_id": ID}),
    },
    {
        "name": "criar_tarefa",
        "description": "Anota uma tarefa. Se o usuário pedir para ser lembrado, preencha remind_at.",
        "input_schema": schema({
            "title": {"type": "string"},
            "description": {"type": "string"},
            "remind_at": nullable("string", DATETIME["description"] + ", ou null sem lembrete"),
        }),
    },
    {
        "name": "listar_tarefas",
        "description": "Lista as tarefas do usuário.",
        "input_schema": schema({"status": {"type": "string", "enum": [*TASK_STATUSES, "todas"]}}),
    },
    {
        "name": "concluir_tarefa",
        "description": "Marca uma tarefa como concluída.",
        "input_schema": schema({"task_id": ID}),
    },
    {
        "name": "criar_nota",
        "description": "Salva uma ideia ou anotação livre.",
        "input_schema": schema({"title": {"type": "string"}, "content": {"type": "string"}}),
    },
    {
        "name": "listar_notas",
        "description": "Lista as notas salvas.",
        "input_schema": schema({}),
    },
    {
        "name": "editar_nota",
        "description": "Edita o título e/ou o conteúdo de uma nota. Mande null no campo que não muda.",
        "input_schema": schema({
            "note_id": ID,
            "title": nullable("string"),
            "content": nullable("string"),
        }),
    },
    {
        "name": "apagar_nota",
        "description": "Apaga uma nota.",
        "input_schema": schema({"note_id": ID}),
    },
]

for tool in TOOLS:
    tool["strict"] = True

HANDLERS = {
    "registrar_transacao": transactions.add_transaction,
    "resumo_financeiro": transactions.get_summary,
    "listar_transacoes": transactions.list_transactions,
    "apagar_transacao": transactions.delete_transaction,
    "criar_meta": goals.create_goal,
    "ver_metas": goals.goals_status,
    "apagar_meta": goals.delete_goal,
    "criar_tarefa": tasks.add_task,
    "listar_tarefas": tasks.list_tasks,
    "concluir_tarefa": tasks.complete_task,
    "criar_nota": notes.create_note,
    "listar_notas": notes.list_notes,
    "editar_nota": notes.edit_note,
    "apagar_nota": notes.delete_note,
}

def run_tool(db, user, name, tool_input):
    handler = HANDLERS.get(name)
    if not handler:
        return f"Ferramenta desconhecida: {name}", True
    try:
        result = handler(db, user, **tool_input)
    except Exception as error:
        db.rollback()
        return f"Erro ao executar {name}: {error}", True
    return result, result.startswith("Erro")
