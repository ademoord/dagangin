# Dagangin on PythonAnywhere

Dagangin is a Flask-only POS-ERP micro-web app designed for **one PythonAnywhere account per business** (e.g. `dagangin-burgerking.pythonanywhere.com`).

## Recommended tier

| Tier | Suitable for |
|------|----------------|
| Free | Local demo only — no MySQL on new accounts, 1 worker, app expiry |
| **Developer (~$10/mo)** | Production customers — MySQL, scheduled tasks, custom domain |

## Stack

- Flask + Jinja2 (server-rendered UI)
- HTMX + Alpine.js (POS cart, invoice preview)
- Chart.js (reporting dashboards)
- SQLite (local dev) / MySQL (production)

## Local development

```bash
cd usahain
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5001 — login: `admin` / `dagangin123`

## Production deploy (per customer)

### 1. Create PA account

Register `dagangin-{client}` on PythonAnywhere (Developer tier).

### 2. Upload code

Upload this directory to `/home/USERNAME/dagangin` via git clone, SFTP, or PA console.

### 3. Virtualenv

```bash
mkvirtualenv --python=/usr/bin/python3.13 dagangin-venv
pip install -r ~/dagangin/requirements.txt
```

### 4. MySQL database

In the Databases tab, create a database named `USERNAME$dagangin`.

### 5. config.txt

Create `~/config.txt`:

```
SECRET_KEY=your-random-secret-here
SQLALCHEMY_DATABASE_URI=mysql+pymysql://USERNAME@USERNAME.mysql.pythonanywhere-services.com/USERNAME$dagangin
SQLALCHEMY_TRACK_MODIFICATIONS=False
BUSINESS_NAME=Nama Toko Client
```

### 6. WSGI configuration

Point the Web tab WSGI file to import from `wsgi.py`:

```python
import sys
path = '/home/USERNAME/dagangin'
if path not in sys.path:
    sys.path.insert(0, path)
from wsgi import application
```

### 7. Static files

Map `/static/` → `/home/USERNAME/dagangin/static/`

### 8. Initialize database

```bash
workon dagangin-venv
cd ~/dagangin
python -c "from flask_app import app, db; app.app_context().push(); db.create_all()"
python -c "from seed import seed_if_local; from flask_app import app; app.app_context().push(); seed_if_local()"
```

Change the default admin password immediately in production.

### 9. Reload web app

Use the Reload button on the Web tab.

## Provisioning script

Run `./scripts/provision.sh` locally with `CLIENT_SLUG` and `PA_USERNAME` set for a printable checklist.

## Modules

| Route | Module |
|-------|--------|
| `/pos/` | Point of sale with HTMX cart |
| `/inventory/` | Product CRUD + stock badges |
| `/purchase/` | Purchase orders |
| `/invoicing/` | Invoices with desktop preview |
| `/reporting/` | KPI cards + Chart.js |

## Notes

- One web worker handles one request at a time — fine for small UMKM (1–2 kasir).
- Upgrade PA plan for additional workers if a client grows.
- No Node.js build step required — all assets are plain CSS/JS.
