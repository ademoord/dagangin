# Dagangin on PythonAnywhere

Dagangin is a Flask-only POS-ERP micro-web app designed for **one PythonAnywhere account per business** (e.g. `dagangin-burgerking.pythonanywhere.com`).

**Database:** SQLite everywhere — local dev and production. Each instance stores data in `data/dagangin.sqlite3` inside the project directory.

## Recommended tier

| Tier | Suitable for |
|------|----------------|
| **Free** | Production for one UMKM — SQLite on PA filesystem, no external DB needed |
| Developer (~$10/mo) | More CPU, always-on, custom domain, scheduled tasks |

No paid database service is required.

## Stack

- Flask + Jinja2 (server-rendered UI)
- HTMX + Alpine.js (POS cart, invoice preview)
- Chart.js (reporting dashboards)
- **SQLite** (`data/dagangin.sqlite3`) — local and production

## Local development

No `~/config.txt` on your Mac → SQLite + demo seed automatically.

```bash
git clone https://github.com/ademoord/dagangin.git
cd dagangin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5001 — login: `admin` / `dagangin123`

## Production deploy (per customer)

### 1. Create PA account

Register e.g. `dagangin-{client}` on PythonAnywhere (**Free tier OK**).

### 2. Clone the project

```bash
cd ~
git clone https://github.com/ademoord/dagangin.git
```

Or upload to `/home/USERNAME/dagangin` via SFTP.

### 3. Virtualenv

```bash
mkvirtualenv --python=/usr/bin/python3.13 dagangin-venv
pip install -r ~/dagangin/requirements.txt
```

### 4. config.txt

Create `~/config.txt` in your PA **home directory** (not inside the repo):

```
SECRET_KEY=your-random-secret-here
SQLALCHEMY_TRACK_MODIFICATIONS=False
BUSINESS_NAME=Nama Toko Client
```

`SQLALCHEMY_DATABASE_URI` is **optional**. If omitted, Dagangin uses SQLite at:

`/home/USERNAME/dagangin/data/dagangin.sqlite3`

To set the path explicitly (optional):

```
SQLALCHEMY_DATABASE_URI=sqlite:////home/USERNAME/dagangin/data/dagangin.sqlite3
```

(four slashes after `sqlite:` for an absolute path)

### 5. WSGI configuration

Point the Web tab WSGI file to import from `wsgi.py`:

```python
import sys
path = '/home/USERNAME/dagangin'
if path not in sys.path:
    sys.path.insert(0, path)
from wsgi import application
```

Replace `USERNAME` with your PA username.

### 6. Static files

Map `/static/` → `/home/USERNAME/dagangin/static/`

### 7. Initialize database

Run once in a PA Bash console:

```bash
workon dagangin-venv
cd ~/dagangin
python -c "from flask_app import app, db; app.app_context().push(); db.create_all()"
python -c "from seed import seed_if_local; from flask_app import app; app.app_context().push(); seed_if_local()"
```

Create your own admin user or change the password — do not keep `dagangin123` in production.

### 8. Reload web app

Use the **Reload** button on the Web tab.

## Backup (important)

SQLite lives on PA's disk. **Back up regularly:**

```bash
cp ~/dagangin/data/dagangin.sqlite3 ~/dagangin-backup-$(date +%Y%m%d).sqlite3
```

Download copies via SFTP or PA Files tab. PA does not auto-backup your app data.

## Provisioning script

```bash
CLIENT_SLUG=burgerking PA_USERNAME=dagangin-burgerking ./scripts/provision.sh
```

## Modules

| Route | Module |
|-------|--------|
| `/pos/` | Point of sale with HTMX cart |
| `/products/` | Product catalog CRUD |
| `/inventory/` | Stock monitoring and adjustments |
| `/partners/` | Customer / vendor master |
| `/purchase/` | Purchase orders |
| `/invoicing/` | Invoices with desktop preview + PDF |
| `/reporting/` | KPI cards + Chart.js |

## Notes

- One web worker (Free tier) handles one request at a time — fine for 1–2 kasir UMKM.
- SQLite + single PA worker is a good match: one writer at a time.
- Schema changes use `db.create_all()` today; adopt Flask-Migrate revision files if the schema grows.
- No Node.js build step — all assets are plain CSS/JS.
- Keep `config.txt` out of git (already in `.gitignore`).

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Empty app / no tables | Run `db.create_all()` once in Bash console |
| `OperationalError: unable to open database` | `data/` not writable — check permissions on `~/dagangin/data/` |
| Still shows demo data you don't want | `seed_if_local()` was run — reset by deleting `data/dagangin.sqlite3` and re-init |
| Lost all data after redeploy | SQLite file not backed up — restore from backup copy |
