import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)
default_sqlite_uri = 'sqlite:///' + os.path.join(data_dir, 'dagangin.sqlite3')

home_directory = os.path.expanduser('~')
config_file_path = os.path.join(home_directory, 'config.txt')

# Production (PythonAnywhere): ~/config.txt for secrets + business name.
# Local dev: no config.txt → demo defaults + auto-seed.
# Database is always SQLite (data/dagangin.sqlite3) unless overridden in config.txt.
if os.path.exists(config_file_path):
    with open(config_file_path, 'r') as config_file:
        for line in config_file:
            line = line.strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            app.config[key] = value
else:
    app.config['LOCAL_DEV'] = True
    app.config['SECRET_KEY'] = 'local-dev-dagangin-secret'
    app.config['BUSINESS_NAME'] = 'Dagangin Demo'

if 'SQLALCHEMY_DATABASE_URI' not in app.config:
    app.config['SQLALCHEMY_DATABASE_URI'] = default_sqlite_uri
if 'SQLALCHEMY_TRACK_MODIFICATIONS' not in app.config:
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Silakan masuk terlebih dahulu.'
login_manager.login_message_category = 'info'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
