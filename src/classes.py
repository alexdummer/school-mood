"""
Klassen-Verwaltungs-UI für den Admin-Bereich.
Ermöglicht das Anlegen, Einsehen und Löschen von Klassen.
"""

import streamlit as st
import src.db as db


def show_class_manager():
    """Zeigt die Klassenverwaltung und den Kiosk-Starter für eine gewählte Klasse."""
    st.title("🏫 Klassen verwalten")

    classes = db.get_classes()
    active_sessions = {s["class_name"]: s for s in db.get_active_sessions()}

    # ── Neue Klasse anlegen ───────────────────────────────────────────────────
    with st.expander("➕ Neue Klasse anlegen", expanded=len(classes) == 0):
        with st.form("new_class_form"):
            col_input, col_btn = st.columns([3, 1])
            with col_input:
                new_name = st.text_input(
                    "Klassenname",
                    placeholder="z.B. 5a, Klasse 3b, ...",
                    label_visibility="collapsed",
                )
            with col_btn:
                submitted = st.form_submit_button("✅ Anlegen", use_container_width=True, type="primary")

            if submitted:
                if not new_name.strip():
                    st.error("Bitte einen Klassenname eingeben.")
                elif any(c["name"] == new_name.strip() for c in classes):
                    st.warning(f"Die Klasse '{new_name.strip()}' existiert bereits.")
                else:
                    db.create_class(new_name)
                    st.success(f"Klasse '{new_name.strip()}' wurde angelegt!")
                    st.rerun()

    st.markdown("---")

    # ── Klassen-Übersicht ─────────────────────────────────────────────────────
    if not classes:
        st.info("Noch keine Klassen angelegt. Lege oben deine erste Klasse an.")
        return

    st.subheader("📋 Deine Klassen")

    for cls in classes:
        is_active = cls["name"] in active_sessions
        active_session = active_sessions.get(cls["name"])

        # Bordered card via HTML (st.container(border=True) erfordert Streamlit >= 1.30)
        st.markdown(
            "<div style='border:1px solid #dee2e6; border-radius:8px; " "padding:12px 16px; margin-bottom:12px;'>",
            unsafe_allow_html=True,
        )
        col_name, col_status, col_actions = st.columns([3, 2, 3])

        with col_name:
            st.markdown(f"### 🏷️ {cls['name']}")

        with col_status:
            if is_active:
                sess = active_session
                st.markdown(
                    f"<div style='background:#d4edda; border:1px solid #28a745;"
                    f"border-radius:8px; padding:8px 12px; margin-top:8px;'>"
                    f"<b style='color:#155724;'>🟢 Session aktiv</b><br>"
                    f"<small style='color:#155724;'>{sess['phase']}<br>"
                    f"{sess['total_votes']} Stimmen bisher</small></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='background:#f8f9fa; border:1px solid #dee2e6;"
                    "border-radius:8px; padding:8px 12px; margin-top:8px;'>"
                    "<b style='color:#6c757d;'>⚪ Keine aktive Session</b></div>",
                    unsafe_allow_html=True,
                )

        with col_actions:
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            if not is_active:
                phase = st.selectbox(
                    "Phase",
                    ["Ankunft in der Schule", "Nach Hause gehen"],
                    key=f"phase_{cls['id']}",
                    label_visibility="collapsed",
                )

                if st.button(
                    "▶️ Kiosk starten",
                    key=f"start_{cls['id']}",
                    use_container_width=True,
                    type="primary",
                ):
                    session_id = db.open_session(
                        class_id=cls["id"],
                        phase=phase,
                    )
                    st.session_state.kiosk_active = True
                    st.session_state.kiosk_session_id = session_id
                    st.session_state.kiosk_phase = phase
                    st.session_state.kiosk_class_name = cls["name"]
                    st.rerun()

                if st.button(
                    "🗑️ Löschen",
                    key=f"del_{cls['id']}",
                    use_container_width=True,
                ):
                    db.delete_class(cls["id"])
                    st.success(f"Klasse '{cls['name']}' wurde gelöscht.")
                    st.rerun()
            else:
                st.info("Kiosk läuft auf diesem oder einem anderen Gerät.")
                if st.button(
                    "📲 Session übernehmen",
                    key=f"takeover_{cls['id']}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state.kiosk_active = True
                    st.session_state.kiosk_session_id = active_session["id"]
                    st.session_state.kiosk_phase = active_session["phase"]
                    st.session_state.kiosk_class_name = cls["name"]
                    st.rerun()

                if st.button(
                    "⏹️ Session beenden",
                    key=f"stop_{cls['id']}",
                    use_container_width=True,
                ):
                    db.close_session(active_session["id"])
                    st.success(f"Session für '{cls['name']}' wurde beendet.")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
