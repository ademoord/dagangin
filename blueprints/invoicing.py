from datetime import timedelta
from decimal import Decimal
import io

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from config import db
from helpers import generate_number, now_wib
from models import INVOICE_STATUS_LABELS, Invoice, InvoiceLine, Partner, Product
from services.invoice_pdf import build_invoice_pdf

invoicing_bp = Blueprint('invoicing', __name__, url_prefix='/invoicing')


@invoicing_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    selected_id = request.args.get('selected', type=int)

    pagination = Invoice.query.join(Partner).order_by(
        Invoice.created_at.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    invoices = []
    for inv in pagination.items:
        label, variant = INVOICE_STATUS_LABELS.get(inv.status, (inv.status, 'muted'))
        invoices.append({'invoice': inv, 'status_label': label, 'status_variant': variant})

    selected = Invoice.query.get(selected_id) if selected_id else None
    if not selected and invoices:
        selected = invoices[0]['invoice']

    return render_template(
        'invoicing/index.html',
        title='Daftar Faktur',
        invoices=invoices,
        pagination=pagination,
        selected=selected,
    )


@invoicing_bp.route('/preview/<int:invoice_id>')
@login_required
def preview(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoicing/_preview.html', selected=invoice)


@invoicing_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    partners = Partner.query.filter(Partner.is_customer.is_(True)).order_by(Partner.name).all()
    products = Product.query.order_by(Product.name).all()

    if request.method == 'POST':
        try:
            partner_id = request.form.get('partner_id', type=int)
            notes = request.form.get('notes', '').strip()
            due_days = request.form.get('due_days', 14, type=int)
            product_ids = request.form.getlist('product_id')
            quantities = request.form.getlist('quantity')
            prices = request.form.getlist('unit_price')

            if not partner_id:
                raise ValueError('Mitra pelanggan wajib dipilih.')

            partner = Partner.query.get(partner_id)
            if not partner or not partner.is_customer:
                raise ValueError('Mitra yang dipilih bukan pelanggan.')

            lines = []
            subtotal = Decimal('0')
            for pid, qty, price in zip(product_ids, quantities, prices):
                if not pid:
                    continue
                qty = int(qty or 0)
                unit_price = Decimal(price or '0')
                if qty <= 0:
                    continue
                line_total = unit_price * qty
                subtotal += line_total
                lines.append((int(pid), qty, unit_price, line_total))

            if not lines:
                raise ValueError('Minimal satu item faktur.')

            last_id = db.session.query(db.func.max(Invoice.id)).scalar() or 0
            invoice_number = generate_number('INV', last_id)

            invoice = Invoice(
                invoice_number=invoice_number,
                partner_id=partner_id,
                status='sent',
                subtotal=subtotal,
                total=subtotal,
                issue_date=now_wib(),
                due_date=now_wib() + timedelta(days=due_days),
                notes=notes,
            )
            db.session.add(invoice)
            db.session.flush()

            for pid, qty, unit_price, line_total in lines:
                db.session.add(InvoiceLine(
                    invoice_id=invoice.id,
                    product_id=pid,
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                ))

            db.session.commit()
            flash('Faktur {} berhasil dibuat.'.format(invoice_number), 'success')
            return redirect(url_for('invoicing.index', selected=invoice.id))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'invoicing/form.html',
        title='Buat Faktur',
        partners=partners,
        products=products,
    )


@invoicing_bp.route('/<int:invoice_id>/pdf')
@login_required
def download_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    pdf_bytes = build_invoice_pdf(invoice)
    filename = '{}.pdf'.format(invoice.invoice_number.replace('/', '-'))
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


@invoicing_bp.route('/<int:invoice_id>/status', methods=['POST'])
@login_required
def update_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form.get('status', invoice.status)
    allowed = {'sent', 'paid', 'pending', 'overdue', 'cancelled'}

    if new_status not in allowed:
        flash('Status tidak valid.', 'error')
        return redirect(url_for('invoicing.index', selected=invoice.id))

    invoice.status = new_status
    db.session.commit()
    label, _ = INVOICE_STATUS_LABELS.get(new_status, (new_status, 'muted'))
    flash('Status faktur diubah menjadi {}.'.format(label), 'success')
    return redirect(url_for('invoicing.index', selected=invoice.id))
