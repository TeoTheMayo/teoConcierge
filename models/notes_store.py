import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    with _connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS notebooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notebook_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS note_revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_notes_notebook_id ON notes(notebook_id);
            CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_note_revisions_note_id ON note_revisions(note_id);
            """
        )

        now = _utc_now_iso()
        connection.execute(
            """
            INSERT OR IGNORE INTO notebooks (name, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            ("Default", now, now),
        )
        connection.commit()


def list_notes(db_path):
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            SELECT n.id, n.title, n.updated_at, b.name AS notebook_name
            FROM notes AS n
            JOIN notebooks AS b ON b.id = n.notebook_id
            ORDER BY n.updated_at DESC
            """
        )
        return cursor.fetchall()


def create_note(db_path, title="Untitled Note"):
    now = _utc_now_iso()
    with _connect(db_path) as connection:
        notebook = connection.execute(
            "SELECT id FROM notebooks WHERE name = ?",
            ("Default",),
        ).fetchone()

        if notebook is None:
            connection.execute(
                """
                INSERT INTO notebooks (name, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                ("Default", now, now),
            )
            notebook_id = connection.execute(
                "SELECT id FROM notebooks WHERE name = ?",
                ("Default",),
            ).fetchone()["id"]
        else:
            notebook_id = notebook["id"]

        cursor = connection.execute(
            """
            INSERT INTO notes (notebook_id, title, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (notebook_id, title, "", now, now),
        )
        note_id = cursor.lastrowid
        connection.commit()
        return note_id


def get_note(db_path, note_id):
    with _connect(db_path) as connection:
        return connection.execute(
            """
            SELECT n.id, n.title, n.content, n.updated_at, b.name AS notebook_name
            FROM notes AS n
            JOIN notebooks AS b ON b.id = n.notebook_id
            WHERE n.id = ?
            """,
            (note_id,),
        ).fetchone()


def save_note(db_path, note_id, title, content):
    now = _utc_now_iso()
    with _connect(db_path) as connection:
        connection.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, content, now, note_id),
        )
        connection.execute(
            """
            INSERT INTO note_revisions (note_id, content, created_at)
            VALUES (?, ?, ?)
            """,
            (note_id, content, now),
        )
        connection.commit()
