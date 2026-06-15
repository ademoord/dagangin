from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from config import db
from models import PARTNER_TYPE_FILTERS, Invoice, Partner, PurchaseOrder

partners_bp = Blueprint('partners', __name__, url_prefix='/partners')


def _partner_query(role=None, search=''):
    query = Partner.query
    if role == 'customer':
        query = query.filter(Partner.is_customer.is_(True))
    elif role == 'supplier':
        query = query.filter(Partner.is_supplier.is_(True))
    if search:
        like = '%{}%'.format(search)
        query = query.filter(
            or_(
                Partner.name.ilike(like),
                Partner.phone.ilike(like),
                Partner.email.ilike(like),
            )
        )
    return query.order_by(Partner.name)


@partners_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', 'all')
    search = request.args.get('q', '').strip()

    if role not in PARTNER_TYPE_FILTERS:
        role = 'all'

    pagination = _partner_query(role, search).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'partners/index.html',
        title='Data Mitra',
        partners=pagination.items,
        pagination=pagination,
        role=role,
        search=search,
        role_filters=PARTNER_TYPE_FILTERS,
    )


@partners_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            is_customer = request.form.get('is_customer') == 'on'
            is_supplier = request.form.get('is_supplier') == 'on'

            if not name:
                raise ValueError('Nama mitra wajib diisi.')
            if not is_customer and not is_supplier:
                raise ValueError('Pilih minimal peran Pelanggan atau Vendor.')

            partner = Partner(
                name=name,
                phone=request.form.get('phone', '').strip() or None,
                email=request.form.get('email', '').strip() or None,
                address=request.form.get('address', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
                is_customer=is_customer,
                is_supplier=is_supplier,
            )
            db.session.add(partner)
            db.session.commit()
            flash('Mitra {} berhasil ditambahkan.'.format(name), 'success')

            next_url = request.form.get('next') or request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('partners.index'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'partners/form.html',
        title='Tambah Mitra',
        partner=None,
        next_url=request.args.get('next', ''),
    )


@partners_bp.route('/edit/<int:partner_id>', methods=['GET', 'POST'])
@login_required
def edit(partner_id):
    partner = Partner.query.get_or_404(partner_id)

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            is_customer = request.form.get('is_customer') == 'on'
            is_supplier = request.form.get('is_supplier') == 'on'

            if not name:
                raise ValueError('Nama mitra wajib diisi.')
            if not is_customer and not is_supplier:
                raise ValueError('Pilih minimal peran Pelanggan atau Vendor.')

            partner.name = name
            partner.phone = request.form.get('phone', '').strip() or None
            partner.email = request.form.get('email', '').strip() or None
            partner.address = request.form.get('address', '').strip() or None
            partner.notes = request.form.get('notes', '').strip() or None
            partner.is_customer = is_customer
            partner.is_supplier = is_supplier
            db.session.commit()
            flash('Mitra berhasil diperbarui.', 'success')
            return redirect(url_for('partners.index'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'partners/form.html',
        title='Ubah Mitra',
        partner=partner,
        next_url='',
    )


@partners_bp.route('/delete/<int:partner_id>', methods=['POST'])
@login_required
def delete(partner_id):
    partner = Partner.query.get_or_404(partner_id)

    if partner.invoices.count() or partner.purchase_orders.count():
        flash('Mitra tidak bisa dihapus karena masih dipakai di faktur atau pesanan pembelian.', 'error')
        return redirect(url_for('partners.index'))

    db.session.delete(partner)
    db.session.commit()
    flash('Mitra dihapus.', 'info')
    return redirect(url_for('partners.index'))
