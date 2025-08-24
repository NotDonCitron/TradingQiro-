# Signal Forwarder - Dokumentation

## Übersicht

Das **Signal Forwarder System** überwacht automatisch die Telegram-Gruppe `-2299206473` und leitet erkannte Signale an Ihre eigene Gruppe `-1002773853382` weiter.

## Funktionsweise

### 1. Signal-Erkennung

Das System erkennt automatisch Signale im folgenden Format:

```bash
🟢 Long
Name: API3/USDT
Margin mode: Cross (25.0X)

↪️ Entry price(USDT):
1.4619

Targets(USDT):
1) 1.4765
2) 1.4911
3) 1.5058
4) 1.5204
5) 🔝 unlimited
```

### 2. Signal-Verarbeitung
- **Parsing**: Extrahiert Symbol, Direction, Leverage, Entry Price und Targets
- **Formatierung**: Konvertiert in übersichtliches Format mit Emojis
- **Weiterleitung**: Sendet automatisch an Ihre Telegram-Gruppe

### 3. Signal-Ausgabe ohne automatisches "unlimited"

```bash
🟢 Long
Name: API3/USDT
Margin mode: Cross (25X)

↪️ Entry price(USDT):
1.4619

Targets(USDT):
1) 1.4765
2) 1.4911
3) 1.5058
4) 1.5204
```

**Wichtige Eigenschaften:**
- ✅ Nur echte Targets werden weitergeleitet
- ✅ Kein automatisches "5) 🔝 unlimited" hinzugefügt
- ✅ "unlimited" aus Originalsignalen wird herausgefiltert
- ✅ Saubere, präzise Target-Liste
- ✅ Cornix-kompatibles Format
- ✅ Keine zusätzlichen oder künstlichen Targets

## Konfiguration

### Environment Variables (.env)

```bash
OWN_GROUP_CHAT_ID=-1002773853382        # Ihre Telegram-Gruppe
MONITORED_CHAT_IDS=-2299206473,-1001804143400  # Überwachte Gruppen
```

### Überwachte Chats
- **-2299206473**: Standard-Signale → Weiterleitung
- **-1001804143400**: @cryptet_com → Vollautomatischer Cryptet-Workflow

## API Endpoints

### Status abrufen

```bash
curl http://localhost:8000/forwarder/status
```

Antwort:

```json
{
  "status": {
    "enabled": true,
    "target_group_id": "-1002773853382",
    "monitored_chat_id": -2299206473,
    "pattern_configured": true
  },
  "monitored_chat": -2299206473,
  "target_group": "-1002773853382"
}
```

### Allgemeiner Status

```bash
curl http://localhost:8000/status
```

## System-Architektur

### Komponenten
1. **SignalForwarder** (`src/core/signal_forwarder.py`)
   - Signal-Erkennung und Parsing
   - Formatierung und Weiterleitung

2. **TelethonConnector** (`src/connectors/telethon_connector.py`)
   - Telegram-Integration
   - Chat-Überwachung

3. **Main Handler** (`src/main.py`)
   - Message-Routing
   - Komponenten-Integration

### Workflow
1. **Nachricht empfangen** von -2299206473
2. **Signal-Prüfung** durch `_is_signal()`
3. **Parsing** durch `_parse_signal()`
4. **Formatierung** durch `_format_signal()`
5. **Weiterleitung** an Ihre Gruppe

## Testing

### Signal Forwarder Test

```bash
python test_signal_forwarder.py
```

### Echte Weiterleitung Test

```bash
python test_real_forwarding.py
```

## Logging

Alle Aktionen werden geloggt:
- `signal_forwarder_initialized`: System gestartet
- `signal_forwarded`: Signal erfolgreich weitergeleitet
- `signal_forwarder_no_signal`: Nachricht war kein Signal
- `signal_forwarder_parse_failed`: Parsing fehlgeschlagen
- `signal_forwarder_error`: Allgemeiner Fehler

## Unterschied zu Cryptet-Workflow

| Quelle | Chat-ID | Verarbeitung |
|--------|---------|--------------|
| Standard-Gruppe | -2299206473 | **Signal-Weiterleitung** → Einfache Weiterleitung |
| @cryptet_com | -1001804143400 | **Cryptet-Automation** → Browser-Automation + P&L-Monitoring |

## Status

✅ **Aktiv und funktionsfähig**
- Signal-Erkennung: ✅
- Parsing: ✅
- Formatierung: ✅
- Telegram-Weiterleitung: ✅
- API-Endpoints: ✅
- Logging: ✅

Das System überwacht jetzt automatisch beide Gruppen und verarbeitet Signale entsprechend ihrer Quelle.
