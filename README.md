## Student Startup Dashboard (Group 31)

Simple Flask web application built by a student group to explore companies, basic financial snapshots, and a personal watchlist.

### Features
* Add companies (auto-normalizes URL and title)
* View company detail with latest price, market cap, PE, revenue, employees
* Compare two companies side‑by‑side
* Watchlist (add/remove when logged in)
* Lightweight price history chart (3 months daily closes)
* Optional placeholder AI summary flag (`ENABLE_CLAUDE=1`) producing a short static summary (no external API)

### Tech Stack
* Python + Flask
* SQLAlchemy (SQLite locally, can point to Postgres)
* WTForms for simple forms
* yfinance for price data
* Chart.js for charts

### Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r rival_project/requirements.txt
export DATABASE_URL=sqlite:///dev.db
flask --app rival_project.run:app run -p 5002
```
Visit http://127.0.0.1:5002

### Enabling Placeholder Claude Flag
```bash
export ENABLE_CLAUDE=1
flask --app rival_project.run:app run -p 5002
```
Shows minimal deterministic summary text (no real AI calls).

### Notes
Removed unused experimental modules (similarity, summarizer, scheduler, signals) to keep codebase focused and student friendly.
Use `scripts/db_healthcheck.py` for a quick connectivity test when pointing to Postgres.

_This line added to test patch application._
