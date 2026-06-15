from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from config import db
from models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Selamat datang, {}!'.format(user.username), 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pos.index'))
        flash('Nama pengguna atau kata sandi salah.', 'error')
    return render_template('login.html', title='Masuk')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah keluar.', 'info')
    return redirect(url_for('auth.login'))
