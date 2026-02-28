import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

'''Database Schema setup'''

_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id         TEXT    NOT NULL,
    filename           TEXT    NOT NULL,
    processed_at       TEXT    NOT NULL,
    extraction_method  TEXT    NOT NULL,
    elapsed_seconds    REAL    NOT NULL,
    rejected           INTEGER NOT NULL DEFAULT 0,
    rejection_message  TEXT
);

CREATE TABLE IF NOT EXISTS extracted_fields (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER NOT NULL REFERENCES documents(id),
    field_name   TEXT    NOT NULL,
    value        TEXT,
    changed      INTEGER,   -- 1/0 when LLM was given a regex seed; NULL otherwise
    explanation  TEXT
);
"""


def init_db(db_path):
    """Create tables if they don't already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_DDL)


def save_result(db_path, filename: str, request_id: str, extraction_method: str, result: dict) -> int:
    """
    Write: Each document gets its own row and document id to reference between file table and mettadata table
    """
    rejected = result.get("rejected", False)
    processed_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute( #? used for parameter substitution to prevent SQL injection, even though in this context it's not a user-facing input.
            """
            INSERT INTO documents
                (request_id, filename, processed_at, extraction_method,
                 elapsed_seconds, rejected, rejection_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                filename,
                processed_at,
                extraction_method,
                result.get("elapsed_seconds", 0.0),
                1 if rejected else 0,
                result.get("message") if rejected else None,
            ),
        )
        document_id = cur.lastrowid

        if not rejected:
            rows = []
            for field_name, field_data in result.get("metadata", {}).items():
                changed = field_data.get("changed")  # None for non-seeded fields
                rows.append((
                    document_id,
                    field_name,
                    field_data.get("value"),
                    (1 if changed else 0) if changed is not None else None,
                    field_data.get("explanation"),
                ))
            conn.executemany(
                """
                INSERT INTO extracted_fields
                    (document_id, field_name, value, changed, explanation)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )

    return document_id

def get_document_history(db_path, filename: str) -> list[dict]:
    """
    Read: Return all past processing runs for a given filename, with their fields.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        docs = conn.execute(
            "SELECT * FROM documents WHERE filename = ? ORDER BY processed_at DESC",
            (filename,),
        ).fetchall()

        history = []
        for doc in docs:
            fields = conn.execute(
                "SELECT field_name, value, changed, explanation "
                "FROM extracted_fields WHERE document_id = ?",
                (doc["id"],),
            ).fetchall()
            entry = dict(doc)
            entry["fields"] = [dict(f) for f in fields]
            history.append(entry)

    return history


def generate_request_id() -> str:
    """Creates the unique request ID for the audit trail, using UUID4 for randomness."""
    return str(uuid.uuid4())