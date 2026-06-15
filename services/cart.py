from decimal import Decimal

from flask import session
from sqlalchemy import select

from config import db
from models import Product, StockMovement


def get_cart():
    return session.setdefault('cart', {})


def cart_summary(cart=None):
    cart = cart or get_cart()
    items = []
    subtotal = Decimal('0')
    count = 0

    if not cart:
        return items, subtotal, count

    product_ids = [int(pid) for pid in cart.keys()]
    products = {p.id: p for p in Product.query.filter(Product.id.in_(product_ids)).all()}

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product or qty <= 0:
            continue
        line_total = Decimal(str(product.price)) * qty
        subtotal += line_total
        count += qty
        items.append({
            'product': product,
            'quantity': qty,
            'line_total': line_total,
        })

    return items, subtotal, count


def add_to_cart(product_id, quantity=1):
    cart = get_cart()
    key = str(product_id)
    cart[key] = cart.get(key, 0) + quantity
    if cart[key] <= 0:
        cart.pop(key, None)
    session['cart'] = cart
    session.modified = True


def set_cart_qty(product_id, quantity):
    cart = get_cart()
    key = str(product_id)
    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = quantity
    session['cart'] = cart
    session.modified = True


def clear_cart():
    session.pop('cart', None)
    session.modified = True


def record_stock_movement(product_id, movement_type, quantity, reference_type, reference_id, notes=None):
    movement = StockMovement(
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
    )
    db.session.add(movement)
    return movement


def decrement_stock(product_id, quantity, reference_type, reference_id):
    product = db.session.get(Product, product_id, with_for_update=True)
    if not product:
        raise ValueError('Produk tidak ditemukan.')
    if product.stock < quantity:
        raise ValueError('Stok {} tidak cukup.'.format(product.name))
    product.stock -= quantity
    record_stock_movement(product_id, 'out', quantity, reference_type, reference_id)
    return product


def increment_stock(product_id, quantity, reference_type, reference_id):
    product = db.session.get(Product, product_id, with_for_update=True)
    if not product:
        raise ValueError('Produk tidak ditemukan.')
    product.stock += quantity
    record_stock_movement(product_id, 'in', quantity, reference_type, reference_id)
    return product
