import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def connect(database_path):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path):
    connection = connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_ref TEXT NOT NULL,
                assessment_type TEXT NOT NULL CHECK (assessment_type IN ('diabetes', 'heart-disease')),
                input_values TEXT NOT NULL,
                predicted_class INTEGER NOT NULL,
                output_category TEXT NOT NULL,
                probability REAL,
                model_version TEXT NOT NULL,
                explanation TEXT,
                guidance TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_assessments_type_category ON assessments(assessment_type, output_category)"
        )
        connection.commit()
    finally:
        connection.close()


@contextmanager
def database_connection(database_path):
    connection = connect(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def serialize_assessment(row):
    item = dict(row)
    item["input_values"] = json.loads(item["input_values"])
    item["explanation"] = json.loads(item["explanation"]) if item["explanation"] else None
    item["guidance"] = json.loads(item["guidance"])
    return item
