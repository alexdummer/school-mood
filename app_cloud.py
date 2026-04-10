import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from src.auth import check_password
from src.kiosk import show_kiosk_active
from src.dashboard import draw_dashboard

# --- DATENBANK VERBINDUNG (STREAMLIT CLOUD) ---
try:
    conn = st.connection("postgresql", type="sql")
    has_db = True
except Exception as e:
    has_db = False
    st.error(f"Datenbankverbindung fehlgeschlagen. Bitte .streamlit/secrets.toml prüfen! Fehler: {e}")


def init_db():
    if not has_db:
        return
    with conn.session as s:
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
        s.commit()


def save_session(phase, gut_count, mittel_count, schlecht_count, timestamp=None):
    if not has_db:
        st.warning("Keine Cloud-Datenbank Verbindung. Daten nicht gespeichert.")
        return

    if timestamp is None:
        timestamp = datetime.now()
    school_id = st.session_state.get("school_id", "default_school")

    with conn.session as s:
        s.execute(
            text(
                "INSERT INTO session_logs (school_id, phase, gut_count, mittel_count, schlecht_count, timestamp)"
                + " VALUES (:school, :phase, :g, :m, :s, :t)"
            ),
            {
                "school": school_id,
                "phase": phase,
                "g": gut_count,
                "m": mittel_count,
                "s": schlecht_count,
                "t": timestamp,
            },
        )
        s.commit()


def get_data():
    if not has_db:
        return pd.DataFrame()

    school_id = st.session_state.get("school_id", "default_school")
    try:
        df = conn.query(
            "SELECT * FROM session_logs WHERE school_id = :school",
            params={"school": school_id},
        )
    except Exception:
        df = pd.DataFrame()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date
        df["hour"] = df["timestamp"].dt.hour
        df["weekday"] = df["timestamp"].dt.day_name()
    return df


def sync_db_changes(original_df, edited_df):
    """Gleicht die Cloud Postgres-Datenbankeinträge mit dem Editor ab."""
    if not has_db:
        return

    orig_ids = set(original_df["id"])
    edited_ids = set(edited_df["id"].dropna())
    deleted_ids = orig_ids - edited_ids

    with conn.session as s:
        # 1. Löschungen
        for d_id in deleted_ids:
            s.execute(text("DELETE FROM session_logs WHERE id = :id"), {"id": int(d_id)})

        # 2. Updates
        for index, row in edited_df.iterrows():
            r_id = row.get("id")
            if pd.notna(r_id) and r_id in orig_ids:
                orig_row = original_df[original_df["id"] == r_id].iloc[0]
                if (
                    row["gut_count"] != orig_row["gut_count"]
                    or row["mittel_count"] != orig_row["mittel_count"]
                    or row["schlecht_count"] != orig_row["schlecht_count"]
                    or row["phase"] != orig_row["phase"]
                ):

                    s.execute(
                        text(
                            """
                        UPDATE session_logs
                        SET phase = :p, gut_count = :g, mittel_count = :m, schlecht_count = :s
                        WHERE id = :id
                    """
                        ),
                        {
                            "p": row["phase"],
                            "g": int(row["gut_count"]),
                            "m": int(row["mittel_count"]),
                            "s": int(row["schlecht_count"]),
                            "id": int(r_id),
                        },
                    )
        s.commit()


def show_admin_dashboard():
    st.title("📊 Cloud Auswertungs-Dashboard")
    df = get_data()

    filtered_df = draw_dashboard(df)

    if filtered_df is not None:
        with st.expander("Rohdaten ansehen, filtern & bearbeiten"):
            import time

            st.info(
                "Klicke in eine Zelle zum Bearbeiten oder wähle eine Zeile an der linken Seite aus,"
                + " um sie zu entfernen. Klicke danach auf 'Änderungen speichern'."
            )

            edit_df = filtered_df.sort_values(by="timestamp", ascending=False) if "timestamp" in filtered_df.columns else filtered_df

            edited_df = st.data_editor(
                edit_df,
                num_rows="dynamic",
                key="cloud_data_editor",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "school_id": st.column_config.TextColumn("Schul ID", disabled=True),
                    "timestamp": st.column_config.DatetimeColumn("Zeitpunkt", disabled=True),
                    "date": None,
                    "hour": None,
                    "weekday": None,
                },
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Änderungen in Cloud-Datenbank speichern", type="primary"):
                sync_db_changes(edit_df, edited_df)
                st.success("Daten in der Cloud aktualisiert!")
                time.sleep(1)
                st.rerun()


def main():
    st.set_page_config(page_title="Schul-Wohlbefinden (Cloud)", page_icon="🏫", layout="centered")

    css = ""
    if st.session_state.get("kiosk_active", False):
        css += """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

    if not check_password():
        st.stop()

    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    if st.session_state.get("kiosk_active", False):
        show_kiosk_active(st.session_state.get("kiosk_phase", "Unbekannt"), save_session)
        return

    st.sidebar.title("Navigation")
    st.sidebar.info(f"Eingeloggt als: **{st.session_state.school_id}**")

    app_mode = st.sidebar.radio("Gehe zu", ["Kiosk starten", "Admin Dashboard"])

    if app_mode == "Kiosk starten":
        st.title("Kiosk Session Setup")
        st.info("Stelle hier die Phase ein und starte die Session. Danach kann das Tablet den Kindern gegeben werden.")

        phase = st.radio("Modus für diese Session:", ["Ankunft in der Schule", "Nach Hause gehen"])

        if st.button("▶️ Kiosk Session starten", type="primary"):
            st.session_state.kiosk_active = True
            st.session_state.kiosk_phase = phase
            st.session_state.session_votes = {"Gut": 0, "Mittel": 0, "Schlecht": 0}
            st.session_state.session_start = datetime.now()
            st.rerun()

    elif app_mode == "Admin Dashboard":
        show_admin_dashboard()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Abmelden"):
        st.session_state["password_correct"] = False
        st.rerun()


if __name__ == "__main__":
    main()
