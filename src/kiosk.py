# Letztes Update: Klassen-Support & sofortige DB-Persistenz
import streamlit as st
import plotly.graph_objects as go
import uuid
import src.db as db


def show_kiosk_active(session_id: int, phase: str, class_name: str):
    """Die aktive Kiosk-Ansicht für das Klassen-Tablet (ohne Navigation).

    Jede Stimme wird sofort in die DB geschrieben – kein Datenverlust
    auch wenn der Browser geschlossen wird.
    """
    if "show_popup" not in st.session_state:
        st.session_state.show_popup = False
    if "popup_type" not in st.session_state:
        st.session_state.popup_type = ""
    if "confirm_discard" not in st.session_state:
        st.session_state.confirm_discard = False

    # ── Kopfzeile ─────────────────────────────────────────────────────────────
    st.markdown(
        "<h1 style='text-align: center; font-size: clamp(1.5rem, 5vw, 3rem); margin-bottom: 0;'>" "Wie geht es dir heute?</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h3 style='text-align: center; color: gray; font-size: clamp(1rem, 3vw, 1.5rem); margin-top: 0;'>" f"{class_name} · {phase}</h3>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Button-Styling ────────────────────────────────────────────────────────
    st.markdown(
        """
    <style>
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button p,
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] button p,
    div[data-testid="column"]:nth-of-type(1) div.stButton > button p,
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button p,
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button p,
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] button p,
    div[data-testid="column"]:nth-of-type(2) div.stButton > button p,
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button p,
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stButton"] button p,
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] button p,
    div[data-testid="column"]:nth-of-type(3) div.stButton > button p,
    div[data-testid="stColumn"]:nth-of-type(3) div.stButton > button p {
        font-size: clamp(40px, 10vw, 100px) !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(1) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button,
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(2) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button,
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(3) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(3) div.stButton > button {
        height: clamp(60px, 20vh, 200px) !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Farben */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(1) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button {
        background-color: #2ecc71 !important; border: 2px solid #27ae60 !important;
    }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button:hover,
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] button:hover,
    div[data-testid="column"]:nth-of-type(1) div.stButton > button:hover,
    div[data-testid="stColumn"]:nth-of-type(1) div.stButton > button:hover {
        background-color: #27ae60 !important;
    }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(2) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button {
        background-color: #f39c12 !important; border: 2px solid #e67e22 !important;
    }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button:hover,
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] button:hover,
    div[data-testid="column"]:nth-of-type(2) div.stButton > button:hover,
    div[data-testid="stColumn"]:nth-of-type(2) div.stButton > button:hover {
        background-color: #e67e22 !important;
    }
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stButton"] button,
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] button,
    div[data-testid="column"]:nth-of-type(3) div.stButton > button,
    div[data-testid="stColumn"]:nth-of-type(3) div.stButton > button {
        background-color: #e74c3c !important; border: 2px solid #c0392b !important;
    }
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stButton"] button:hover,
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] button:hover,
    div[data-testid="column"]:nth-of-type(3) div.stButton > button:hover,
    div[data-testid="stColumn"]:nth-of-type(3) div.stButton > button:hover {
        background-color: #c0392b !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ── Hauptbereich: Buttons links, Live-Chart rechts ────────────────────────
    main_col_left, main_col_right = st.columns([5, 4], gap="small")

    with main_col_left:
        st.markdown("<div style='margin-top: clamp(20px, 12vh, 120px);'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("😃"):
                db.cast_vote(session_id, "Gut")
                st.session_state.show_popup = True
                st.session_state.popup_type = "Gut"

        with col2:
            if st.button("😐"):
                db.cast_vote(session_id, "Mittel")
                st.session_state.show_popup = True
                st.session_state.popup_type = "Mittel"

        with col3:
            if st.button("☹️"):
                db.cast_vote(session_id, "Schlecht")
                st.session_state.show_popup = True
                st.session_state.popup_type = "Schlecht"

    with main_col_right:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Aktuelle Stimmung:")

        # Stimmen direkt aus DB lesen (aktueller Stand)
        counts = db.get_session_vote_counts(session_id)
        total_live = sum(counts.values())

        if total_live > 0:
            labels = ["Gut", "Mittel", "Schlecht"]
            values = [counts["Gut"], counts["Mittel"], counts["Schlecht"]]
            colors = ["#2ecc71", "#f39c12", "#e74c3c"]
            fig_live = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=0.4)])
            fig_live.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_live, use_container_width=True)
        else:
            st.write("*Noch keine Stimmen abgegeben.*")

    # ── Popup ─────────────────────────────────────────────────────────────────
    if st.session_state.show_popup:
        st.session_state.show_popup = False

        color_map = {
            "Gut": ("😃", "#2ecc71", "#eafaf1"),
            "Mittel": ("😐", "#f39c12", "#fef5e7"),
            "Schlecht": ("☹️", "#e74c3c", "#fdedec"),
        }
        emoji, color, bg_color = color_map.get(st.session_state.popup_type, ("✅", "#2ecc71", "#eafaf1"))
        unique_id = uuid.uuid4().hex

        popup_html = f"""
        <style>
        .custom-overlay-{unique_id} {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.6); z-index: 99998;
            animation: fadeOutOverlay-{unique_id} 2.5s forwards; pointer-events: none;
        }}
        .custom-popup-{unique_id} {{
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            background: {bg_color};
            padding: clamp(20px, 5vw, 50px) clamp(30px, 8vw, 80px);
            border-radius: clamp(15px, 3vw, 30px); width: 80%; max-width: 600px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5); z-index: 99999;
            text-align: center; border: clamp(4px, 1vw, 8px) solid {color};
            animation: fadeOutPopup-{unique_id} 2.5s forwards; pointer-events: none;
        }}
        .custom-popup-{unique_id} h1 {{
            font-size: clamp(60px, 15vw, 150px); margin: 0; padding: 0; line-height: 1.2;
        }}
        .custom-popup-{unique_id} p {{
            font-size: clamp(20px, 5vw, 45px); color: #333; margin-top: 15px;
            font-family: sans-serif; font-weight: bold;
        }}
        @keyframes fadeOutOverlay-{unique_id} {{
            0% {{ opacity: 1; visibility: visible; }}
            70% {{ opacity: 1; visibility: visible; }}
            100% {{ opacity: 0; visibility: hidden; }}
        }}
        @keyframes fadeOutPopup-{unique_id} {{
            0% {{ opacity: 0; visibility: visible; transform: translate(-50%, -50%) scale(0.5); }}
            10% {{ opacity: 1; transform: translate(-50%, -50%) scale(1.1); }}
            20% {{ transform: translate(-50%, -50%) scale(1); }}
            70% {{ opacity: 1; visibility: visible; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0; visibility: hidden; transform: translate(-50%, -50%) scale(0.8); }}
        }}
        </style>
        <div class="custom-overlay-{unique_id}"></div>
        <div class="custom-popup-{unique_id}">
            <h1>{emoji}</h1>
            <p>Danke!<br>Deine Stimmung wurde gespeichert.</p>
        </div>
        """
        st.markdown(popup_html, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Lehrkraft-Bereich ─────────────────────────────────────────────────────
    with st.expander("🔒 Lehrkraft-Bereich"):
        counts = db.get_session_vote_counts(session_id)
        st.write("**Bisherige Stimmen:**")
        col_g, col_m, col_s = st.columns(3)
        col_g.metric("😃 Gut", counts["Gut"])
        col_m.metric("😐 Mittel", counts["Mittel"])
        col_s.metric("☹️ Schlecht", counts["Schlecht"])

        st.markdown("---")

        # Confirm-Discard-State
        if st.session_state.confirm_discard:
            st.warning("⚠️ Wirklich alle Stimmen dieser Session löschen?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("🗑️ Ja, verwerfen", type="primary", use_container_width=True):
                    db.discard_session(session_id)
                    _reset_kiosk_state()
                    st.rerun()
            with col_no:
                if st.button("Abbrechen", use_container_width=True):
                    st.session_state.confirm_discard = False
                    st.rerun()
        else:
            if st.button("✅ Session beenden & speichern", type="primary", use_container_width=True):
                db.close_session(session_id)
                _reset_kiosk_state()
                st.rerun()

            if st.button("🗑️ Session verwerfen (alle Stimmen löschen)", use_container_width=True):
                st.session_state.confirm_discard = True
                st.rerun()


def _reset_kiosk_state():
    """Setzt alle Kiosk-relevanten Session-State-Variablen zurück."""
    for key in ["kiosk_active", "kiosk_session_id", "kiosk_phase", "kiosk_class_name", "show_popup", "popup_type", "confirm_discard"]:
        if key in st.session_state:
            del st.session_state[key]
