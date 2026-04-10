import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import io
from src.auth import check_password
from src.kiosk import show_kiosk_active
from src.dashboard import draw_dashboard


# --- KONFIGURATION & DATENBANK ---
def get_db_file():
    """Gibt den Dateinamen der Datenbank für die aktuell eingeloggte Schule zurück."""
    school_id = st.session_state.get("school_id", "default_school")
    return f"stimmung_{school_id}.db"


def init_db():
    """Initialisiert die Datenbank der aktuellen Schule, falls sie nicht existiert."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
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
    conn.commit()
    conn.close()


def save_session(phase, gut_count, mittel_count, schlecht_count, timestamp=None):
    """Speichert die aggregierten Ergebnisse einer Kiosk-Session in der Datenbank."""
    if timestamp is None:
        timestamp = datetime.now()
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute(
        "INSERT INTO session_logs (phase, gut_count, mittel_count, schlecht_count, timestamp) VALUES (?, ?, ?, ?, ?)",
        (phase, gut_count, mittel_count, schlecht_count, timestamp),
    )
    conn.commit()
    conn.close()


def save_dataframe_to_db(df_import):
    """Speichert ein gesamtes DataFrame (z.B. aus einem Excel-Import) direkt in die Datenbank."""
    conn = sqlite3.connect(get_db_file())

    columns_to_keep = [
        "phase",
        "gut_count",
        "mittel_count",
        "schlecht_count",
        "timestamp",
    ]
    if all(col in df_import.columns for col in columns_to_keep):
        df_to_save = df_import[columns_to_keep].copy()
        df_to_save["timestamp"] = df_to_save["timestamp"].astype(str)
        df_to_save.to_sql("session_logs", conn, if_exists="append", index=False)
        conn.commit()
    conn.close()


def get_data():
    """Lädt alle Session-Daten der aktuellen Schule als Pandas DataFrame."""
    conn = sqlite3.connect(get_db_file())
    try:
        df = pd.read_sql_query("SELECT * FROM session_logs", conn)
    except pd.io.sql.DatabaseError:
        df = pd.DataFrame()
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date
        df["hour"] = df["timestamp"].dt.hour
        df["weekday"] = df["timestamp"].dt.day_name()
    return df


def sync_db_changes(original_df, edited_df):
    """Gleicht die lokalen SQLite-Datenbankeinträge mit dem Tabellen-Editor ab."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()

    orig_ids = set(original_df["id"])
    edited_ids = set(edited_df["id"].dropna())
    deleted_ids = orig_ids - edited_ids

    # 1. Löschungen übernehmen
    for d_id in deleted_ids:
        c.execute("DELETE FROM session_logs WHERE id=?", (int(d_id),))

    # 2. Updates übernehmen
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

                c.execute(
                    "UPDATE session_logs SET phase=?, gut_count=?, mittel_count=?, schlecht_count=? WHERE id=?",
                    (
                        row["phase"],
                        int(row["gut_count"]),
                        int(row["mittel_count"]),
                        int(row["schlecht_count"]),
                        int(r_id),
                    ),
                )
    conn.commit()
    conn.close()


def show_admin_dashboard():
    """Die Ansicht für Auswertungen."""
    st.title("📊 Auswertungs-Dashboard")

    df = get_data()

    # --- IMPORT BEREICH ---
    with st.expander("📥 Excel Daten Importieren / Zusammenführen"):
        uploaded_file = st.file_uploader("Wähle eine Excel Datei (.xlsx) aus", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df_imported = pd.read_excel(uploaded_file)
                st.write("Vorschau der hochgeladenen Daten:")
                st.dataframe(df_imported.head(3))

                col_imp1, col_imp2 = st.columns(2)
                with col_imp1:
                    if st.button("Nur ansehen (temporär)"):
                        df = pd.concat([df, df_imported], ignore_index=True)
                        if "timestamp" in df.columns:
                            df["timestamp"] = pd.to_datetime(df["timestamp"])
                            df["date"] = df["timestamp"].dt.date
                            df["hour"] = df["timestamp"].dt.hour
                            df["weekday"] = df["timestamp"].dt.day_name()
                        st.success("Daten wurden temporär hinzugefügt!")

                with col_imp2:
                    if st.button("In Datenbank speichern"):
                        save_dataframe_to_db(df_imported)
                        st.success("Daten wurden dauerhaft in die Datenbank übernommen!")
                        time.sleep(2)
                        st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Einlesen der Excel Datei: {e}")

    filtered_df = draw_dashboard(df)

    if filtered_df is not None:
        # Rohdaten anzeigen und Bearbeiten
        with st.expander("Rohdaten ansehen, filtern & bearbeiten"):
            st.info(
                "Klicke in eine Zelle zum Bearbeiten oder wähle eine Zeile"
                + " an der linken Seite aus, um sie zu entfernen. Klicke danach auf 'Änderungen speichern'."
            )

            edit_df = filtered_df.sort_values(by="timestamp", ascending=False) if "timestamp" in filtered_df.columns else filtered_df

            edited_df = st.data_editor(
                edit_df,
                num_rows="dynamic",
                key="local_data_editor",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "timestamp": st.column_config.DatetimeColumn("Zeitpunkt", disabled=True),
                    "date": None,
                    "hour": None,
                    "weekday": None,
                },
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_dwn = st.columns([1, 1])

            with col_save:
                if st.button("💾 Änderungen in Datenbank speichern", type="primary"):
                    sync_db_changes(edit_df, edited_df)
                    st.success("Daten erfolgreich aktualisiert!")
                    time.sleep(1)
                    st.rerun()

            # Excel Export Button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                filtered_df.to_excel(writer, index=False, sheet_name="SchoolMood_Data")

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Als Excel (XLSX) herunterladen",
                data=buffer.getvalue(),
                file_name="schoolmood_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# --- MAIN APP LOGIC ---
def main():
    st.set_page_config(page_title="Schul-Wohlbefinden", page_icon="🏫", layout="centered")

    # CSS Hacks um Streamlit "app-artiger" aussehen zu lassen
    css = "<style>"

    # Wenn Kiosk aktiv ist, blenden wir die Sidebar komplett per CSS aus
    if st.session_state.get("kiosk_active", False):
        css += """
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        """

    css += "</style>"

    st.markdown(css, unsafe_allow_html=True)

    # 1. Globale Authentifizierung: Nichts passiert ohne Login
    if not check_password():
        st.stop()  # Stoppt die Ausführung hier, bis das Passwort stimmt

    # 2. Datenbank für die jetzt eingeloggte Schule initialisieren!
    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    # 3. Prüfen, ob eine Kiosk-Session läuft
    if st.session_state.get("kiosk_active", False):
        show_kiosk_active(st.session_state.get("kiosk_phase", "Unbekannt"), save_session)
        return

    # 4. Normales Menü (für die Lehrkraft)
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

    # Abmelde-Button in der Sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Abmelden"):
        st.session_state["password_correct"] = False
        st.rerun()


if __name__ == "__main__":
    main()
