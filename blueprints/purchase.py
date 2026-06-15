from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from config import db
from helpers import generate_number
from models import PO_STATUS_LABELS, POLine, Partner, Product, PurchaseOrder
from services.cart import increment_stock

purchase_bp = Blueprint('purchase', __name__, url_prefix='/purchase')


@purchase_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    pagination = PurchaseOrder.query.join(Partner).order_by(
        PurchaseOrder.created_at.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    orders = []
    for po in pagination.items:
        label, variant = PO_STATUS_LABELS.get(po.status, (po.status, 'muted'))
        orders.append({'po': po, 'status_label': label, 'status_variant': variant})

    return render_template(
        'purchase/index.html',
        title='Daftar Pesanan Pembelian',
        orders=orders,
        pagination=pagination,
    )


@purchase_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    partners = Partner.query.filter(Partner.is_supplier.is_(True)).order_by(Partner.name).all()
    products = Product.query.order_by(Product.name).all()

    if request.method == 'POST':
        try:
            partner_id = request.form.get('partner_id', type=int)
            notes = request.form.get('notes', '').strip()
            product_ids = request.form.getlist('product_id')
            quantities = request.form.getlist('quantity')
            costs = request.form.getlist('unit_cost')

            if not partner_id:
                raise ValueError('Mitra vendor wajib dipilih.')

            partner = Partner.query.get(partner_id)
            if not partner or not partner.is_supplier:
                raise ValueError('Mitra yang dipilih bukan vendor.')

            lines = []
            subtotal = Decimal('0')
            for pid, qty, cost in zip(product_ids, quantities, costs):
                if not pid:
                    continue
                qty = int(qty or 0)
                unit_cost = Decimal(cost or '0')
                if qty <= 0:
                    continue
                line_total = unit_cost * qty
                subtotal += line_total
                lines.append((int(pid), qty, unit_cost, line_total))

            if not lines:
                raise ValueError('Minimal satu item pesanan.')

            last_id = db.session.query(db.func.max(PurchaseOrder.id)).scalar() or 0
            po_number = generate_number('PO', last_id)

            po = PurchaseOrder(
                po_number=po_number,
                partner_id=partner_id,
                status='sent',
                subtotal=subtotal,
                total=subtotal,
                notes=notes,
            )
            db.session.add(po)
            db.session.flush()

            for pid, qty, unit_cost, line_total in lines:
                db.session.add(POLine(
                    po_id=po.id,
                    product_id=pid,
                    quantity=qty,
                    unit_cost=unit_cost,
                    line_total=line_total,
                ))

            db.session.commit()
            flash('Pesanan {} berhasil dibuat.'.format(po_number), 'success')
            return redirect(url_for('purchase.index'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'purchase/form.html',
        title='Buat Pesanan Pembelian',
        partners=partners,
        products=products,
    )


@purchase_bp.route('/<int:po_id>/status', methods=['POST'])
@login_required
def update_status(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    new_status = request.form.get('status', po.status)
    allowed = {'sent', 'processing', 'completed', 'cancelled'}

    if new_status not in allowed:
        flash('Status tidak valid.', 'error')
        return redirect(url_for('purchase.index'))

    try:
        if new_status == 'completed' and po.status != 'completed':
            for line in po.lines:
                increment_stock(line.product_id, line.quantity, 'po', po.id)
                product = line.product
                if product:
                    product.cost = line.unit_cost

        po.status = new_status
        db.session.commit()
        label, _ = PO_STATUS_LABELS.get(new_status, (new_status, 'muted'))
        flash('Status pesanan diubah menjadi {}.'.format(label), 'success')
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), 'error')

    return redirect(url_for('purchase.index'))
