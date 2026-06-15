from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from config import db
from helpers import stock_status
from models import Category, Product
from services.cart import decrement_stock, increment_stock

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@inventory_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')

    query = Product.query.join(Category)
    if search:
        like = '%{}%'.format(search)
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like)))

    products = []
    for product in query.order_by(Product.name).all():
        status_key, label, variant = stock_status(product)
        if status_filter == 'low' and status_key != 'low':
            continue
        if status_filter == 'ok' and status_key != 'ok':
            continue
        if status_filter == 'habis' and status_key != 'habis':
            continue
        products.append({
            'product': product,
            'status_key': status_key,
            'status_label': label,
            'status_variant': variant,
        })

    total = len(products)
    per_page = 15
    start = (page - 1) * per_page
    page_items = products[start:start + per_page]
    pages = max(1, (total + per_page - 1) // per_page)

    class SimplePagination:
        def __init__(self):
            self.page = page
            self.pages = pages
            self.per_page = per_page
            self.total = total
            self.items = page_items
            self.has_prev = page > 1
            self.has_next = page < pages
            self.prev_num = page - 1
            self.next_num = page + 1

        def iter_pages(self):
            return range(1, pages + 1)

    return render_template(
        'inventory/index.html',
        title='Persediaan',
        products=page_items,
        pagination=SimplePagination(),
        search=search,
        status_filter=status_filter,
    )


@inventory_bp.route('/adjust/<int:product_id>', methods=['GET', 'POST'])
@login_required
def adjust(product_id):
    product = Product.query.get_or_404(product_id)
    _, status_label, status_variant = stock_status(product)

    if request.method == 'POST':
        try:
            new_stock = request.form.get('stock', type=int)
            notes = request.form.get('notes', '').strip() or 'Penyesuaian stok manual'

            if new_stock is None or new_stock < 0:
                raise ValueError('Stok harus angka nol atau lebih.')

            diff = new_stock - product.stock
            if diff == 0:
                flash('Stok tidak berubah.', 'info')
                return redirect(url_for('inventory.index'))
            if diff > 0:
                increment_stock(product.id, diff, 'adjustment', product.id)
            else:
                decrement_stock(product.id, -diff, 'adjustment', product.id)

            db.session.commit()
            flash('Stok {} diperbarui menjadi {}.'.format(product.name, new_stock), 'success')
            return redirect(url_for('inventory.index'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'inventory/adjust.html',
        title='Sesuaikan Stok',
        product=product,
        status_label=status_label,
        status_variant=status_variant,
    )
