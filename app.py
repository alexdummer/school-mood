import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px
import time

# --- KONFIGURATION & DATENBANK ---
def get_db_file():
    """Gibt den Dateinamen der Datenbank für die aktuell eingeloggte Schule zurück."""
    # Standard-Fallback, falls (aus welchem Grund auch immer) keine ID gesetzt ist
    school_id = st.session_state.get('school_id', 'default_school')
    return f"stimmung_{school_id}.db"

def init_db():
    """Initialisiert die Datenbank der aktuellen Schule, falls sie nicht existiert."""
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            phase TEXT,
            gut_count INTEGER DEFAULT 0,
            mittel_count INTEGER DEFAULT 0,
            schlecht_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def save_session(phase, gut_count, mittel_count, schlecht_count, timestamp=None):
    """Speichert die aggregierten Ergebnisse einer Kiosk-Session in der Datenbank."""
    if timestamp is None:
        timestamp = datetime.now()
    conn = sqlite3.connect(get_db_file())
    c = conn.cursor()
    c.execute("INSERT INTO session_logs (phase, gut_count, mittel_count, schlecht_count, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (phase, gut_count, mittel_count, schlecht_count, timestamp))
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
    
    # Konvertiere timestamp string in datetime objekt
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Hilfsspalten für bessere Auswertung
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['weekday'] = df['timestamp'].dt.day_name()
    return df

# --- AUTHENTIFIZIERUNG ---
def check_password():
    """Prüft Schul-ID und Passwort gegen secrets.toml"""
    def password_entered():
        school_id = st.session_state["username_input"].strip().lower()
        password = st.session_state["password_input"]

        try:
            # Greife auf das [passwords] dictionary im secrets file zu
            correct_password = st.secrets["passwords"][school_id]
            if password == correct_password:
                st.session_state["password_correct"] = True
                st.session_state["school_id"] = school_id
                del st.session_state["password_input"]  # Passwort aus Speicher löschen
            else:
                st.session_state["password_correct"] = False
        except KeyError:
            # Schule existiert nicht im secrets.toml oder secrets.toml fehlt
            # Fallback für lokales Testen ohne secrets.toml:
            if school_id == "test" and password == "admin":
                st.session_state["password_correct"] = True
                st.session_state["school_id"] = "testschule"
                del st.session_state["password_input"]
            else:
                st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Login für Schulen")
        st.text_input("Schul-ID (Benutzername)", key="username_input")
        st.text_input("Passwort", type="password", key="password_input")
        st.button("Einloggen", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Login für Schulen")
        st.text_input("Schul-ID (Benutzername)", key="username_input")
        st.text_input("Passwort", type="password", key="password_input")
        st.button("Einloggen", on_click=password_entered)
        st.error("😕 Schul-ID oder Passwort falsch")
        return False
    else:
        return True


# --- UI FUNKTIONEN ---

def show_kiosk_active(phase):
    """Die aktive Kiosk-Ansicht für das Tablet der Kinder (ohne Navigation)."""
    st.markdown("<h1 style='text-align: center;'>Wie geht es dir heute?</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>{phase}</h3>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <style>
    /* Größenanpassung: Streamlit verpackt Text in <p> Tags in Buttons */
    div[data-testid="stButton"] button p, div.stButton > button p {
        font-size: 100px !important;
        line-height: 1 !important;
        margin: 0 !important;
    }
    div[data-testid="stButton"] button, div.stButton > button {
        height: 200px !important;
        width: 100% !important;
    }

    /* Farben für die Abstimmungs-Buttons in Kiosk View */
    /* 1. Button: Grün */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(1) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button {
        background-color: #2ecc71 !important;
        border: 2px solid #27ae60 !important;
    }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button:hover,
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] button:hover,
    div[data-testid="column"]:nth-of-type(1) div.stButton > button:hover,
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button:hover {
        background-color: #27ae60 !important;
    }
    
    /* 2. Button: Orange */
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(2) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button {
        background-color: #f39c12 !important;
        border: 2px solid #e67e22 !important;
    }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button:hover,
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] button:hover,
    div[data-testid="column"]:nth-of-type(2) div.stButton > button:hover,
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button:hover {
        background-color: #e67e22 !important;
    }
    
    /* 3. Button: Rot */
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(3) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(3) div.stButton > button {
        background-color: #e74c3c !important;
        border: 2px solid #c0392b !important;
    }
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stButton"] button:hover,
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] button:hover,
    div[data-testid="column"]:nth-of-type(3) div.stButton > button:hover,
    div[data-testid="stColumn"]:nth-of-type(3) div.stButton > button:hover {
        background-color: #c0392b !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    if 'voted' not in st.session_state:
        st.session_state.voted = False

    if st.session_state.voted:
        st.success("Danke! Deine Stimmung wurde gespeichert.")
        time.sleep(2) # Kurze Pause, dann Reset
        st.session_state.voted = False
        st.rerun()
    
    # Die Buttons aktualisieren nur noch den lokalen Session-State
    with col1:
        if st.button("😃"):
            st.session_state.session_votes["Gut"] += 1
            st.session_state.voted = True
            st.rerun()
            
    with col2:
        if st.button("😐"):
            st.session_state.session_votes["Mittel"] += 1
            st.session_state.voted = True
            st.rerun()

    with col3:
        if st.button("☹️"):
            st.session_state.session_votes["Schlecht"] += 1
            st.session_state.voted = True
            st.rerun()

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Versteckter Beenden-Button für die Lehrkraft
    with st.expander("Lehrkraft-Bereich"):
        # Vorschau der Stimmen
        st.write(f"Bisherige Stimmen (werden beim Beenden gespeichert):")
        st.write(f"😃 {st.session_state.session_votes['Gut']} | 😐 {st.session_state.session_votes['Mittel']} | ☹️ {st.session_state.session_votes['Schlecht']}")
        if st.button("❌ Session beenden"):
            # Speichere die aggregierten Daten in die Datenbank
            save_session(
                phase=phase,
                gut_count=st.session_state.session_votes["Gut"],
                mittel_count=st.session_state.session_votes["Mittel"],
                schlecht_count=st.session_state.session_votes["Schlecht"],
                timestamp=st.session_state.session_start
            )
            # Aufräumen
            st.session_state.kiosk_active = False
            del st.session_state.session_votes
            del st.session_state.session_start
            st.rerun()

def show_admin_dashboard():
    """Die Ansicht für Auswertungen."""
    st.title("📊 Auswertungs-Dashboard")
    
    df = get_data()
    
    if df.empty:
        st.warning("Noch keine Daten vorhanden.")
        return

    # Filter-Optionen in der Sidebar (oder oben)
    st.subheader("Filter")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_phase = st.multiselect("Phase wählen", df['phase'].unique(), default=df['phase'].unique())
    with col_f2:
        # Datumsbereich
        min_date = df['date'].min()
        max_date = df['date'].max()
        date_range = st.date_input("Zeitraum", [min_date, max_date])

    # Daten filtern
    mask = (df['phase'].isin(selected_phase))
    # Einfache Datumsfilter-Logik (falls range gewählt wurde)
    if isinstance(date_range, list) and len(date_range) == 2:
        mask = mask & (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
    
    filtered_df = df[mask]
    
    # KPIs
    st.markdown("### Übersicht")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    if len(filtered_df) > 0:
        gut_total = int(filtered_df['gut_count'].sum())
        mittel_total = int(filtered_df['mittel_count'].sum())
        schlecht_total = int(filtered_df['schlecht_count'].sum())
        total_votes = gut_total + mittel_total + schlecht_total
    else:
        gut_total = mittel_total = schlecht_total = total_votes = 0

    kpi1.metric("Gesamtzahl Stimmen", total_votes)
    kpi3.metric("Erfasste Kiosk-Sessions", len(filtered_df))
    
    if total_votes > 0:
        pct_gut = round((gut_total / total_votes) * 100, 1)
        kpi2.metric("Anteil 'Gut'", f"{pct_gut}%")
    else:
        kpi2.metric("Anteil 'Gut'", "0%")

    # --- VISUALISIERUNGEN ---
    
    # 1. Stimmung Verteilung (Tortendiagramm)
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Verteilung der Stimmung")
        mood_counts = pd.DataFrame({
            'Stimmung': ['Gut', 'Mittel', 'Schlecht'],
            'Anzahl': [gut_total, mittel_total, schlecht_total]
        })
        
        # Eigene Farben definieren
        color_map = {"Gut": "#2ecc71", "Mittel": "#f1c40f", "Schlecht": "#e74c3c"}
        
        fig_pie = px.pie(mood_counts, values='Anzahl', names='Stimmung', 
                         color='Stimmung', color_discrete_map=color_map, hole=0.4)
        st.plotly_chart(fig_pie)

    # 2. Verlauf über die Zeit (Balkendiagramm gestapelt nach Datum)
    with c2:
        st.subheader("Verlauf über Tage")
        if not filtered_df.empty:
            daily_mood = filtered_df.groupby('date')[['gut_count', 'mittel_count', 'schlecht_count']].sum().reset_index()
            daily_mood_melted = daily_mood.melt(id_vars='date', value_vars=['gut_count', 'mittel_count', 'schlecht_count'], var_name='mood', value_name='Anzahl')
            daily_mood_melted['mood'] = daily_mood_melted['mood'].map({'gut_count': 'Gut', 'mittel_count': 'Mittel', 'schlecht_count': 'Schlecht'})
            
            fig_bar = px.bar(daily_mood_melted, x='date', y='Anzahl', color='mood', 
                             color_discrete_map=color_map, barmode='group')
            st.plotly_chart(fig_bar)
        else:
            st.info("Keine Daten für Verlauf")

    # 3. Tageszeit-Trend (Wann wird abgestimmt?)
    st.markdown("---")
    st.subheader("Aktivität nach Uhrzeit")
    if not filtered_df.empty:
        # Summiere alle Stimmen pro Stunde
        hourly_counts = filtered_df.groupby('hour')[['gut_count', 'mittel_count', 'schlecht_count']].sum().sum(axis=1).reset_index(name='Anzahl Stimmen')
        fig_line = px.line(hourly_counts, x='hour', y='Anzahl Stimmen', markers=True)
        st.plotly_chart(fig_line)
    else:
        st.info("Keine Daten für Tageszeit-Trend")
    
    # Rohdaten anzeigen (optional)
    with st.expander("Rohdaten anzeigen"):
        st.dataframe(filtered_df.sort_values(by='timestamp', ascending=False))


# --- MAIN APP LOGIC ---
def main():
    st.set_page_config(page_title="Schul-Wohlbefinden", page_icon="🏫", layout="centered")
    
    # CSS Hacks um Streamlit "app-artiger" aussehen zu lassen
    css = """
    <style>
    div.stButton > button:first-child {
        font-size: 100px;
        height: 200px;
        margin-top: 20px;
    }
    """
    
    # Wenn Kiosk aktiv ist, blenden wir die Sidebar komplett per CSS aus, 
    # damit Kinder nicht im Menü herumklicken können.
    if st.session_state.get('kiosk_active', False):
        css += """
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        """
        
    css += "</style>"
        
    st.markdown(css, unsafe_allow_html=True)

    # 1. Globale Authentifizierung: Nichts passiert ohne Login
    if not check_password():
        st.stop() # Stoppt die Ausführung hier, bis das Passwort stimmt

    # 2. Datenbank für die jetzt eingeloggte Schule initialisieren!
    # (Muss nach dem Login passieren, da wir vorher die school_id nicht kennen)
    init_db()

    # 3. Prüfen, ob eine Kiosk-Session läuft
    if st.session_state.get('kiosk_active', False):
        show_kiosk_active(st.session_state.get('kiosk_phase', 'Unbekannt'))
        return # Stoppt hier, damit das normale Menü nicht geladen wird

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