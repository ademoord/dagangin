from flask import Blueprint, current_app, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    from flask import redirect, url_for
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('pos.index'))
    return redirect(url_for('auth.login'))


@main_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html', title='Pengaturan')


@main_bp.route('/help')
@login_required
def help_page():
    return render_template('help.html', title='Bantuan')


@main_bp.route('/more')
@login_required
def more():
    return render_template('more.html', title='Menu Lainnya')
