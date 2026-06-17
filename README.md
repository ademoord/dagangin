# Dagangin

POS-ERP micro-web app for Indonesian UMKM. Flask-only stack with HTMX, Alpine.js, and Chart.js.

**Database:** SQLite (`data/dagangin.sqlite3`) — local dev and production (PythonAnywhere Free tier).

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5001 — login: `admin` / `dagangin123`

## Documentation

- [PythonAnywhere deployment](docs/PYTHONANYWHERE.md)
- [Provisioning checklist](scripts/provision.sh)
