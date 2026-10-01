# authentik passwordless sample

Ein lokales Minimalbeispiel für **React / Next.js + NextAuth → authentik → FastAPI** mit Python 3.13, uv, Docker Compose und Mailpit. Alle anwendungsspezifischen authentik-Objekte werden durch `authentik/blueprints/sample.yaml` erstellt, einschließlich Flows, Policies, Prompts, OIDC-Provider, Claims und Brand. Keine manuelle Einrichtung im Admin-UI erforderlich.

## Start

Voraussetzungen: laufendes Docker mit Compose, Make, Python 3 auf dem Host. Node, uv und Python 3.13 laufen in den Containern. Ports 3000, 8000, 8025 und 9000 müssen frei sein. Beim ersten Start werden Images heruntergeladen; authentik führt seine Datenbankmigrationen aus.

```sh
make start-dev
```

Der Befehl erzeugt fehlende zufällige Secrets in `.env`, baut und startet den Stack, wartet auf die Dienste und wendet den Blueprint an. Ein erneuter Aufruf übernimmt Änderungen am Blueprint. Bestehende Secrets und SMTP-Einstellungen bleiben erhalten.

| Dienst | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Mailpit / Entwicklungspostfach | http://localhost:8025 |
| FastAPI / Swagger | http://localhost:8000/docs |
| authentik | http://localhost:9000 |

```sh
make stop-dev  # Container stoppen; Daten und E-Mails bleiben in Volumes
make logs     # Logs verfolgen
make test     # Backend-Tests in Python 3.13 ausführen
```

Frontend- und Backend-Quellcode ist für Hot Reload eingebunden. Nach Änderungen an Abhängigkeiten, Compose oder Dockerfiles erneut `make start-dev` ausführen. Blueprint- und Template-Änderungen ebenfalls mit `make start-dev` übernehmen.

## Registrierung und Login ausprobieren

1. Frontend öffnen und **Log in / Sign up** anklicken.
2. Eine beliebige neue Adresse wie `you@example.test` eingeben. Die Loginoption ist standardmäßig **Sign in with magic link**.
3. Für eine unbekannte Adresse öffnet sich automatisch die Registrierung mit dem Hinweis, dass noch kein Account existiert. E-Mail, Vorname und Nachname eingeben.
4. In Mailpit die Nachricht **Complete your registration** öffnen. Den Link im selben Browser öffnen und **Continue** bestätigen. Die zusätzliche Bestätigung stammt aus authentik und verhindert, dass ein E-Mail-Scanner den Link beim bloßen Öffnen verbraucht.
5. Die Registrierung aktiviert den Account und meldet ihn direkt im Frontend an. **Get User Info** zeigt die Antwort von FastAPI mit `sub`, `email`, `first_name`, `last_name` und `created_at`.
6. **Sign out** beendet die NextAuth- und authentik-Sessions und führt zurück ins Frontend.
7. Bei einem vorhandenen Account versendet **Sign in with magic link** die Nachricht **Your sign-in link**. Der Link funktioniert nur mit der authentik-Session des anfordernden Browsers.
8. Auf einem anderen Gerät einen eigenen Login starten und **Sign in with code instead** wählen. Mailpit enthält dann einen sechsstelligen Code, der im Login des Zielgeräts eingegeben wird. Das Postfach kann auf einem beliebigen Gerät gelesen werden.

Für einen Wechsel von einem bereits gestarteten Magic-Link-Login zur Code-Variante ins Frontend zurückgehen und erneut **Log in / Sign up** wählen. Der NextAuth-Handler beendet den unfertigen authentik-Flow vor dem neuen Login. Der Magic-Link-Mailtext enthält ebenfalls einen Hinweis zur Code-Alternative.

Ein versehentlich im falschen Browser bestätigter Link wird abgewiesen, kann dabei aber bereits verbraucht werden. Dann einen neuen Link anfordern oder den Code-Login starten. Nicht bestätigte Registrierungen bleiben inaktiv; über einen neuen Magic-Link-Login lässt sich die E-Mail-Verifikation nachholen. Der Code-Login ist bis dahin gesperrt.

## Token und Browserbindung

- NextAuth nutzt einen vertraulichen OIDC-Client mit Authorization Code, **PKCE S256**, State und Nonce. Die Tokens liegen in der verschlüsselten NextAuth-Session. Der Access Token wird für diesen Demo-Aufruf an den angemeldeten Browser ausgegeben; dieser sendet ihn direkt als `Authorization: Bearer …` an FastAPI.
- FastAPI lädt authentiks öffentliche JWKS-Schlüssel und prüft **RS256-Signatur, Issuer, Audience, Ablauf und erforderliche Claims**. Zusätzlich ist der Scope `sample_user` nötig. Vorname, Nachname und das tatsächliche `date_joined` kommen aus einer authentik-Scope-Mapping-Expression. Dafür braucht die API keinen Admin-Token und keine eigene User-Datenbank.
- Öffentliche OIDC-URLs verwenden `localhost:9000`. Serverseitige Token- und JWKS-Anfragen verwenden Compose-DNS `authentik-server:9000`. NextAuth setzt dabei den öffentlichen Host-Header, damit der Token-Issuer konsistent bleibt. Endpunkte sind explizit konfiguriert: NextAuth v4 würde bei Discovery die internen Endpunkte durch öffentliche URLs ersetzen.
- Eine Blueprint-Policy erzeugt einen zufälligen Browsernachweis in der serverseitigen authentik-Session. Der E-Mail-FlowToken enthält eine Kopie. Nach der Linkbestätigung vergleicht eine Policy den **ursprünglichen Token-Plan** mit der aktuellen Session und der User-ID. Das ist erforderlich, weil authentik beim Wiederherstellen den Token-Kontext mit einem vorhandenen Flow-Kontext zusammenführt. Ein Deny-Stage blockiert Abweichungen vor Aktivierung oder Login. Bei Policy-Fehlern wird ebenfalls verweigert.
- Nach verifiziertem Link wird ein nativer authentik-EmailDevice für genau die verifizierte Adresse angelegt. Der Code-Login verwendet den eingebauten Authenticator Validation Stage; Codes sind einmalig, fünf Minuten gültig und falsche Versuche werden durch authentik gedrosselt. Die finale Policy verlangt außerdem den tatsächlich validierten E-Mail-Authenticator.
- Der Email-Stage ist mit zehn Minuten Tokenlaufzeit konfiguriert; authentik 2026.8.3 fügt intern eine Minute hinzu. Access Tokens sind 15 Minuten gültig. Das Minimalbeispiel implementiert kein automatisches Token-Refresh: nach Ablauf erneut anmelden.
- Sign-out entfernt beide Browser-Sessions. Ein bereits kopierter JWT-Access-Token bleibt bis zu seinem Ablauf gültig, da FastAPI die Signatur lokal prüft.

## SMTP statt Mailpit

In `.env` die vorbereiteten Einstellungen ändern und `make start-dev` ausführen:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=login@example.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

`SMTP_USE_TLS` aktiviert STARTTLS; für SMTPS typischerweise Port 465 mit `SMTP_USE_SSL=true` und `SMTP_USE_TLS=false`. Alle E-Mail-Stages verwenden die globalen authentik-SMTP-Einstellungen. Mailpit liefert keine Nachrichten nach außen aus; nur bei explizitem Wechsel zu einem echten SMTP-Server werden echte E-Mails verschickt.

## Aufbau und Grenzen

- `compose.yaml`: sechs Dienste, persistente Volumes und Healthchecks; nur lokale Loopback-Ports sind veröffentlicht. PostgreSQL JIT ist deaktiviert, um die vielen kleinen Blueprint-Abfragen beim lokalen Start zu beschleunigen.
- `authentik/blueprints/sample.yaml`: gesamte authentik-Konfiguration als deklarative YAML mit Expression-Policies.
- `authentik/templates/email/`: HTML- und Text-Mails für Registrierung, Magic Link und Code.
- `frontend/lib/auth.ts`: NextAuth-Konfiguration; `frontend/app/page.tsx`: Demo-Oberfläche.
- `backend/app/main.py`: Tokenprüfung und geschütztes `/api/user`.
- `backend/tests/test_tokens.py`: kryptografische Positiv- und Negativtests.
- `docs/verification.md`: Ergebnisse der Browserprüfung.

Das Beispiel verwendet HTTP und feste localhost-Adressen. Für einen anderen Host müssen öffentliche URLs, OIDC-Redirect-URIs, Host-Header und CORS-Origin gemeinsam angepasst werden; für Produktivbetrieb TLS verwenden. Der ausdrücklich gewünschte Hinweis für unbekannte Accounts legt offen, ob eine Adresse registriert ist. Bei Bedarf ist der bestehende Admin-Flow unter `http://localhost:9000/if/flow/default-authentication-flow/` erreichbar; der Nutzer heißt `akadmin`, sein zufälliges Bootstrap-Passwort steht lokal in `.env`. `.env` ist von Git ausgeschlossen.

Versionen: authentik **2026.8.3**, Next.js **16.3.8**, NextAuth **4.24.15**, Mailpit **1.31.3**, Python **3.13**, uv **0.12.21**, PostgreSQL **16**. Python- und npm-Abhängigkeiten sind in Lockfiles festgehalten.

## Wiederverwendbarer Integrationsprompt

Den folgenden Prompt in das Zielprojekt kopieren und die Platzhalter ersetzen. Er beschreibt die vollständige Logik dieses Beispiels einschließlich der Browserbindung und des Code-Fallbacks. Falls dieses Repository als Referenz verfügbar ist, seinen Pfad oder seine Git-URL angeben; der Prompt funktioniert auch ohne Referenz.

```text
Integriere die folgende passwortlose Authentifizierung vollständig in dieses
Projekt. Arbeite im vorhandenen Repository und passe dich an dessen Struktur,
UI, Konventionen und Infrastruktur an.

Projektparameter:
- Projektname: <PROJEKTNAME>
- authentik Application-Slug: <APP_SLUG>
- Öffentliche Frontend-URL: <FRONTEND_URL, z. B. http://localhost:3000>
- Öffentliche Backend-URL: <BACKEND_URL, z. B. http://localhost:8000>
- Öffentliche authentik-URL: <AUTHENTIK_URL, z. B. http://localhost:9000>
- Interne authentik-URL: <AUTHENTIK_INTERNAL_URL,
  z. B. http://authentik-server:9000>
- OIDC-Client-ID: <OIDC_CLIENT_ID>
- Geschützter API-Scope: <USER_SCOPE, z. B. sample_user>
- Optionale Referenz: <PFAD ODER GIT-URL DIESES BEISPIELS; SONST WEGLASSEN>

Vorgehen:
1. Prüfe zuerst das Repository und vorhandene Authentication-Lösungen.
   Lies die aktuelle offizielle Dokumentation von authentik, NextAuth/Auth.js,
   FastAPI, uv und Mailpit. Prüfe die Syntax gegen die tatsächlich verwendeten
   Versionen. Übernimm versionsabhängige Implementierungsdetails der Referenz
   nur nach Prüfung. Dokumentiere und fixiere die gewählten Versionen.
2. Plane Architektur, Flows, Konfiguration und Verifikation. Stelle notwendige
   Rückfragen vor der Implementierung und nutze für Routineentscheidungen
   sinnvolle, ausdrücklich dokumentierte Annahmen.
3. Baue die Integration vollständig und teste sie selbst end-to-end mit dem
   integrierten Browser und Mailpit. Liefere eine funktionierende Umsetzung,
   nachvollziehbare Testergebnisse und Startanweisungen.

Technischer Aufbau:
- React-Frontend mit Next.js und NextAuth/Auth.js für OIDC und Sessions.
- FastAPI-Backend mit Python 3.13 und uv; Python- und npm-Lockfiles einchecken.
- Docker Compose mit Frontend, Backend, authentik-Server, authentik-Worker,
  PostgreSQL und Mailpit. Vorhandene passende Dienste integrieren.
- Ein Makefile mit `make start-dev`, das den gesamten lokalen Stack baut,
  startet, auf Bereitschaft wartet und die aktuelle Konfiguration anwendet.
  Ergänze `make stop-dev`, `make logs` und `make test`.
- Keine manuelle authentik-Einrichtung: alle anwendungsspezifischen Flows,
  Stages, Prompts, Policies, Scope-Mappings, Provider, Application, Brand und
  Logout-Konfiguration über versionierte authentik-Blueprints deklarieren.
  Eigene Expression-Policies sind erlaubt; native Stages bevorzugen.
- Secrets außerhalb von Git in `.env` halten. Fehlende Secrets zufällig
  erzeugen und bestehende Secrets sowie SMTP-Einstellungen erhalten.
  `.env.example`, persistente Datenvolumes und Healthchecks bereitstellen.
  Wiederholtes `make start-dev` muss ohne doppelte Konfigurationsobjekte
  funktionieren und Blueprint-Änderungen übernehmen.

Login und automatische Registrierung:
- Im Frontend gibt es einen Einstieg „Log in / Sign up“. Die eigentlichen
  Formulare werden von authentik angezeigt; keine eigene Passwortprüfung
  oder parallele Login-Implementierung im Frontend beziehungsweise Backend.
- Der Nutzer gibt seine E-Mail ein und kann „Sign in with magic link“ oder
  „Sign in with code instead“ wählen. Magic Link ist die Standardoption.
- E-Mail-Adressen trimmen und konsistent normalisieren; bestehende Nutzer
  ohne Unterscheidung der Groß-/Kleinschreibung finden.
- Existiert kein Account, automatisch zum Sign-up-Flow wechseln. Dort einen
  sichtbaren Hinweis anzeigen, dass der Account noch nicht existiert.
  Die eingegebene E-Mail übernehmen.
- Sign-up erfasst First Name, Last Name und E-Mail; kein Passwort verlangen.
  Vorname und Nachname getrennt als User-Attribute speichern. Erforderliche
  Werte, reine Leerzeichen und doppelte Registrierungen validieren.
- Zunächst einen inaktiven Account erzeugen und eine Verifikationsmail
  schicken. Ohne erfolgreiche Verifikation keine Aktivierung oder Anmeldung.
- Der Link bestätigt die E-Mail, schließt die Registrierung ab und meldet
  den Nutzer über den ursprünglichen OIDC-Flow direkt in der Anwendung an.
  State, PKCE, Nonce und Callback-Ziel dabei erhalten. Die native Bestätigung
  gegen E-Mail-Linkscanner beibehalten.
- Eine nicht abgeschlossene Registrierung muss durch einen neuen
  Magic-Link-Login verifiziert werden können. Für unbestätigte Accounts ist
  Code-Login gesperrt. Bestehende Accounts im Sign-up-Flow nicht überschreiben.

Magic-Link-Login und zwingende Browserbindung:
- Für vorhandene Nutzer einen einmaligen Link mit kurzer Laufzeit mailen.
  Im selben Browser führt die Bestätigung direkt zur angemeldeten Anwendung.
- Der Link darf in einem anderen Browser, Browserprofil oder Gerät keine
  authentik-Session erzeugen und keine Registrierung aktivieren. Prüfe diese
  Bindung in authentik selbst; PKCE oder ein fehlgeschlagener NextAuth-Callback
  allein reichen nicht, weil authentik sonst bereits angemeldet sein könnte.
- Nutze einen kryptografisch zufälligen Nachweis in der serverseitigen
  authentik-Session und im Snapshot des E-Mail-FlowTokens. Prüfe bei Rückkehr
  den Nachweis und die User-ID gegen den ursprünglichen Token-Plan.
  Vertraue nicht allein dem wiederhergestellten Flow-Kontext: authentik kann
  ihn mit einem bestehenden Flow-Kontext des Zielbrowsers zusammenführen.
- Aktivierung und User Login dürfen erst nach erfolgreicher Prüfung erfolgen.
  Fehlende Nachweise, falsche Nutzer und Policy-Ausnahmen müssen verweigern.
  Beachte: eine False-Policy an einer Stage-Bindung überspringt die Stage;
  das ist nicht automatisch eine Verweigerung. Verwende entsprechend
  konfigurierte Deny-Stages und sichere Fehlerergebnisse.
- Zeige beim falschen Browser eine verständliche Meldung mit Hinweis auf den
  ursprünglichen Browser oder einen neuen Code-Login. Dokumentiere, falls
  die native Bestätigung den abgewiesenen Link bereits verbraucht.

Sechsstelliger E-Mail-Code als Fallback:
- Auf dem Zielgerät wird ein eigener OIDC-Login gestartet. Der Nutzer wählt
  „Sign in with code instead“, gibt seine E-Mail ein und erhält einen
  sechsstelligen, einmaligen Code mit fünf Minuten Laufzeit. Führende Nullen
  erhalten. Das Postfach darf auf einem anderen Gerät gelesen werden.
- Ein Code muss nicht zwischen zwei unabhängig gestarteten Login-Vorgängen
  übertragbar sein; er wird im Login des anfordernden Zielgeräts eingegeben.
- Nutze authentiks nativen E-Mail-Authenticator und Authenticator Validation
  Stage mit eingebauter Drosselung falscher Versuche. Keine selbst entwickelte
  Code-Datenbank im Anwendungsbackend.
- Nach erfolgreicher Link-Verifikation einen bestätigten EmailDevice für
  genau diese bereits verifizierte Adresse vorbereiten, damit kein zweiter
  Verifikationsschritt nur zur Code-Einrichtung nötig ist.
- Vor dem finalen Login zusätzlich sicherstellen, dass der E-Mail-Authenticator
  tatsächlich erfolgreich validiert wurde und zum richtigen Nutzer gehört.
- Aus einem unfertigen Magic-Link-Flow muss ein neuer Code-Login möglich sein.
  Alte Flow-Pläne vor dem neuen Login gezielt abbrechen. NextAuth-generierte
  Cookies, State, PKCE und Nonce bei der Weiterleitung vollständig erhalten.

OIDC, Backend und Logout:
- Vertraulicher OIDC-Client mit Authorization Code, PKCE S256, State und Nonce.
  Authorization-Code-Grant explizit konfigurieren, sofern die Version das
  verlangt. Strikte Callback- und Post-Logout-Redirect-URIs verwenden.
- Öffentliche Browser-URLs und interne Compose-DNS-Adressen unterscheiden.
  Der öffentliche Issuer muss in Tokens und Validierung konsistent bleiben.
  Token-, Userinfo- und JWKS-Anfragen müssen aus Containern erreichbar sein.
  Prüfe insbesondere, ob Discovery explizite interne Endpunkte überschreibt.
- JWT-Signatur mit einem authentik-Signaturschlüssel und veröffentlichtem JWKS
  prüfen. In FastAPI nur die konfigurierte Algorithmus-Allowlist akzeptieren
  und Issuer, Audience, Ablauf, erforderliche Claims und API-Scope validieren.
  Fehlende oder ungültige Tokens mit 401, fehlende Berechtigungen mit 403 und
  einen nicht erreichbaren Identity Provider sinnvoll mit 503 beantworten.
- Einen authentifizierten „Get User Info“-Button integrieren. Der Browser
  sendet den Access Token als Bearer Token direkt an FastAPI. Die API liefert
  sub, email, first_name, last_name und created_at. Erstellungszeit aus dem
  tatsächlichen authentik-User-Datensatz beziehen, nicht aus dem Loginzeitpunkt.
  Die Werte über signierte OIDC-Scope-Mappings bereitstellen; kein Admin-Token
  im Frontend und keine unnötige zweite User-Datenbank.
- Tokens in der verschlüsselten NextAuth-Session halten. Nur den benötigten
  Access Token an den angemeldeten Browser geben; ID Token und Client Secret
  nicht in die clientseitige Session aufnehmen. CORS auf das Frontend begrenzen.
- „Sign out“ beendet NextAuth und die authentik-Session über den OIDC-Logout
  und führt zur Frontend-Startseite zurück. Logout-Requests gegen CSRF absichern.
  Ein erneuter Login muss wieder eine Authentifizierung verlangen.
- Access Tokens für dieses Minimalbeispiel 15 Minuten gültig machen. Nach
  Ablauf eine verständliche erneute Anmeldung ermöglichen; automatisches
  Refresh ist kein Muss. Dokumentiere, dass bereits kopierte JWTs bei lokaler
  Signaturprüfung bis zum Ablauf gültig bleiben können.

E-Mail und lokale Entwicklung:
- Globales SMTP per Umgebungsvariablen vorbereiten: Host, Port, Username,
  Password, From, STARTTLS und SSL. Alle E-Mail-Stages verwenden diese Werte.
- Standardmäßig ausschließlich an Mailpit senden. Registrierung, Magic Link
  und Code sollen sich mit erfundenen example.test-Adressen vollständig testen
  lassen. Keine echten E-Mails versenden, solange nicht ausdrücklich gewünscht.
- HTML- und Text-Templates bereitstellen, die Zweck, Laufzeit, Browserbindung
  und Code-Alternative verständlich erklären.
- Lokale Ports nur an Loopback veröffentlichen. Für andere Hosts alle URLs,
  Redirect-URIs, Issuer-Konfiguration und CORS gemeinsam anpassen; für einen
  Produktivbetrieb HTTPS konfigurieren. Bestehende Admin-Zugänge erhalten.
- Den gewünschten Hinweis für unbekannte Accounts implementieren und dessen
  Offenlegung des Registrierungsstatus in der Dokumentation benennen.

Abnahme und Übergabe:
- Teste im integrierten Browser: unbekannte E-Mail -> Sign-up mit Hinweis ->
  Mailpit-Verifikation -> direkt angemeldetes Frontend -> Get User Info ->
  Logout -> erneuter Magic-Link-Login -> erneuter Logout -> Code-Login.
- Teste falsche Codes, verbrauchte Links, unfertige Registrierungen und den
  Wechsel aus einem wartenden Magic-Link-Flow zur Code-Variante.
- Teste einen Link mit getrennten Browser-Cookies und belege, dass in dieser
  Sitzung keine Anmeldung oder Aktivierung erfolgt. Wenn ein zweites Gerät
  oder Browserprofil nur simuliert wird, beschreibe die Methode ausdrücklich.
- Prüfe anonyme Backend-Requests und kryptografische Negativfälle: falsche
  Signatur, falscher Issuer/Audience, abgelaufener oder unsignierter Token,
  fehlende Pflichtclaims und fehlender Scope. Prüfe auch nicht verfügbare JWKS.
- Führe passende Backend-Tests, TypeScript-Prüfung und Frontend-Build aus.
  Prüfe `make start-dev` auch bei wiederholtem Aufruf.
- Ergänze README, Konfigurationsbeispiele und ein Testprotokoll mit tatsächlichen
  Ergebnissen, Screenshots, Annahmen und Grenzen. Keine Secrets, Tokens oder
  Einmalcodes in Git oder Testdokumentation aufnehmen. Behaupte keine Prüfung,
  die nicht durchgeführt wurde. Melde dich nach vollständiger Implementierung
  und Verifikation mit Startbefehl, lokalen URLs und verbleibenden Grenzen.
```

## Dokumentation

Am 1. Oktober 2026 geprüft, zusätzlich die Implementierung des authentik-Tags `version/2026.8.3` und der installierten NextAuth-Version gelesen:

- [authentik Docker Compose](https://docs.goauthentik.io/install-config/install/docker-compose/)
- [Blueprint-Dateistruktur und YAML-Tags](https://docs.goauthentik.io/customize/blueprints/v1/structure/)
- [Prompt Stage](https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/prompt/)
- [Email Stage und Templates](https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/email/)
- [Email Authenticator Setup](https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_email)
- [Authenticator Validation](https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_validate/)
- [Flow-Kontext](https://docs.goauthentik.io/add-secure-apps/flows-stages/flow/context/)
- [Expression-Policies](https://docs.goauthentik.io/customize/policies/types/expression/reference)
- [NextAuth authentik Provider](https://authjs.dev/getting-started/providers/authentik)
- [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [Mailpit Docker](https://mailpit.axllent.org/docs/install/docker/)
- [FastAPI JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
