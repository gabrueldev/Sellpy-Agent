from database import models
from services.users import get_or_create_user
from tools import transactions, goals, tasks, notes
from tools.registry import run_tool, TOOLS, HANDLERS

def test_toda_ferramenta_tem_handler():
    assert {t["name"] for t in TOOLS} == set(HANDLERS)

def test_registrar_e_resumir(db, user):
    transactions.add_transaction(db, user, "ganho", 90, "3 bolos", "vendas")
    transactions.add_transaction(db, user, "gasto", 16, "salgado", "Alimentação")
    transactions.add_transaction(db, user, "gasto", 4, "ônibus", "transporte")

    resumo = transactions.get_summary(db, user, "mes")
    assert "Ganhos: R$ 90,00" in resumo
    assert "Gastos: R$ 20,00" in resumo
    assert "Saldo: R$ 70,00" in resumo
    assert "alimentação: R$ 16,00 (80%)" in resumo

def test_valor_invalido(db, user):
    resultado, erro = run_tool(db, user, "registrar_transacao",
                               {"type": "gasto", "value": 0, "description": "x", "category": "y"})
    assert erro

def test_usuarios_nao_veem_dados_um_do_outro(db, user):
    outro = get_or_create_user(db, "wa:5511888888888")
    transactions.add_transaction(db, outro, "gasto", 50, "segredo", "outros")
    notes.create_note(db, outro, "senha do wifi", "1234")

    assert "segredo" not in transactions.list_transactions(db, user)
    assert notes.list_notes(db, user) == "Nenhuma nota salva."

    transacao = db.query(models.Transaction).filter_by(user_id=outro.id).first()
    assert transactions.delete_transaction(db, user, transacao.id).startswith("Erro")

def test_ganho_soma_na_meta(db, user):
    goals.create_goal(db, user, "moto", 1000)
    mensagem = transactions.add_transaction(db, user, "ganho", 250, "venda", "vendas")
    assert "25.0%" in mensagem

    mensagem = transactions.add_transaction(db, user, "ganho", 800, "venda", "vendas")
    assert "completou a meta 'moto'" in mensagem

def test_apagar_ganho_desconta_da_meta(db, user):
    goals.create_goal(db, user, "moto", 1000)
    transactions.add_transaction(db, user, "ganho", 300, "venda", "vendas")
    transacao = db.query(models.Transaction).first()

    transactions.delete_transaction(db, user, transacao.id)
    assert db.query(models.EarningsTarget).first().current_amount == 0

def test_previsao_da_meta(db, user):
    goals.create_goal(db, user, "moto", 1000, "2099-12-31")
    transactions.add_transaction(db, user, "ganho", 140, "venda", "vendas")  # média de 20/dia em 7 dias
    status = goals.goals_status(db, user)
    assert "faltam cerca de 43 dias" in status

def test_tarefa_com_lembrete_no_horario_de_brasilia(db, user):
    mensagem = tasks.add_task(db, user, "pagar fornecedor", "", "2030-01-10T09:00")
    assert "10/01 às 09:00" in mensagem

    tarefa = db.query(models.Tasks).first()
    assert tarefa.remind_at.hour == 12  # 09:00 em Brasília = 12:00 UTC

def test_concluir_tarefa(db, user):
    tasks.add_task(db, user, "ligar para cliente")
    tarefa = db.query(models.Tasks).first()
    tasks.complete_task(db, user, tarefa.id)
    assert tasks.list_tasks(db, user, "pendente") == "Nenhuma tarefa encontrada."
    assert "concluida" in tasks.list_tasks(db, user, "todas")

def test_notas(db, user):
    notes.create_note(db, user, "ideia", "vender brigadeiro gourmet")
    nota = db.query(models.Notes).first()
    notes.edit_note(db, user, nota.id, None, "vender brigadeiro de pistache")
    assert "pistache" in notes.list_notes(db, user)
    notes.delete_note(db, user, nota.id)
    assert notes.list_notes(db, user) == "Nenhuma nota salva."

def test_ferramenta_com_erro_nao_quebra(db, user):
    resultado, erro = run_tool(db, user, "criar_tarefa",
                               {"title": "x", "description": "", "remind_at": "amanhã de manhã"})
    assert erro
    assert "Erro" in resultado
