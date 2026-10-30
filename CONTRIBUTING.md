# Contributing / Mitmachen

English · Deutsch (below)

## English

Thanks for your interest. AgentWorkbench is intentionally small: one FastAPI process, one SQLite file, no build step and no JavaScript framework.

- **Ideas and bugs:** open an issue and say what you want to do or what went wrong. For security issues see [SECURITY.md](SECURITY.md).
- **Changes:** fork, branch, and open a pull request. Keep it focused. A change that adds a framework or a build step needs a very good reason.
- **Tests:** run `pytest` before you open the pull request. New behaviour comes with a test. The CI runs the suite and builds the Docker image.
- **Texts:** the interface is German and English. Add a key to **both** dictionaries, see [docs/development.md](docs/development.md#translations).
- **Docs:** user-facing changes update the English docs in `docs` **and** the German ones in `docs/de`.
- **No personal data:** do not commit hostnames, tokens, names or screenshots of real projects. Use the demo data (`scripts/demo_seed.py`).

Project layout, tests and screenshots are described in [docs/development.md](docs/development.md).

## Deutsch

Danke für dein Interesse. AgentWorkbench ist absichtlich klein: ein FastAPI-Prozess, eine SQLite-Datei, kein Build-Schritt und kein JavaScript-Framework.

- **Ideen und Fehler:** Eröffne ein Issue und sage, was du vorhast oder was schiefging. Für Sicherheitsprobleme siehe [SECURITY.md](SECURITY.md).
- **Änderungen:** Fork, Branch und Pull Request. Halte sie fokussiert. Eine Änderung, die ein Framework oder einen Build-Schritt einführt, braucht einen sehr guten Grund.
- **Tests:** Führe `pytest` aus, bevor du den Pull Request öffnest. Neues Verhalten bekommt einen Test. Die CI führt die Suite aus und baut das Docker-Image.
- **Texte:** Die Oberfläche ist deutsch und englisch. Füge einen Schlüssel in **beide** Wörterbücher ein, siehe [docs/de/development.md](docs/de/development.md#übersetzungen).
- **Doku:** Änderungen, die Benutzer sehen, aktualisieren die englische Doku in `docs` **und** die deutsche in `docs/de`.
- **Keine persönlichen Daten:** Keine Hostnamen, Tokens, Namen oder Screenshots echter Projekte einchecken. Nutze die Demodaten (`scripts/demo_seed.py`).

Aufbau, Tests und Screenshots stehen in [docs/de/development.md](docs/de/development.md).
