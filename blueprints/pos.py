from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from config import db
from helpers import format_rupiah, generate_number
from models import Category, Product, Sale, SaleLine
from services.cart import (
    add_to_cart,
    cart_summary,
    clear_cart,
    decrement_stock,
    get_cart,
    set_cart_qty,
)

pos_bp = Blueprint('pos', __name__, url_prefix='/pos')


def _recent_product_ids():
    recent = request.cookies.get('recent_products', '')
    ids = []
    for part in recent.split(','):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids[:8]


@pos_bp.route('/')
@login_required
def index():
    category_id = request.args.get('category', type=int)
    search = request.args.get('q', '').strip()

    categories = Category.query.order_by(Category.name).all()
    query = Product.query.filter(Product.stock > 0)

    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        like = '%{}%'.format(search)
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like)))

    products = query.order_by(Product.name).all()
    recent_ids = _recent_product_ids()
    recent_products = Product.query.filter(Product.id.in_(recent_ids)).all() if recent_ids else []
    recent_map = {p.id: p for p in recent_products}
    recent_products = [recent_map[i] for i in recent_ids if i in recent_map]

    items, subtotal, count = cart_summary()
    discount = Decimal(request.form.get('discount', '0') if request.method == 'POST' else '0')
    total = subtotal - discount

    return render_template(
        'pos/index.html',
        title='POS',
        products=products,
        categories=categories,
        active_category=category_id,
        search=search,
        recent_products=recent_products,
        cart_items=items,
        cart_subtotal=subtotal,
        cart_total=total,
        cart_count=count,
        cart_discount=discount,
    )


@pos_bp.route('/cart/partial')
@login_required
def cart_partial():
    items, subtotal, count = cart_summary()
    discount = Decimal(request.args.get('discount', '0') or '0')
    total = subtotal - discount
    return render_template(
        'pos/_cart.html',
        cart_items=items,
        cart_subtotal=subtotal,
        cart_total=total,
        cart_count=count,
        cart_discount=discount,
    )


@pos_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def cart_add(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock <= 0:
        flash('Stok {} habis.'.format(product.name), 'error')
        return cart_partial_view()

    cart = get_cart()
    current_qty = cart.get(str(product_id), 0)
    if current_qty + 1 > product.stock:
        flash('Stok {} tidak cukup.'.format(product.name), 'error')
        return cart_partial_view()

    add_to_cart(product_id, 1)
    return cart_partial_view()


@pos_bp.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required
def cart_update(product_id):
    quantity = request.form.get('quantity', type=int) or 0
    product = Product.query.get_or_404(product_id)
    if quantity > product.stock:
        flash('Stok {} maksimal {}.'.format(product.name, product.stock), 'error')
        quantity = product.stock
    set_cart_qty(product_id, quantity)
    return cart_partial_view()


@pos_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def cart_remove(product_id):
    set_cart_qty(product_id, 0)
    return cart_partial_view()


def cart_partial_view():
    items, subtotal, count = cart_summary()
    discount = Decimal(request.form.get('discount', '0') or '0')
    total = subtotal - discount
    return render_template(
        'pos/_cart.html',
        cart_items=items,
        cart_subtotal=subtotal,
        cart_total=total,
        cart_count=count,
        cart_discount=discount,
    )


@pos_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    items, subtotal, count = cart_summary()
    if not items:
        flash('Keranjang kosong.', 'error')
        return redirect(url_for('pos.index'))

    discount = Decimal(request.form.get('discount', '0') or '0')
    notes = request.form.get('notes', '').strip()
    total = subtotal - discount
    if total < 0:
        total = Decimal('0')

    try:
        last_id = db.session.query(db.func.max(Sale.id)).scalar() or 0
        sale_number = generate_number('SL', last_id)

        sale = Sale(
            sale_number=sale_number,
            user_id=current_user.id,
            subtotal=subtotal,
            discount=discount,
            total=total,
            notes=notes,
        )
        db.session.add(sale)
        db.session.flush()

        for item in items:
            product = item['product']
            qty = item['quantity']
            decrement_stock(product.id, qty, 'sale', sale.id)
            line = SaleLine(
                sale_id=sale.id,
                product_id=product.id,
                quantity=qty,
                unit_price=product.price,
                line_total=item['line_total'],
            )
            db.session.add(line)

        db.session.commit()
        clear_cart()
        flash('Pembayaran berhasil! No. transaksi: {}'.format(sale_number), 'success')
        return redirect(url_for('pos.receipt', sale_id=sale.id))
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), 'error')
        return redirect(url_for('pos.index'))


@pos_bp.route('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('pos/receipt.html', title='Struk', sale=sale)
