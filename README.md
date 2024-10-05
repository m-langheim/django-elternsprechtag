# EduConnect

## Projektübersicht

**EduConnect** ist eine moderne Plattform, die Eltern ermöglicht, Termine für Elternsprechtage bei Lehrern zu buchen und Anfragen von Lehrern zur Terminbuchung zu empfangen. Durch eine intuitive Benutzeroberfläche fördert das System eine einfache und effiziente Kommunikation zwischen Eltern und Lehrern.  
Zukünftige Funktionen von **EduConnect** werden die Erfassung von Fehlstunden sowie die Möglichkeit zur Krankschreibung oder Entschuldigung umfassen, um die schulische Verwaltung weiter zu vereinfachen. Weitere Erweiterungen sind ebenfalls geplant, um die Interaktion zwischen Lehrern, Eltern und Schülern noch umfassender zu gestalten.

---

## Installation (Entwicklung)

**Voraussetzungen:**
- **Python** 3.10 oder höher
- **Django** Framework
- **Redis-Server** für asynchrone Aufgaben
- Virtuelle Umgebung für Python wird empfohlen

**Installationsschritte:**

1. **Klonen des Projekts:**
   Klonen Sie das Repository in Ihr lokales Verzeichnis:
   ```bash
   git clone https://github.com/USERNAME/EduConnect.git
   cd EduConnect
   ```

2. **Virtuelle Umgebung erstellen und aktivieren:**
   Es wird empfohlen, eine virtuelle Umgebung zu erstellen, um Abhängigkeiten zu isolieren:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Für macOS/Linux
   venv\Scripts\activate      # Für Windows
   ```

3. **Installieren der Abhängigkeiten:**
   Für die Entwicklungsumgebung müssen Sie die Abhängigkeiten aus der `requirements_development.txt` Datei installieren:
   ```bash
   pip install -r requirements_development.txt
   ```

4. **Redis-Server installieren und starten:**
   **Redis** wird für asynchrone Aufgaben benötigt. Installieren Sie Redis und starten Sie den Server:
   - **macOS/Linux**: 
      ```bash
      sudo apt install redis-server
      sudo systemctl start redis
      ```
   - **Windows**: Laden Sie Redis von der [offiziellen Seite](https://redis.io/download) herunter und installieren Sie es entsprechend.

5. **Konfiguration für Entwicklungsumgebung:**
   In der Datei `elternsprechtag/celery.py` muss die Umgebungsvariable auf die Entwicklungsumgebung gesetzt werden. Ändern Sie folgende Zeile:
   ```python
   os.environ.setdefault(
       "DJANGO_SETTINGS_MODULE", "elternsprechtag.settings.production"
   )
   ```
   zu:
   ```python
   os.environ.setdefault(
       "DJANGO_SETTINGS_MODULE", "elternsprechtag.settings.development"
   )
   ```

6. **Datenbank migrieren (Entwicklungsumgebung):**
   Führen Sie den folgenden Befehl aus, um die Datenbankstruktur zu erstellen:
   ```bash
   python development.py migrate
   ```

7. **Entwicklungsumgebung starten:**
   Starten Sie den Entwicklungsserver mit:
   ```bash
   python development.py runserver
   ```

---

## Installation (Produktion)

**Voraussetzungen:**
- **Docker** und **Docker Compose**

**Installationsschritte:**

1. **Docker und Docker Compose installieren:**
   Befolgen Sie die Anweisungen auf [Docker's offizieller Website](https://docs.docker.com/get-docker/).

2. **`docker-compose.yaml` herunterladen:**
   Laden Sie die Datei `docker-compose.yaml` aus dem Repository herunter.

3. **Konfiguration anpassen:**
   Nehmen Sie die erforderlichen Anpassungen in der `docker-compose.yaml` vor.

4. **Container starten:**
   Führen Sie den folgenden Befehl aus, um die Container zu starten:
   ```bash
   docker-compose up
   ```

---

## **Verwendung**

**EduConnect** ermöglicht Eltern, Termine für Elternsprechtage bei Lehrern zu buchen und Anfragen von Lehrern zu empfangen. Hier ist ein typischer Workflow:

1. **Anmeldung**: 
   - Eltern und Lehrer melden sich über die bereitgestellte Benutzeroberfläche an.
   
2. **Termine buchen**:
   - Eltern können verfügbare Termine einsehen und einen geeigneten Slot für ein Gespräch mit einem Lehrer auswählen.
   - Die ausgewählten Termine werden in der Anwendung angezeigt.

3. **Anfragen von Lehrern**:
   - Lehrer können Anfragen zur Buchung von Terminen senden, die Eltern dann bestätigen oder ablehnen können.

4. **Benachrichtigungen**:
   - Sowohl Eltern als auch Lehrer erhalten Benachrichtigungen über Buchungen und Änderungen an Terminen.

---

## **Tests**

Aktuell sind die Tests nicht vollständig implementiert. Um die vorhandenen Tests auszuführen, nutzen Sie den folgenden Befehl:
```bash
python manage.py test --settings=elternsprechtag.settings.test
```

---
