from database import models
from .dates import brasilia_iso_to_utc_without_timezone, format_in_brasilia

def add_task(db, user, title, description="", remind_at=None):
    task = models.Tasks(
        user_id=user.id,
        title=title,
        description=description,
        remind_at=brasilia_iso_to_utc_without_timezone(remind_at) if remind_at else None
    )
    db.add(task)
    db.commit()

    message = f"Tarefa #{task.id} '{title}' anotada."
    if task.remind_at:
        message += f" Vou te lembrar em {format_in_brasilia(task.remind_at)}."
    return message

def list_tasks(db, user, status="pendente"):
    query = db.query(models.Tasks).filter(models.Tasks.user_id == user.id)
    if status != "todas":
        query = query.filter(models.Tasks.status == status)
    tasks = query.order_by(models.Tasks.created_at).all()

    if not tasks:
        return "Nenhuma tarefa encontrada."
    linhas = []
    for task in tasks:
        linha = f"#{task.id} [{task.status}] {task.title}"
        if task.remind_at:
            linha += f" (lembrete {format_in_brasilia(task.remind_at)})"
        linhas.append(linha)
    return "\n".join(linhas)

def complete_task(db, user, task_id):
    task = db.query(models.Tasks).filter(
        models.Tasks.id == task_id,
        models.Tasks.user_id == user.id
    ).first()
    if not task:
        return "Erro: tarefa não encontrada."

    task.status = "concluida"
    task.remind_at = None
    db.commit()
    return f"Tarefa '{task.title}' concluída! ✅"

def format_task(task):
    return f"""⏰ Lembrete!

📌 Tarefa: {task.title}
📝 {task.description or 'Sem descrição'}"""
