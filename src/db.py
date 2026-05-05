"""
Zentrale Datenbankschicht für SchoolMood.
Enthält alle Funktionen für Klassen, Sessions und Stimmen.
Die alte session_logs-Tabelle wird für Rückwärtskompatibilität beibehalten.
"""

import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------------------------
# Verbindung & Initialisierung
# ---------------------------------------------------------------------------


def get_db_file() -> str:
    """Gibt den Dateinamen der Datenbank für die aktuell eingeloggte Schule zurück."""
    school_id = st.session_state.get("school_id", "default_school")
    return f"stimmung_{school_id}.db"


def init_db():
    """Initialisiert alle Tabellen (alt + neu) in der Schul-Datenbank."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()

    # ── Alt: Session-Logs (Rückwärtskompatibilität) ──────────────────────────
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            phase TEXT,
            gut_count INTEGER DEFAULT 0,
            mittel_count INTEGER DEFAULT 0,
            schlecht_count INTEGER DEFAULT 0
        )
    """
    )

    # ── Neu: Klassen ──────────────────────────────────────────────────────────
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # ── Neu: Sessions (eine Abstimmungsrunde pro Klasse) ─────────────────────
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id TEXT NOT NULL,
            class_id INTEGER REFERENCES classes(id),
            phase TEXT NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            is_discarded INTEGER DEFAULT 0
        )
    """
    )

    # ── Neu: Einzelstimmen (sofort persistiert) ───────────────────────────────
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES sessions(id),
            vote TEXT NOT NULL,
            voted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Klassen-Operationen
# ---------------------------------------------------------------------------


def create_class(name: str) -> int:
    """Legt eine neue Klasse an und gibt die ID zurück."""
    school_id = st.session_state.get("school_id", "default_school")
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "INSERT INTO classes (school_id, name) VALUES (?, ?)",
        (school_id, name.strip()),
    )
    class_id = c.lastrowid
    conn.commit()
    conn.close()
    return class_id


def get_classes() -> list[dict]:
    """Gibt alle Klassen der aktuellen Schule zurück."""
    school_id = st.session_state.get("school_id", "default_school")
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "SELECT id, name, created_at FROM classes WHERE school_id=? ORDER BY name",
        (school_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "created_at": r[2]} for r in rows]


def delete_class(class_id: int):
    """Löscht eine Klasse (nur wenn keine aktiven Sessions existieren)."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute("DELETE FROM classes WHERE id=?", (class_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Session-Operationen
# ---------------------------------------------------------------------------


def open_session(class_id: int, phase: str) -> int:
    """Öffnet eine neue Abstimmungs-Session und gibt die Session-ID zurück."""
    school_id = st.session_state.get("school_id", "default_school")
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (school_id, class_id, phase, started_at) VALUES (?, ?, ?, ?)",
        (school_id, class_id, phase, datetime.now()),
    )
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def close_session(session_id: int):
    """Schließt eine Session (Daten werden behalten)."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "UPDATE sessions SET ended_at=? WHERE id=?",
        (datetime.now(), session_id),
    )
    conn.commit()
    conn.close()


def discard_session(session_id: int):
    """Verwirft eine Session: löscht alle Stimmen und markiert sie als verworfen."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute("DELETE FROM votes WHERE session_id=?", (session_id,))
    c.execute(
        "UPDATE sessions SET ended_at=?, is_discarded=1 WHERE id=?",
        (datetime.now(), session_id),
    )
    conn.commit()
    conn.close()


def get_active_sessions() -> list[dict]:
    """Gibt alle aktuell offenen Sessions der Schule zurück (für Live-Ansicht)."""
    school_id = st.session_state.get("school_id", "default_school")
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        """
        SELECT s.id, s.phase, s.started_at, cl.name AS class_name,
               SUM(CASE WHEN v.vote='Gut' THEN 1 ELSE 0 END) AS gut_count,
               SUM(CASE WHEN v.vote='Mittel' THEN 1 ELSE 0 END) AS mittel_count,
               SUM(CASE WHEN v.vote='Schlecht' THEN 1 ELSE 0 END) AS schlecht_count,
               COUNT(v.id) AS total_votes
        FROM sessions s
        LEFT JOIN classes cl ON s.class_id = cl.id
        LEFT JOIN votes v ON v.session_id = s.id
        WHERE s.school_id=? AND s.ended_at IS NULL AND s.is_discarded=0
        GROUP BY s.id
        ORDER BY s.started_at DESC
        """,
        (school_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "phase": r[1],
            "started_at": r[2],
            "class_name": r[3] or "Unbekannte Klasse",
            "gut_count": r[4] or 0,
            "mittel_count": r[5] or 0,
            "schlecht_count": r[6] or 0,
            "total_votes": r[7] or 0,
        }
        for r in rows
    ]


def get_session_vote_counts(session_id: int) -> dict:
    """Gibt die aktuellen Stimm-Zählungen einer Session zurück (aus der DB)."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "SELECT vote, COUNT(*) FROM votes WHERE session_id=? GROUP BY vote",
        (session_id,),
    )
    rows = c.fetchall()
    conn.close()
    counts = {"Gut": 0, "Mittel": 0, "Schlecht": 0}
    for vote, count in rows:
        if vote in counts:
            counts[vote] = count
    return counts


def get_session_info(session_id: int) -> dict | None:
    """Gibt Informationen zu einer Session zurück."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        """
        SELECT s.id, s.phase, s.started_at, cl.name as class_name
        FROM sessions s
        LEFT JOIN classes cl ON s.class_id = cl.id
        WHERE s.id=?
        """,
        (session_id,),
    )
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "phase": row[1], "started_at": row[2], "class_name": row[3]}
    return None


# ---------------------------------------------------------------------------
# Stimmen-Operationen
# ---------------------------------------------------------------------------


def cast_vote(session_id: int, vote: str):
    """Speichert eine einzelne Stimme sofort in der Datenbank."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "INSERT INTO votes (session_id, vote, voted_at) VALUES (?, ?, ?)",
        (session_id, vote, datetime.now()),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Dashboard-Daten
# ---------------------------------------------------------------------------


def get_new_votes_df() -> pd.DataFrame:
    """Gibt alle Einzelstimmen (neues System) mit Session- und Klasseninfo zurück."""
    conn = sqlite3.connect(get_db_file())
    try:
        df = pd.read_sql_query(
            """
            SELECT v.id, v.vote, v.voted_at,
                   s.phase, s.started_at AS session_start,
                   cl.name AS class_name, cl.id AS class_id,
                   s.id AS session_id
            FROM votes v
            JOIN sessions s ON v.session_id = s.id
            JOIN classes cl ON s.class_id = cl.id
            WHERE s.is_discarded = 0
            ORDER BY v.voted_at DESC
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if not df.empty:
        df["voted_at"] = pd.to_datetime(df["voted_at"])
        df["date"] = df["voted_at"].dt.date
        df["hour"] = df["voted_at"].dt.hour
    return df


def get_aggregated_sessions_df() -> pd.DataFrame:
    """Gibt abgeschlossene Sessions mit aggregierten Stimmzahlen zurück (neues System)."""
    school_id = st.session_state.get("school_id", "default_school")
    conn = sqlite3.connect(get_db_file())
    try:
        df = pd.read_sql_query(
            """
            SELECT s.id AS session_id, s.phase, s.started_at, s.ended_at,
                   cl.name AS class_name,
                   SUM(CASE WHEN v.vote='Gut' THEN 1 ELSE 0 END) AS gut_count,
                   SUM(CASE WHEN v.vote='Mittel' THEN 1 ELSE 0 END) AS mittel_count,
                   SUM(CASE WHEN v.vote='Schlecht' THEN 1 ELSE 0 END) AS schlecht_count,
                   COUNT(v.id) AS total_votes
            FROM sessions s
            LEFT JOIN classes cl ON s.class_id = cl.id
            LEFT JOIN votes v ON v.session_id = s.id
            WHERE s.school_id=? AND s.is_discarded=0 AND s.ended_at IS NOT NULL
            GROUP BY s.id
            ORDER BY s.started_at DESC
            """,
            conn,
            params=(school_id,),
        )
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if not df.empty:
        df["started_at"] = pd.to_datetime(df["started_at"])
        df["date"] = df["started_at"].dt.date
    return df


def get_legacy_df() -> pd.DataFrame:
    """Gibt die alten Session-Logs zurück (Rückwärtskompatibilität)."""
    conn = sqlite3.connect(get_db_file())
    try:
        df = pd.read_sql_query("SELECT * FROM session_logs", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date
        df["class_name"] = "Alte Daten (vor Klassenstruktur)"
    return df


def save_dataframe_to_db(df_import: pd.DataFrame):
    """Speichert importierte Excel-Daten in session_logs (Legacy)."""
    conn = sqlite3.connect(get_db_file())
    columns_to_keep = ["phase", "gut_count", "mittel_count", "schlecht_count", "timestamp"]
    if all(col in df_import.columns for col in columns_to_keep):
        df_to_save = df_import[columns_to_keep].copy()
        df_to_save["timestamp"] = df_to_save["timestamp"].astype(str)
        df_to_save.to_sql("session_logs", conn, if_exists="append", index=False)
        conn.commit()
    conn.close()
