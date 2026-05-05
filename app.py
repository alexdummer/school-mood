import streamlit as st
from src.auth import check_password
from src.db import init_db
from src.kiosk import show_kiosk_active
from src.dashboard import draw_dashboard
from src.classes import show_class_manager


# --- MAIN APP LOGIC ---
def main():
    st.set_page_config(
        page_title="SchoolMood",
        page_icon="🏫",
        layout="centered",
    )

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

    # 1. Login
    if not check_password():
        st.stop()

    # 2. Datenbank initialisieren (einmalig pro Session)
    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    # 3. Kiosk-Modus aktiv?
    if st.session_state.get("kiosk_active", False):
        show_kiosk_active(
            session_id=st.session_state.get("kiosk_session_id"),
            phase=st.session_state.get("kiosk_phase", "Unbekannt"),
            class_name=st.session_state.get("kiosk_class_name", ""),
        )
        return

    # 4. Normales Admin-Menü
    st.sidebar.title("🏫 SchoolMood")
    st.sidebar.info(f"Eingeloggt als: **{st.session_state.school_id}**")

    app_mode = st.sidebar.radio(
        "Navigation",
        ["🏫 Klassen verwalten", "📊 Dashboard", "📡 Live-Anzeige"],
    )

    if app_mode == "🏫 Klassen verwalten":
        show_class_manager()

    elif app_mode == "📊 Dashboard":
        st.title("📊 Auswertungs-Dashboard")
        draw_dashboard()

    elif app_mode == "📡 Live-Anzeige":
        _show_live_view()

    # Abmelden
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Abmelden"):
        st.session_state["password_correct"] = False
        st.rerun()


def _show_live_view():
    """Live-Anzeige aller aktuell laufenden Sessions (mit Auto-Refresh)."""
    import time
    import plotly.graph_objects as go
    from src.db import get_active_sessions

    st.title("📡 Live-Anzeige")
    st.markdown("*Aktualisiert automatisch alle 10 Sekunden.*")

    placeholder = st.empty()

    active = get_active_sessions()

    with placeholder.container():
        if not active:
            st.info("⏳ Aktuell laufen keine Sessions. Starte eine Kiosk-Session unter 'Klassen verwalten'.")
        else:
            st.success(f"🟢 **{len(active)} aktive Session(s)**")
            st.markdown("---")

            cols_per_row = 2
            for i in range(0, len(active), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, sess in enumerate(active[i : i + cols_per_row]):
                    with cols[j]:
                        with st.container(border=True):
                            gut = sess["gut_count"]
                            mittel = sess["mittel_count"]
                            schlecht = sess["schlecht_count"]
                            total = sess["total_votes"]

                            st.markdown(
                                f"<h2 style='margin:0;'>🏷️ {sess['class_name']}</h2>"
                                f"<p style='color:gray; margin:0;'>{sess['phase']} · "
                                f"seit {sess['started_at'][:16]}</p>",
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
                                fig.update_layout(
                                    margin=dict(t=5, b=5, l=5, r=5),
                                    height=250,
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            c1, c2, c3 = st.columns(3)
                            c1.metric("😃 Gut", gut)
                            c2.metric("😐 Mittel", mittel)
                            c3.metric("☹️ Schlecht", schlecht)

    # Auto-Refresh
    time.sleep(10)
    st.rerun()


if __name__ == "__main__":
    main()
