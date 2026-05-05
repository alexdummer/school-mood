"""
Klassen-Verwaltungs-UI für den Admin-Bereich.
Ermöglicht das Anlegen, Einsehen und Löschen von Klassen.
"""

import streamlit as st
from src.db import create_class, get_classes, delete_class, get_active_sessions, open_session


def show_class_manager():
    """Zeigt die Klassenverwaltung und den Kiosk-Starter für eine gewählte Klasse."""
    st.title("🏫 Klassen verwalten")

    classes = get_classes()
    active_sessions = {s["class_name"]: s for s in get_active_sessions()}

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
                    create_class(new_name)
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

        with st.container(border=True):
            col_name, col_status, col_actions = st.columns([3, 2, 3])

            with col_name:
                st.markdown(f"### 🏷️ {cls['name']}")

            with col_status:
                if is_active:
                    sess = active_session
                    st.markdown(
                        f"""
                        <div style='background:#d4edda; border:1px solid #28a745;
                             border-radius:8px; padding:8px 12px; margin-top:8px;'>
                            <b style='color:#155724;'>🟢 Session aktiv</b><br>
                            <small style='color:#155724;'>{sess['phase']}<br>
                            {sess['total_votes']} Stimmen bisher</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div style='background:#f8f9fa; border:1px solid #dee2e6;
                             border-radius:8px; padding:8px 12px; margin-top:8px;'>
                            <b style='color:#6c757d;'>⚪ Keine aktive Session</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with col_actions:
                st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
                if not is_active:
                    if st.button(
                        "▶️ Kiosk starten",
                        key=f"start_{cls['id']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        st.session_state["kiosk_pending_class_id"] = cls["id"]
                        st.session_state["kiosk_pending_class_name"] = cls["name"]
                        st.rerun()

                    if st.button(
                        "🗑️ Löschen",
                        key=f"del_{cls['id']}",
                        use_container_width=True,
                    ):
                        delete_class(cls["id"])
                        st.success(f"Klasse '{cls['name']}' wurde gelöscht.")
                        st.rerun()
                else:
                    st.info("Kiosk läuft auf diesem oder einem anderen Gerät.")

    # ── Kiosk-Start Dialog ────────────────────────────────────────────────────
    if "kiosk_pending_class_id" in st.session_state:
        st.markdown("---")
        cls_name = st.session_state.get("kiosk_pending_class_name", "")
        st.subheader(f"⚙️ Kiosk-Session für Klasse **{cls_name}** starten")

        phase = st.radio(
            "Phase für diese Session:",
            ["Ankunft in der Schule", "Nach Hause gehen"],
            key="kiosk_pending_phase",
            horizontal=True,
        )

        col_go, col_cancel = st.columns(2)
        with col_go:
            if st.button("▶️ Session starten & Kiosk aktivieren", type="primary", use_container_width=True):
                session_id = open_session(
                    class_id=st.session_state["kiosk_pending_class_id"],
                    phase=phase,
                )
                st.session_state.kiosk_active = True
                st.session_state.kiosk_session_id = session_id
                st.session_state.kiosk_phase = phase
                st.session_state.kiosk_class_name = cls_name
                # Aufräumen
                del st.session_state["kiosk_pending_class_id"]
                del st.session_state["kiosk_pending_class_name"]
                st.rerun()

        with col_cancel:
            if st.button("Abbrechen", use_container_width=True):
                del st.session_state["kiosk_pending_class_id"]
                del st.session_state["kiosk_pending_class_name"]
                st.rerun()
