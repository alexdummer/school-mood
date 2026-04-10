import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def draw_dashboard(df):
    """Zeichnet die Filter, KPIs und Diagramme für das Admin Dashboard. Gibt das gefilterte DataFrame zurück."""
    if df.empty:
        st.warning("Noch keine Daten vorhanden.")
        return None

    # Filter-Optionen in der Sidebar (oder oben)
    st.subheader("Filter")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if "phase" in df.columns:
            selected_phase = st.multiselect("Phase wählen", df["phase"].dropna().unique(), default=df["phase"].dropna().unique())
        else:
            selected_phase = []
    with col_f2:
        # Datumsbereich
        if "date" in df.columns:
            min_date = df["date"].min()
            max_date = df["date"].max()
            if pd.isna(min_date) or pd.isna(max_date):
                date_range = []
            else:
                date_range = st.date_input("Zeitraum", [min_date, max_date])
        else:
            date_range = []

    # Daten filtern
    if "phase" in df.columns:
        mask = df["phase"].isin(selected_phase)
    else:
        mask = pd.Series([True] * len(df))

    # Einfache Datumsfilter-Logik (falls range gewählt wurde)
    if len(date_range) == 2 and "date" in df.columns:
        mask = mask & (df["date"] >= date_range[0]) & (df["date"] <= date_range[1])

    filtered_df = df[mask].copy()

    # KPIs
    st.markdown("### Übersicht")
    kpi1, kpi2, kpi3 = st.columns(3)

    if len(filtered_df) > 0:
        gut_total = int(filtered_df["gut_count"].sum())
        mittel_total = int(filtered_df["mittel_count"].sum())
        schlecht_total = int(filtered_df["schlecht_count"].sum())
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

    # Eigene Farben definieren
    color_map = {"Gut": "#2ecc71", "Mittel": "#f1c40f", "Schlecht": "#e74c3c"}

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Verteilung der Stimmung")
        if total_votes > 0:
            labels = ["Gut", "Mittel", "Schlecht"]
            values = [gut_total, mittel_total, schlecht_total]
            colors = ["#2ecc71", "#f1c40f", "#e74c3c"]

            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=0.4)])
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Noch keine Stimmabgaben vorhanden.")

    # 2. Verlauf über die Zeit (Balkendiagramm gestapelt nach Datum)
    with c2:
        st.subheader("Verlauf über Tage")
        if not filtered_df.empty and total_votes > 0:
            daily_mood = filtered_df.groupby("date")[["gut_count", "mittel_count", "schlecht_count"]].sum().reset_index()
            daily_mood_melted = daily_mood.melt(
                id_vars="date", value_vars=["gut_count", "mittel_count", "schlecht_count"], var_name="mood", value_name="Anzahl"
            )
            daily_mood_melted["mood"] = daily_mood_melted["mood"].map({"gut_count": "Gut", "mittel_count": "Mittel", "schlecht_count": "Schlecht"})
            # Datum in String umwandeln für bessere Plotly Kompatibilität auf der X-Achse
            daily_mood_melted["date"] = daily_mood_melted["date"].astype(str)

            fig_bar = px.bar(daily_mood_melted, x="date", y="Anzahl", color="mood", color_discrete_map=color_map, barmode="group")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Noch keine Stimmabgaben vorhanden.")

    # 3. Tageszeit-Trend (Wann wird abgestimmt?)
    st.markdown("---")
    st.subheader("Aktivität nach Uhrzeit")
    if not filtered_df.empty:
        # Summiere alle Stimmen pro Stunde
        hourly_counts = (
            filtered_df.groupby("hour")[["gut_count", "mittel_count", "schlecht_count"]].sum().sum(axis=1).reset_index(name="Anzahl Stimmen")
        )
        fig_line = px.line(hourly_counts, x="hour", y="Anzahl Stimmen", markers=True)
        st.plotly_chart(fig_line)
    else:
        st.info("Keine Daten für Tageszeit-Trend")

    return filtered_df
