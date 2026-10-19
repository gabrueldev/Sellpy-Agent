from database import models

def create_note(db, user, title, content):
    note = models.Notes(user_id=user.id, title=title, content=content)
    db.add(note)
    db.commit()
    return f"Nota #{note.id} '{title}' criada!"

def list_notes(db, user):
    notes = db.query(models.Notes).filter(models.Notes.user_id == user.id).order_by(models.Notes.created_at).all()
    if not notes:
        return "Nenhuma nota salva."
    return "\n".join(f"#{n.id} {n.title}: {n.content}" for n in notes)

def edit_note(db, user, note_id, title=None, content=None):
    note = db.query(models.Notes).filter(models.Notes.id == note_id, models.Notes.user_id == user.id).first()
    if not note:
        return "Erro: nota não encontrada."

    if title:
        note.title = title
    if content:
        note.content = content
    db.commit()
    return "Nota editada com sucesso!"

def delete_note(db, user, note_id):
    note = db.query(models.Notes).filter(models.Notes.id == note_id, models.Notes.user_id == user.id).first()
    if not note:
        return "Erro: nota não encontrada."

    db.delete(note)
    db.commit()
    return "Nota deletada com sucesso!"
