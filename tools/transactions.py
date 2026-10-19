from datetime import timedelta
from sqlalchemy import func

from database import models
from .dates import now_brasilia, brasilia_iso_to_utc_without_timezone, brl
from .goals import add_income_to_goals_and_describe_progress

def add_transaction(db, user, type, value, description, category):
    if value <= 0:
        return "Erro: o valor precisa ser maior que zero."

    transaction = models.Transaction(
        user_id=user.id,
        type=type,
        value=round(value, 2),
        description=description,
        category=category.lower()
    )
    db.add(transaction)
    db.commit()

    message = f"{'Ganho' if type == 'ganho' else 'Gasto'} de {brl(value)} registrado em {category}."
    if type == "ganho":
        message += add_income_to_goals_and_describe_progress(db, user, value)
    return message

def period_start(period):
    hoje = now_brasilia().replace(hour=0, minute=0, second=0, microsecond=0)
    starts = {
        "hoje": hoje,
        "semana": hoje - timedelta(days=hoje.weekday()),
        "mes": hoje.replace(day=1),
    }
    start = starts.get(period)
    return brasilia_iso_to_utc_without_timezone(start.isoformat()) if start else None

def get_summary(db, user, period="mes"):
    query = db.query(models.Transaction).filter(models.Transaction.user_id == user.id)
    start = period_start(period)
    if start:
        query = query.filter(models.Transaction.created_at >= start)
    transactions = query.all()

    ganhos = sum(t.value for t in transactions if t.type == "ganho")
    gastos = sum(t.value for t in transactions if t.type == "gasto")

    por_categoria = {}
    for t in transactions:
        if t.type == "gasto":
            por_categoria[t.category] = por_categoria.get(t.category, 0) + t.value

    linhas = [
        f"Período: {period}",
        f"Ganhos: {brl(ganhos)}",
        f"Gastos: {brl(gastos)}",
        f"Saldo: {brl(ganhos - gastos)}",
    ]
    if gastos:
        linhas.append("Gastos por categoria:")
        for categoria, valor in sorted(por_categoria.items(), key=lambda item: -item[1]):
            linhas.append(f"- {categoria}: {brl(valor)} ({valor / gastos * 100:.0f}%)")
    if not transactions:
        linhas.append("Nenhuma movimentação nesse período.")
    return "\n".join(linhas)

def list_transactions(db, user, limit=10):
    transactions = db.query(models.Transaction)\
        .filter(models.Transaction.user_id == user.id)\
        .order_by(models.Transaction.created_at.desc())\
        .limit(min(limit, 30)).all()

    if not transactions:
        return "Nenhuma movimentação registrada."
    return "\n".join(
        f"#{t.id} {t.type} {brl(t.value)} - {t.description} ({t.category})" for t in transactions
    )

def delete_transaction(db, user, transaction_id):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == user.id
    ).first()
    if not transaction:
        return "Erro: movimentação não encontrada."

    if transaction.type == "ganho":
        add_income_to_goals_and_describe_progress(db, user, -transaction.value)
    db.delete(transaction)
    db.commit()
    return f"Movimentação #{transaction_id} apagada."
