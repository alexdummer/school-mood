import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def show_kiosk_active(phase, save_session_callback):
    """Die aktive Kiosk-Ansicht für das Tablet der Kinder (ohne Navigation)."""
    st.markdown("<h1 style='text-align: center;'>Wie geht es dir heute?</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>{phase}</h3>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(
        """
    <style>
    /* Größenanpassung: Streamlit verpackt Text in <p> Tags in Buttons */
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
        font-size: 100px !important;
        line-height: 1 !important;
        margin: 0 !important;
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
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("😃"):
            st.session_state.session_votes["Gut"] += 1
            st.toast("Danke! Deine Stimmung wurde gespeichert.", icon="😃")

    with col2:
        if st.button("😐"):
            st.session_state.session_votes["Mittel"] += 1
            st.toast("Danke! Deine Stimmung wurde gespeichert.", icon="😐")

    with col3:
        if st.button("☹️"):
            st.session_state.session_votes["Schlecht"] += 1
            st.toast("Danke! Deine Stimmung wurde gespeichert.", icon="☹️")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Schüler-Dashboard Live Ansicht ---
    st.markdown("### 📊 Aktuelle Stimmung:")
    st.info("So haben wir in dieser Session bisher abgestimmt:")

    live_df = pd.DataFrame(
        {
            "Stimmung": ["Gut", "Mittel", "Schlecht"],
            "Stimmen": [st.session_state.session_votes["Gut"], st.session_state.session_votes["Mittel"], st.session_state.session_votes["Schlecht"]],
        }
    )

    total_live = live_df["Stimmen"].sum()
    if total_live > 0:
        labels = ["Gut", "Mittel", "Schlecht"]
        values = [st.session_state.session_votes["Gut"], st.session_state.session_votes["Mittel"], st.session_state.session_votes["Schlecht"]]
        colors = ["#2ecc71", "#f39c12", "#e74c3c"]

        fig_live = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=0.4)])
        fig_live.update_layout(height=300)
        st.plotly_chart(fig_live, use_container_width=True)
    else:
        st.write("*Noch keine Stimmen abgegeben.*")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Versteckter Beenden-Button für die Lehrkraft
    with st.expander("Lehrkraft-Bereich"):
        # Vorschau der Stimmen
        st.write("Bisherige Stimmen (werden beim Beenden gespeichert):")
        st.write(
            f"😃 {st.session_state.session_votes['Gut']} |"
            + f" 😐 {st.session_state.session_votes['Mittel']} |"
            + f" ☹️ {st.session_state.session_votes['Schlecht']}"
        )
        if st.button("❌ Session beenden"):
            # Speichere die aggregierten Daten in die Datenbank über die übergebene Callback-Funktion
            save_session_callback(
                phase=phase,
                gut_count=st.session_state.session_votes["Gut"],
                mittel_count=st.session_state.session_votes["Mittel"],
                schlecht_count=st.session_state.session_votes["Schlecht"],
                timestamp=st.session_state.session_start,
            )
            # Aufräumen
            st.session_state.kiosk_active = False
            del st.session_state.session_votes
            del st.session_state.session_start
            st.rerun()
