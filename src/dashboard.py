"""
Dashboard-Modul: Gesamtauswertung und klassenweise Analyse.
Kombiniert neue Einzelstimmen-Daten mit alten session_logs.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import src.db as db


def draw_dashboard():
    """Zeichnet das vollständige Dashboard mit Tabs für Gesamt- und Klassenansicht."""
    # Daten laden
    votes_df = db.get_new_votes_df()  # Einzelstimmen (neues System)
    sessions_df = db.get_aggregated_sessions_df()  # Aggregiert nach Session
    legacy_df = db.get_legacy_df()  # Alte session_logs

    has_new_data = not votes_df.empty
    has_legacy = not legacy_df.empty

    if not has_new_data and not has_legacy:
        st.warning("📭 Noch keine Daten vorhanden. Starte eine Kiosk-Session, um Daten zu erfassen.")
        return

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_gesamt, tab_klassen, tab_legacy = st.tabs(["🌍 Gesamtansicht", "🏫 Klassenweise", "📂 Alte Daten"])

    with tab_gesamt:
        _draw_gesamtansicht(votes_df, legacy_df, sessions_df)

    with tab_klassen:
        _draw_klassenansicht(votes_df, sessions_df)

    with tab_legacy:
        _draw_legacy_view(legacy_df)


# ---------------------------------------------------------------------------
# Tab 1: Gesamtansicht
# ---------------------------------------------------------------------------


def _draw_gesamtansicht(votes_df, legacy_df, sessions_df):
    st.subheader("🌍 Gesamtauswertung (alle Klassen)")

    # Kombinierte Gesamtzahlen aus neuen Votes
    if not votes_df.empty:
        gut_neu = int((votes_df["vote"] == "Gut").sum())
        mittel_neu = int((votes_df["vote"] == "Mittel").sum())
        schlecht_neu = int((votes_df["vote"] == "Schlecht").sum())
    else:
        gut_neu = mittel_neu = schlecht_neu = 0

    # Legacy-Summen dazurechnen
    if not legacy_df.empty:
        gut_alt = int(legacy_df["gut_count"].sum())
        mittel_alt = int(legacy_df["mittel_count"].sum())
        schlecht_alt = int(legacy_df["schlecht_count"].sum())
    else:
        gut_alt = mittel_alt = schlecht_alt = 0

    gut_total = gut_neu + gut_alt
    mittel_total = mittel_neu + mittel_alt
    schlecht_total = schlecht_neu + schlecht_alt
    total_votes = gut_total + mittel_total + schlecht_total

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown("### 📈 Kennzahlen")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Gesamt Stimmen", total_votes)

    pct_gut = round((gut_total / total_votes) * 100, 1) if total_votes > 0 else 0
    pct_schlecht = round((schlecht_total / total_votes) * 100, 1) if total_votes > 0 else 0
    kpi2.metric("Anteil 'Gut' 😃", f"{pct_gut}%")
    kpi3.metric("Anteil 'Schlecht' ☹️", f"{pct_schlecht}%")
    kpi4.metric("Sessions gesamt", len(sessions_df) + len(legacy_df) if not legacy_df.empty else len(sessions_df))

    st.markdown("---")

    # ── Tortendiagramm Gesamt ─────────────────────────────────────────────────
    col_pie, col_filter = st.columns([2, 1])
    with col_pie:
        st.subheader("Stimmungsverteilung gesamt")
        if total_votes > 0:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Gut", "Mittel", "Schlecht"],
                        values=[gut_total, mittel_total, schlecht_total],
                        marker=dict(colors=["#2ecc71", "#f39c12", "#e74c3c"]),
                        hole=0.4,
                        textinfo="label+percent+value",
                    )
                ]
            )
            fig.update_layout(margin=dict(t=10, b=10), height=350)
            st.plotly_chart(fig, use_container_width=True)

    # ── Zeitlicher Verlauf (nur neue Daten mit Datum) ─────────────────────────
    if not votes_df.empty and "date" in votes_df.columns:
        st.markdown("---")
        st.subheader("📅 Verlauf über Zeit")

        # Datum-Filter
        min_d = votes_df["date"].min()
        max_d = votes_df["date"].max()
        if min_d != max_d:
            date_range = st.date_input(
                "Zeitraum filtern",
                [min_d, max_d],
                key="gesamt_date_filter",
            )
            if len(date_range) == 2:
                filtered = votes_df[(votes_df["date"] >= date_range[0]) & (votes_df["date"] <= date_range[1])]
            else:
                filtered = votes_df
        else:
            filtered = votes_df

        if not filtered.empty:
            daily = filtered.groupby(["date", "vote"]).size().reset_index(name="count")
            fig_line = px.bar(
                daily,
                x="date",
                y="count",
                color="vote",
                color_discrete_map={"Gut": "#2ecc71", "Mittel": "#f39c12", "Schlecht": "#e74c3c"},
                barmode="stack",
                labels={"date": "Datum", "count": "Stimmen", "vote": "Stimmung"},
            )
            fig_line.update_layout(margin=dict(t=10, b=10), height=300)
            st.plotly_chart(fig_line, use_container_width=True)

    # ── Phase-Vergleich ───────────────────────────────────────────────────────
    if not votes_df.empty and "phase" in votes_df.columns:
        st.markdown("---")
        st.subheader("🕐 Vergleich: Ankunft vs. Abgang")

        phase_counts = votes_df.groupby(["phase", "vote"]).size().reset_index(name="count")
        if not phase_counts.empty:
            fig_phase = px.bar(
                phase_counts,
                x="phase",
                y="count",
                color="vote",
                color_discrete_map={"Gut": "#2ecc71", "Mittel": "#f39c12", "Schlecht": "#e74c3c"},
                barmode="group",
                labels={"phase": "Phase", "count": "Stimmen", "vote": "Stimmung"},
            )
            fig_phase.update_layout(margin=dict(t=10, b=10), height=300)
            st.plotly_chart(fig_phase, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 2: Klassenweise
# ---------------------------------------------------------------------------


def _draw_klassenansicht(votes_df, sessions_df):
    st.subheader("🏫 Auswertung nach Klasse")

    if votes_df.empty:
        st.info("Noch keine Daten aus dem neuen Klassen-System vorhanden.")
        return

    # Filter
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        available_classes = sorted(votes_df["class_name"].dropna().unique())
        selected_classes = st.multiselect(
            "Klassen wählen",
            available_classes,
            default=available_classes,
            key="klassen_filter",
        )
    with col_f2:
        available_phases = sorted(votes_df["phase"].dropna().unique())
        selected_phases = st.multiselect(
            "Phase wählen",
            available_phases,
            default=available_phases,
            key="phase_filter",
        )

    mask = votes_df["class_name"].isin(selected_classes) & votes_df["phase"].isin(selected_phases)
    filtered = votes_df[mask]

    if filtered.empty:
        st.warning("Keine Daten für die gewählten Filter.")
        return

    # ── Vergleichsdiagramm: alle Klassen nebeneinander ────────────────────────
    st.markdown("---")
    st.subheader("📊 Stimmungsverteilung je Klasse")

    class_summary = filtered.groupby(["class_name", "vote"]).size().reset_index(name="count")

    fig_class = px.bar(
        class_summary,
        x="class_name",
        y="count",
        color="vote",
        color_discrete_map={"Gut": "#2ecc71", "Mittel": "#f39c12", "Schlecht": "#e74c3c"},
        barmode="group",
        labels={"class_name": "Klasse", "count": "Stimmen", "vote": "Stimmung"},
    )
    fig_class.update_layout(margin=dict(t=10, b=10), height=350)
    st.plotly_chart(fig_class, use_container_width=True)

    # ── Einzelne Klassen-Karten ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔍 Details pro Klasse")

    # In Spalten zu je 2 aufteilen
    classes_to_show = filtered["class_name"].unique()
    cols_per_row = 2

    for i in range(0, len(classes_to_show), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, cls in enumerate(classes_to_show[i : i + cols_per_row]):
            cls_data = filtered[filtered["class_name"] == cls]
            gut = int((cls_data["vote"] == "Gut").sum())
            mittel = int((cls_data["vote"] == "Mittel").sum())
            schlecht = int((cls_data["vote"] == "Schlecht").sum())
            total = gut + mittel + schlecht

            with cols[j]:
                with st.container(border=True):
                    st.markdown(f"**🏷️ {cls}** – {total} Stimmen")
                    if total > 0:
                        fig_mini = go.Figure(
                            data=[
                                go.Pie(
                                    labels=["Gut", "Mittel", "Schlecht"],
                                    values=[gut, mittel, schlecht],
                                    marker=dict(colors=["#2ecc71", "#f39c12", "#e74c3c"]),
                                    hole=0.5,
                                    textinfo="percent",
                                    showlegend=False,
                                )
                            ]
                        )
                        fig_mini.update_layout(
                            margin=dict(t=5, b=5, l=5, r=5),
                            height=200,
                        )
                        st.plotly_chart(fig_mini, use_container_width=True)
                        col_g, col_m, col_s = st.columns(3)
                        col_g.metric("😃", gut)
                        col_m.metric("😐", mittel)
                        col_s.metric("☹️", schlecht)

    # ── Session-Verlauf pro Klasse ─────────────────────────────────────────────
    if not sessions_df.empty and "class_name" in sessions_df.columns:
        st.markdown("---")
        st.subheader("📋 Session-Verlauf")

        sess_filtered = sessions_df[sessions_df["class_name"].isin(selected_classes)]
        if not sess_filtered.empty:
            display_cols = ["class_name", "phase", "started_at", "gut_count", "mittel_count", "schlecht_count", "total_votes"]
            available = [c for c in display_cols if c in sess_filtered.columns]
            st.dataframe(
                sess_filtered[available].rename(
                    columns={
                        "class_name": "Klasse",
                        "phase": "Phase",
                        "started_at": "Gestartet",
                        "gut_count": "😃 Gut",
                        "mittel_count": "😐 Mittel",
                        "schlecht_count": "☹️ Schlecht",
                        "total_votes": "Gesamt",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


# ---------------------------------------------------------------------------
# Tab 3: Alte Daten (Legacy)
# ---------------------------------------------------------------------------


def _draw_legacy_view(legacy_df):
    st.subheader("📂 Alte Daten (vor Klassenstruktur)")

    if legacy_df.empty:
        st.info("Keine alten Session-Logs vorhanden.")
        return

    st.info(
        "Diese Daten stammen aus der alten Version der App (ohne Klassenstruktur). "
        "Sie werden separat angezeigt und fließen in die Gesamtstatistik ein."
    )

    gut_total = int(legacy_df["gut_count"].sum())
    mittel_total = int(legacy_df["mittel_count"].sum())
    schlecht_total = int(legacy_df["schlecht_count"].sum())
    total = gut_total + mittel_total + schlecht_total

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Gesamt Stimmen (alt)", total)
    kpi2.metric("Sessions (alt)", len(legacy_df))
    kpi3.metric("Anteil 'Gut'", f"{round(gut_total/total*100, 1)}%" if total > 0 else "—")

    if total > 0:
        col_pie, _ = st.columns([2, 1])
        with col_pie:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Gut", "Mittel", "Schlecht"],
                        values=[gut_total, mittel_total, schlecht_total],
                        marker=dict(colors=["#2ecc71", "#f39c12", "#e74c3c"]),
                        hole=0.4,
                    )
                ]
            )
            fig.update_layout(margin=dict(t=10, b=10), height=300)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    with st.expander("📋 Rohdaten (alte Session-Logs)"):
        st.dataframe(
            legacy_df[["id", "timestamp", "phase", "gut_count", "mittel_count", "schlecht_count"]].rename(
                columns={
                    "id": "ID",
                    "timestamp": "Zeitpunkt",
                    "phase": "Phase",
                    "gut_count": "😃 Gut",
                    "mittel_count": "😐 Mittel",
                    "schlecht_count": "☹️ Schlecht",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
