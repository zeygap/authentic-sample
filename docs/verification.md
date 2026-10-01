# Verifikation

Geprüft am **1. Oktober 2026** auf macOS/ARM64 mit Docker Desktop und dem integrierten Codex-Browser. Es wurde ausschließlich SMTP an Mailpit verwendet; keine echte E-Mail-Adresse und kein externer SMTP-Versand.

| Prüfung | Ergebnis |
| --- | --- |
| `make start-dev`, einschließlich wiederholtem Aufruf | Alle sechs Dienste gesund; Blueprint ohne manuelle Admin-Konfiguration angewendet |
| Unbekannte E-Mail beim Login | Automatischer Wechsel zu Sign-up; Hinweis auf fehlenden Account sichtbar; E-Mail übernommen |
| Registrierung mit Vorname, Nachname und E-Mail | Verifikationsmail in Mailpit; nach Link und Continue direkt in NextAuth angemeldet |
| Get User Info nach Registrierung | HTTP 200; tatsächliche authentik-User-ID, E-Mail, Vorname, Nachname und Erstellungsdatum |
| Bestehender Account / Magic Link | Mailpit-Mail, Linkbestätigung im ursprünglichen Browser, erfolgreicher OIDC-Callback und API-Antwort |
| Magic Link ohne ursprüngliche Session | Ablehnung mit erklärendem Hinweis; keine Anmeldung |
| Bestehender Account / sechsstelliger Code | Native Code-Maske; Mailpit-Code führt zum erfolgreichen OIDC-Login |
| Falscher Code | Native Fehlermeldung; keine Anmeldung; anschließend korrekter Code akzeptiert |
| Code-Fallback nach unfertigem Magic-Link-Flow | Erneuter Frontend-Login setzt den unfertigen Flow zurück; Code-Variante erfolgreich |
| Sign-out | NextAuth und authentik abgemeldet; Frontend zeigt Signed out; neuer Login verlangt wieder die E-Mail |
| Backend-Tests | 10 Tests bestanden: gültiger Token, fehlender Token, falsche Audience, falscher Issuer, Ablauf, falsche Signatur, fehlender Scope, unsignierter Token, fehlende Ablaufzeit, nicht verfügbare JWKS |
| Frontend | TypeScript-Prüfung und Next.js-Produktionsbuild erfolgreich |

Die Prüfung ohne ursprüngliche Session wurde im integrierten Browser mit **127.0.0.1 statt localhost** durchgeführt. Dadurch fehlen die an `localhost` gebundenen authentik-Cookies. Dies simuliert den entscheidenden Unterschied eines zweiten Browsers beziehungsweise Geräts. Ein physisches zweites Gerät wurde nicht verwendet. Der Code-Login wurde auf einem frisch gestarteten Login getestet; das E-Mail-Postfach wurde in einem separaten Mailpit-Tab gelesen.

Lokale Screenshots (von Git ausgeschlossen):

- `artifacts/signup-user-info.jpg`: eingeloggter Nutzer unmittelbar nach Registrierung mit FastAPI-Antwort.
- `artifacts/magic-login-user-info.jpg`: eingeloggter Nutzer nach Magic-Link-Login mit FastAPI-Antwort.
- `artifacts/browser-binding-denied.jpg`: abgewiesener Link ohne ursprüngliche Browser-Session.

Die verwendeten Testaccounts `ada.browser@example.test` und `grace.browser@example.test` bleiben zum Ausprobieren in der lokalen Datenbank. Die Container laufen weiter. Secrets, Tokens und Einmalcodes sind nicht in dieser Testdokumentation enthalten.
