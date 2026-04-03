from flask import Flask, redirect, render_template, request, url_for
from datetime import datetime

from config import DB_PATH, DEBUG, PORT, SECRET_KEY
from models.notes_store import create_note, get_note, init_db, list_notes, save_note

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["DEBUG"] = DEBUG


init_db(DB_PATH)


def format_display_datetime(value):
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%m/%d/%Y %H:%M:%S")
    except (TypeError, ValueError):
        return value


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/notes")
def notes():
    rows = list_notes(DB_PATH)
    notes_list = []
    for row in rows:
        notes_list.append(
            {
                "id": row["id"],
                "title": row["title"],
                "updated_at": row["updated_at"],
                "updated_display": format_display_datetime(row["updated_at"]),
                "notebook_name": row["notebook_name"],
            }
        )
    return render_template("notes.html", notes_list=notes_list)


@app.route("/notes/create", methods=["POST"])
def create_note_route():
    note_id = create_note(DB_PATH)
    return redirect(url_for("note_editor", note_id=note_id))


@app.route("/notes/<int:note_id>")
def note_editor(note_id):
    note = get_note(DB_PATH, note_id)
    if note is None:
        return redirect(url_for("notes"))
    notes_list = list_notes(DB_PATH)
    note_updated_display = format_display_datetime(note["updated_at"])
    return render_template(
        "note_editor.html",
        note=note,
        notes_list=notes_list,
        note_updated_display=note_updated_display,
    )


@app.route("/notes/<int:note_id>/save", methods=["POST"])
def save_note_route(note_id):
    title = request.form.get("title", "").strip() or "Untitled Note"
    content = request.form.get("content", "")
    save_note(DB_PATH, note_id, title, content)
    return redirect(url_for("note_editor", note_id=note_id))


@app.route("/calendar")
def calendar():
    return render_template("calendar.html")


@app.route("/tasks")
def tasks():
    return render_template("tasks.html")


if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT)
