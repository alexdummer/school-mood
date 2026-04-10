import streamlit as st


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
