from datetime import date

from database import models
from .dates import now_brasilia, brl

def goal_progress(goal):
    progress = min(goal.current_amount / goal.amount * 100, 100) if goal.amount else 0
    remaining = max(goal.amount - goal.current_amount, 0)
    return progress, remaining

def active_goals(db, user):
    return db.query(models.EarningsTarget).filter(
        models.EarningsTarget.user_id == user.id,
        models.EarningsTarget.current_amount < models.EarningsTarget.amount
    ).all()

def create_goal(db, user, title, amount, until_date=None):
    if amount <= 0:
        return "Erro: o valor da meta precisa ser maior que zero."

    goal = models.EarningsTarget(
        user_id=user.id,
        title=title,
        amount=amount,
        until_date=date.fromisoformat(until_date) if until_date else None
    )
    db.add(goal)
    db.commit()
    return f"Meta '{title}' de {brl(amount)} criada!"

def add_income_to_goals_and_describe_progress(db, user, value):
    goals = active_goals(db, user)
    message = ""

    for goal in goals:
        goal.current_amount = max(goal.current_amount + value, 0)
        progress, remaining = goal_progress(goal)
        if remaining == 0:
            message += f"\n🎉 Parabéns! Você completou a meta '{goal.title}'!"
        else:
            message += f"\n🎯 Meta '{goal.title}': {progress:.1f}% (faltam {brl(remaining)})"

    db.commit()
    return message

def average_daily_income(db, user, days=7):
    from datetime import timedelta
    from .transactions import period_start
    since = period_start("hoje") - timedelta(days=days - 1)

    total = sum(
        t.value for t in db.query(models.Transaction).filter(
            models.Transaction.user_id == user.id,
            models.Transaction.type == "ganho",
            models.Transaction.created_at >= since
        )
    )
    return total / days

def goals_status(db, user):
    goals = db.query(models.EarningsTarget).filter(models.EarningsTarget.user_id == user.id).all()
    if not goals:
        return "Nenhuma meta criada."

    avg_income = average_daily_income(db, user)
    linhas = []
    for goal in goals:
        progress, remaining = goal_progress(goal)
        linha = f"#{goal.id} {goal.title}: {brl(goal.current_amount)} de {brl(goal.amount)} ({progress:.1f}%)"
        if remaining and avg_income > 0:
            linha += f" - no ritmo atual, faltam cerca de {round(remaining / avg_income)} dias"
        if goal.until_date:
            dias = (goal.until_date - now_brasilia().date()).days
            linha += f" - prazo em {dias} dias" if dias >= 0 else " - prazo vencido"
        linhas.append(linha)
    return "\n".join(linhas)

def delete_goal(db, user, goal_id):
    goal = db.query(models.EarningsTarget).filter(
        models.EarningsTarget.id == goal_id,
        models.EarningsTarget.user_id == user.id
    ).first()
    if not goal:
        return "Erro: meta não encontrada."
    db.delete(goal)
    db.commit()
    return f"Meta '{goal.title}' apagada."
