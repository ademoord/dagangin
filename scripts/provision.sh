#!/usr/bin/env bash
# Provision a new Dagangin instance on PythonAnywhere (Free tier OK).
#
# Usage (run from your local machine after customizing variables):
#   CLIENT_SLUG=burgerking PA_USERNAME=dagangin-burgerking ./scripts/provision.sh
#
# Prerequisites:
# - PythonAnywhere account (Free tier works with SQLite)
# - Client slug chosen (e.g. burgerking -> dagangin-burgerking.pythonanywhere.com)

set -euo pipefail

CLIENT_SLUG="${CLIENT_SLUG:?Set CLIENT_SLUG e.g. burgerking}"
PA_USERNAME="${PA_USERNAME:?Set PA_USERNAME e.g. dagangin-burgerking}"
PA_HOST="${PA_HOST:-www.pythonanywhere.com}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Dagangin provision checklist for: ${PA_USERNAME}.${PA_HOST}"
echo ""
echo "1. Create PythonAnywhere account: ${PA_USERNAME} (Free tier OK)"
echo "2. Clone repo to /home/${PA_USERNAME}/dagangin:"
echo "     git clone https://github.com/ademoord/dagangin.git ~/dagangin"
echo "3. Create virtualenv and install dependencies:"
echo "     mkvirtualenv --python=/usr/bin/python3.13 dagangin-venv"
echo "     pip install -r ~/dagangin/requirements.txt"
echo "4. Create ~/config.txt with:"
cat <<EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
SQLALCHEMY_TRACK_MODIFICATIONS=False
BUSINESS_NAME=Dagangin ${CLIENT_SLUG}
EOF
echo ""
echo "   SQLite database (automatic): /home/${PA_USERNAME}/dagangin/data/dagangin.sqlite3"
echo ""
echo "5. Configure WSGI file (/var/www/${PA_USERNAME}_pythonanywhere_com_wsgi.py):"
cat <<'WSGI'
import sys
path = '/home/USERNAME/dagangin'
if path not in sys.path:
    sys.path.insert(0, path)
from wsgi import application
WSGI
echo "   (replace USERNAME with ${PA_USERNAME})"
echo ""
echo "6. Map static files: URL /static/ -> /home/${PA_USERNAME}/dagangin/static/"
echo "7. Set virtualenv to dagangin-venv on Web tab, then Reload"
echo "8. Open Bash console, activate venv, run:"
echo "      cd ~/dagangin && python -c \"from flask_app import app, db; app.app_context().push(); db.create_all()\""
echo "      cd ~/dagangin && python -c \"from seed import seed_if_local; from flask_app import app; app.app_context().push(); seed_if_local()\""
echo ""
echo "9. Change admin password in production (do not keep dagangin123)"
echo "10. Schedule regular backups of ~/dagangin/data/dagangin.sqlite3"
echo ""
echo "See docs/PYTHONANYWHERE.md for full documentation."
