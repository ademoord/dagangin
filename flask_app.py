from flask import request
from flask_login import login_required
from flask_wtf.csrf import CSRFProtect, generate_csrf

from blueprints.auth import auth_bp
from blueprints.products import products_bp
from blueprints.partners import partners_bp
from blueprints.invoicing import invoicing_bp
from blueprints.inventory import inventory_bp
from blueprints.main import main_bp
from blueprints.pos import pos_bp
from blueprints.purchase import purchase_bp
from blueprints.reporting import reporting_bp
from config import app, db, login_manager
from helpers import format_date_id, format_rupiah
from models import User
from seed import seed_if_local

csrf = CSRFProtect(app)


@app.template_filter('rupiah')
def rupiah_filter(amount):
    return format_rupiah(amount)


@app.template_filter('date_id')
def date_id_filter(dt, with_time=False):
    return format_date_id(dt, with_time=with_time)


@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf)


app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(products_bp)
app.register_blueprint(pos_bp)
app.register_blueprint(purchase_bp)
app.register_blueprint(partners_bp)
app.register_blueprint(invoicing_bp)
app.register_blueprint(reporting_bp)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.after_request
def set_security_headers(response):
    if not app.config.get('LOCAL_DEV') and request.headers.get('X-Forwarded-Proto') == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response


with app.app_context():
    db.create_all()
    if app.config.get('LOCAL_DEV'):
        seed_if_local()
