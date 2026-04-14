# Letztes Update: Popup Bugfix und Audio Anpassung
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import plotly.graph_objects as go
import wave
import struct
import math
import base64
import io
import uuid


@st.cache_data
def get_beep_audio_base64():
    """Generates a soft success beep WAV file and returns its base64 string."""
    buffer = io.BytesIO()

    nchannels = 1
    sampwidth = 2
    framerate = 44100
    nframes = int(framerate * 0.4)  # 0.4 seconds long
    comptype = "NONE"
    compname = "not compressed"

    with wave.open(buffer, "w") as wav_file:
        wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))

        freq1 = 1046.50  # C6
        freq2 = 1318.51  # E6

        for i in range(nframes):
            env = 1.0 - (i / nframes)  # Fade out envelope
            t = float(i) / framerate
            value = math.sin(2.0 * math.pi * freq1 * t) + math.sin(2.0 * math.pi * freq2 * t)
            value = value / 2.0

            volume = 16000 * env
            sample = int(value * volume)

            wav_file.writeframes(struct.pack("<h", sample))

    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def show_kiosk_active(phase, save_session_callback):
    """Die aktive Kiosk-Ansicht für das Tablet der Kinder (ohne Navigation)."""
    if "show_popup" not in st.session_state:
        st.session_state.show_popup = False
    if "popup_type" not in st.session_state:
        st.session_state.popup_type = ""

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
            st.session_state.show_popup = True
            st.session_state.popup_type = "Gut"

    with col2:
        if st.button("😐"):
            st.session_state.session_votes["Mittel"] += 1
            st.session_state.show_popup = True
            st.session_state.popup_type = "Mittel"

    with col3:
        if st.button("☹️"):
            st.session_state.session_votes["Schlecht"] += 1
            st.session_state.show_popup = True
            st.session_state.popup_type = "Schlecht"

    if st.session_state.show_popup:
        st.session_state.show_popup = False

        if st.session_state.popup_type == "Gut":
            emoji = "😃"
            color = "#2ecc71"
            bg_color = "#eafaf1"
        elif st.session_state.popup_type == "Mittel":
            emoji = "😐"
            color = "#f39c12"
            bg_color = "#fef5e7"
        else:
            emoji = "☹️"
            color = "#e74c3c"
            bg_color = "#fdedec"

        b64_audio = get_beep_audio_base64()
        unique_id = uuid.uuid4().hex

        popup_html = f"""
        <style>
        .custom-overlay-{unique_id} {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.6);
            z-index: 99998;
            animation: fadeOutOverlay-{unique_id} 2.5s forwards;
            pointer-events: none;
        }}
        .custom-popup-{unique_id} {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: {bg_color};
            padding: 50px 80px;
            border-radius: 30px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            z-index: 99999;
            text-align: center;
            border: 8px solid {color};
            animation: fadeOutPopup-{unique_id} 2.5s forwards;
            pointer-events: none;
        }}
        .custom-popup-{unique_id} h1 {{
            font-size: 150px;
            margin: 0;
            padding: 0;
            line-height: 1.2;
        }}
        .custom-popup-{unique_id} p {{
            font-size: 45px;
            color: #333;
            margin-top: 15px;
            font-family: sans-serif;
            font-weight: bold;
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

        # Audio separat einbinden über components.html
        audio_js = f"""
        <script>
            // unique id {unique_id}
            var audio = new Audio("data:audio/wav;base64,{b64_audio}");
            audio.play().catch(function(e) {{
                console.log("Audio autoplay wurde vom Browser blockiert:", e);
            }});
        </script>
        """
        components.html(audio_js, height=0)

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
