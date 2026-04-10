# Deployment auf Streamlit Community Cloud (Mit Datenbank)

Die Streamlit Community Cloud ist großartig, um Apps kostenlos zu hosten. Allerdings werden Container bei Inaktivität regelmäßig neu gestartet. **Dabei wird die lokale SQLite-Datenbank (`stimmung_*.db`) gelöscht.**

Damit deine gesammelten Kiosk-Daten erhalten bleiben, habe ich dir die Datei `app_cloud.py` vorbereitet. Sie nutzt **PostgreSQL** als echte Cloud-Datenbank.

## Schritt-für-Schritt Anleitung

### 1. Eine kostenlose PostgreSQL Datenbank erstellen
Die einfachste Möglichkeit für Streamlit ist **Supabase** oder **Neon**.
1. Gehe zu [Supabase](https://supabase.com/) und erstelle ein kostenloses Konto.
2. Erstelle ein neues Projekt.
3. Gehe im Dashboard auf **Project Settings -> Database** und kopiere dir die *Connection String* (URI). Sie sieht ungefähr so aus:
   `postgresql://postgres:[DEIN-PASSWORT]@db.xxxx.supabase.co:5432/postgres`

### 2. GitHub vorbereiten
Lade folgende Dateien in dein GitHub-Repository hoch:
* `app_cloud.py`
* Deine `.streamlit/secrets.toml` lädst du **NICHT** hoch!
* Erstelle eine Datei namens `requirements.txt` und füge Folgendes ein:
```txt
streamlit
pandas
plotly
SQLAlchemy
psycopg2-binary
```

### 3. Streamlit Cloud einrichten
1. Gehe auf [share.streamlit.io](https://share.streamlit.io/) und klicke auf "New App".
2. Wähle dein Repository aus.
3. **Wichtig:** Trage als *Main file path* `app_cloud.py` ein (nicht app.py!).
4. Klicke auf **Advanced settings...** und füge unter *Secrets* folgendes ein:

```toml
[passwords]
test = "admin"
meineschule = "schlauespasswort"
# ... weitere Schulen ...

[connections.postgresql]
dialect = "postgresql"
host = "db.xxxx.supabase.co"
port = "5432"
database = "postgres"
username = "postgres"
password = "DeinSupabasePasswort"
```

**(Tipp: Ersetze die Werte bei `connections.postgresql` mit den Daten aus deiner Supabase-Verbindung!)**

5. Klicke auf **Deploy!**

Das war's! Deine App läuft nun sicher in der Cloud, und das Beenden einer Kiosk-Session speichert die Daten verlässlich in deiner Supabase-Datenbank.
