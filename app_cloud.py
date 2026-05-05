"""
Cloud-Version von SchoolMood (Streamlit Community Cloud / PostgreSQL).
Entspricht funktional app.py, nutzt aber st.connection("postgresql") statt SQLite.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from src.auth import check_password
from src.kiosk import show_kiosk_active
from src.dashboard import draw_dashboard
from src.classes import show_class_manager

st.set_page_config(page_title="SchoolMood Cloud", page_icon="🏫", layout="centered")

# ---------------------------------------------------------------------------
# Datenbankverbindung (PostgreSQL via Streamlit Secrets)
# ---------------------------------------------------------------------------
try:
    conn = st.connection("postgresql", type="sql")
    has_db = True
except Exception as e:
    has_db = False
    st.error(f"Datenbankverbindung fehlgeschlagen. Bitte .streamlit/secrets.toml prüfen! Fehler: {e}")


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Cloud-DB-Operationen
# (werden in st.session_state injiziert, damit db.py-Aufrufe aus kiosk.py
#  und classes.py transparent über PostgreSQL laufen)
# ---------------------------------------------------------------------------


def _school_id() -> str:
    return st.session_state.get("school_id", "default_school")


def init_db_cloud():
    """Legt alle Tabellen in PostgreSQL an (falls nicht vorhanden)."""
    if not has_db:
        return
    with conn.session as s:
        # Legacy
        s.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS session_logs (
                id SERIAL PRIMARY KEY,
                school_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                phase TEXT,
                gut_count INTEGER DEFAULT 0,
                mittel_count INTEGER DEFAULT 0,
                schlecht_count INTEGER DEFAULT 0
            )
        """
            )
        )
        # Klassen
        s.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS classes (
                id SERIAL PRIMARY KEY,
                school_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        # Sessions
        s.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                school_id TEXT NOT NULL,
                class_id INTEGER REFERENCES classes(id),
                phase TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                is_discarded INTEGER DEFAULT 0
            )
        """
            )
        )
        # Stimmen
        s.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS votes (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id),
                vote TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        s.commit()


# ---------------------------------------------------------------------------
# Cloud-Implementierungen der db.py-Funktionen
# (Monkey-Patch: src.db wird für Cloud durch diese ersetzt)
# ---------------------------------------------------------------------------


def _cloud_cast_vote(session_id: int, vote: str):
    if not has_db:
        st.warning("Keine DB-Verbindung – Stimme nicht gespeichert.")
        return
    with conn.session as s:
        s.execute(
            text("INSERT INTO votes (session_id, vote, voted_at) VALUES (:sid, :v, :t)"),
            {"sid": session_id, "v": vote, "t": datetime.now()},
        )
        s.commit()


def _cloud_get_session_vote_counts(session_id: int) -> dict:
    if not has_db:
        return {"Gut": 0, "Mittel": 0, "Schlecht": 0}
    df = conn.query(
        "SELECT vote, COUNT(*) AS cnt FROM votes WHERE session_id = :sid GROUP BY vote",
        params={"sid": session_id},
        ttl=0,
    )
    counts = {"Gut": 0, "Mittel": 0, "Schlecht": 0}
    for _, row in df.iterrows():
        if row["vote"] in counts:
            counts[row["vote"]] = int(row["cnt"])
    return counts


def _cloud_close_session(session_id: int):
    if not has_db:
        return
    with conn.session as s:
        s.execute(
            text("UPDATE sessions SET ended_at = :t WHERE id = :sid"),
            {"t": datetime.now(), "sid": session_id},
        )
        s.commit()


def _cloud_discard_session(session_id: int):
    if not has_db:
        return
    with conn.session as s:
        s.execute(text("DELETE FROM votes WHERE session_id = :sid"), {"sid": session_id})
        s.execute(
            text("UPDATE sessions SET ended_at = :t, is_discarded = 1 WHERE id = :sid"),
            {"t": datetime.now(), "sid": session_id},
        )
        s.commit()


def _cloud_get_active_sessions() -> list[dict]:
    if not has_db:
        return []
    school = _school_id()
    df = conn.query(
        """
        SELECT s.id, s.phase, s.started_at::text AS started_at, cl.name AS class_name,
               SUM(CASE WHEN v.vote='Gut' THEN 1 ELSE 0 END) AS gut_count,
               SUM(CASE WHEN v.vote='Mittel' THEN 1 ELSE 0 END) AS mittel_count,
               SUM(CASE WHEN v.vote='Schlecht' THEN 1 ELSE 0 END) AS schlecht_count,
               COUNT(v.id) AS total_votes
        FROM sessions s
        LEFT JOIN classes cl ON s.class_id = cl.id
        LEFT JOIN votes v ON v.session_id = s.id
        WHERE s.school_id = :school AND s.ended_at IS NULL AND s.is_discarded = 0
        GROUP BY s.id, s.phase, s.started_at, cl.name
        ORDER BY s.started_at DESC
        """,
        params={"school": school},
        ttl=0,
    )
    return df.to_dict("records") if not df.empty else []


def _cloud_open_session(class_id: int, phase: str) -> int:
    if not has_db:
        return -1
    school = _school_id()
    with conn.session as s:
        result = s.execute(
            text("INSERT INTO sessions (school_id, class_id, phase, started_at)" " VALUES (:school, :cid, :phase, :t) RETURNING id"),
            {"school": school, "cid": class_id, "phase": phase, "t": datetime.now()},
        )
        session_id = result.fetchone()[0]
        s.commit()
    return session_id


def _cloud_get_classes() -> list[dict]:
    if not has_db:
        return []
    school = _school_id()
    df = conn.query(
        "SELECT id, name, created_at::text AS created_at FROM classes WHERE school_id = :school ORDER BY name",
        params={"school": school},
        ttl=0,
    )
    return df.to_dict("records") if not df.empty else []


def _cloud_create_class(name: str) -> int:
    if not has_db:
        return -1
    school = _school_id()
    with conn.session as s:
        result = s.execute(
            text("INSERT INTO classes (school_id, name) VALUES (:school, :name) RETURNING id"),
            {"school": school, "name": name.strip()},
        )
        class_id = result.fetchone()[0]
        s.commit()
    return class_id


def _cloud_delete_class(class_id: int):
    if not has_db:
        return
    with conn.session as s:
        s.execute(text("DELETE FROM classes WHERE id = :cid"), {"cid": class_id})
        s.commit()


def _cloud_get_new_votes_df() -> pd.DataFrame:
    if not has_db:
        return pd.DataFrame()
    school = _school_id()
    try:
        df = conn.query(
            """
            SELECT v.id, v.vote, v.voted_at,
                   s.phase, s.started_at AS session_start,
                   cl.name AS class_name, cl.id AS class_id,
                   s.id AS session_id
            FROM votes v
            JOIN sessions s ON v.session_id = s.id
            JOIN classes cl ON s.class_id = cl.id
            WHERE s.is_discarded = 0 AND s.school_id = :school
            ORDER BY v.voted_at DESC
            """,
            params={"school": school},
            ttl=0,
        )
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df["voted_at"] = pd.to_datetime(df["voted_at"])
        df["date"] = df["voted_at"].dt.date
        df["hour"] = df["voted_at"].dt.hour
    return df


def _cloud_get_aggregated_sessions_df() -> pd.DataFrame:
    if not has_db:
        return pd.DataFrame()
    school = _school_id()
    try:
        df = conn.query(
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
            WHERE s.school_id = :school AND s.is_discarded = 0 AND s.ended_at IS NOT NULL
            GROUP BY s.id, s.phase, s.started_at, s.ended_at, cl.name
            ORDER BY s.started_at DESC
            """,
            params={"school": school},
            ttl=0,
        )
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df["started_at"] = pd.to_datetime(df["started_at"])
        df["date"] = df["started_at"].dt.date
    return df


def _cloud_get_legacy_df() -> pd.DataFrame:
    if not has_db:
        return pd.DataFrame()
    school = _school_id()
    try:
        df = conn.query(
            "SELECT * FROM session_logs WHERE school_id = :school",
            params={"school": school},
            ttl=0,
        )
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date
        df["class_name"] = "Alte Daten (vor Klassenstruktur)"
    return df


# ---------------------------------------------------------------------------
# Monkey-Patch: src.db durch Cloud-Funktionen ersetzen
# ---------------------------------------------------------------------------


def _patch_db_module():
    """Ersetzt die SQLite-Implementierungen in src.db durch PostgreSQL-Varianten."""
    import src.db as db_module

    db_module.cast_vote = _cloud_cast_vote
    db_module.get_session_vote_counts = _cloud_get_session_vote_counts
    db_module.close_session = _cloud_close_session
    db_module.discard_session = _cloud_discard_session
    db_module.get_active_sessions = _cloud_get_active_sessions
    db_module.open_session = _cloud_open_session
    db_module.get_classes = _cloud_get_classes
    db_module.create_class = _cloud_create_class
    db_module.delete_class = _cloud_delete_class
    db_module.get_new_votes_df = _cloud_get_new_votes_df
    db_module.get_aggregated_sessions_df = _cloud_get_aggregated_sessions_df
    db_module.get_legacy_df = _cloud_get_legacy_df


# ---------------------------------------------------------------------------
# Live-Ansicht
# ---------------------------------------------------------------------------


def _show_live_view():
    import time
    import plotly.graph_objects as go

    st.title("📡 Live-Anzeige")
    st.markdown("*Aktualisiert automatisch alle 10 Sekunden.*")

    active = _cloud_get_active_sessions()

    if not active:
        st.info("⏳ Aktuell laufen keine Sessions.")
    else:
        st.success(f"🟢 **{len(active)} aktive Session(s)**")
        st.markdown("---")

        cols_per_row = 2
        for i in range(0, len(active), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, sess in enumerate(active[i : i + cols_per_row]):
                with cols[j]:
                    gut = int(sess.get("gut_count") or 0)
                    mittel = int(sess.get("mittel_count") or 0)
                    schlecht = int(sess.get("schlecht_count") or 0)
                    total = int(sess.get("total_votes") or 0)

                    st.markdown(
                        "<div style='border:1px solid #dee2e6; border-radius:8px; padding:12px 16px; margin-bottom:8px;'>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<h2 style='margin:0;'>🏷️ {sess['class_name']}</h2>"
                        f"<p style='color:gray; margin:0;'>{sess['phase']} · "
                        f"seit {str(sess['started_at'])[:16]}</p>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{total} Stimmen bisher**")

                    if total > 0:
                        fig = go.Figure(
                            data=[
                                go.Pie(
                                    labels=["Gut", "Mittel", "Schlecht"],
                                    values=[gut, mittel, schlecht],
                                    marker=dict(colors=["#2ecc71", "#f39c12", "#e74c3c"]),
                                    hole=0.5,
                                    textinfo="label+percent",
                                )
                            ]
                        )
                        fig.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=250)
                        st.plotly_chart(fig, use_container_width=True)

                    c1, c2, c3 = st.columns(3)
                    c1.metric("😃 Gut", gut)
                    c2.metric("😐 Mittel", mittel)
                    c3.metric("☹️ Schlecht", schlecht)
                    st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(10)
    st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    # DB-Funktionen patchen (SQLite → PostgreSQL)
    _patch_db_module()

    # CSS: Sidebar ausblenden wenn Kiosk aktiv
    css = "<style>"
    if st.session_state.get("kiosk_active", False):
        css += """
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .stApp > header { display: none !important; }
        .block-container {
            max-width: 100% !important;
            padding-top: 1rem !important;
            padding-right: 1rem !important;
            padding-left: 1rem !important;
            padding-bottom: 1rem !important;
        }
        """
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)

    # Login
    if not check_password():
        st.stop()

    # DB initialisieren
    if "db_initialized" not in st.session_state:
        init_db_cloud()
        st.session_state.db_initialized = True

    # Kiosk aktiv?
    if st.session_state.get("kiosk_active", False):
        show_kiosk_active(
            session_id=st.session_state.get("kiosk_session_id"),
            phase=st.session_state.get("kiosk_phase", "Unbekannt"),
            class_name=st.session_state.get("kiosk_class_name", ""),
        )
        return

    # Admin-Menü
    st.sidebar.title("🏫 SchoolMood Cloud")
    st.sidebar.info(f"Eingeloggt als: **{st.session_state.school_id}**")

    app_mode = st.sidebar.radio(
        "Navigation",
        ["🏫 Klassen verwalten", "📊 Dashboard", "📡 Live-Anzeige"],
    )

    if app_mode == "🏫 Klassen verwalten":
        show_class_manager()

    elif app_mode == "📊 Dashboard":
        st.title("📊 Cloud Auswertungs-Dashboard")
        draw_dashboard()

    elif app_mode == "📡 Live-Anzeige":
        _show_live_view()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Abmelden"):
        st.session_state["password_correct"] = False
        st.rerun()


if __name__ == "__main__":
    main()
