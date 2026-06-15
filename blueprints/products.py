from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from config import db
from helpers import stock_status
from models import Category, Product

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)

    query = Product.query.join(Category)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        like = '%{}%'.format(search)
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like)))

    pagination = query.order_by(Product.name).paginate(page=page, per_page=15, error_out=False)
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'products/index.html',
        title='Data Produk',
        products=pagination.items,
        pagination=pagination,
        search=search,
        categories=categories,
        active_category=category_id,
    )


@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            category_id = request.form.get('category_id', type=int)
            sku = request.form.get('sku', '').strip()
            stock = request.form.get('stock', 0, type=int)
            unit = request.form.get('unit', 'pcs').strip()
            price = Decimal(request.form.get('price', '0'))
            cost = Decimal(request.form.get('cost', '0') or '0')
            threshold = request.form.get('low_stock_threshold', 5, type=int)

            if not name or not category_id:
                raise ValueError('Nama dan kategori wajib diisi.')

            if not sku:
                cat = Category.query.get(category_id)
                prefix = cat.name[:3].upper() if cat else 'PRD'
                sku = '{}-{:03d}'.format(prefix, Product.query.count() + 1)

            product = Product(
                name=name,
                sku=sku,
                category_id=category_id,
                stock=stock,
                unit=unit,
                price=price,
                cost=cost,
                low_stock_threshold=threshold,
            )
            db.session.add(product)
            db.session.commit()
            flash('Produk {} berhasil ditambahkan.'.format(name), 'success')

            next_url = request.form.get('next') or request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('products.index'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'products/form.html',
        title='Tambah Produk',
        categories=categories,
        product=None,
        next_url=request.args.get('next', ''),
    )


@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        try:
            product.name = request.form.get('name', '').strip()
            product.category_id = request.form.get('category_id', type=int)
            product.sku = request.form.get('sku', '').strip()
            product.unit = request.form.get('unit', 'pcs').strip()
            product.price = Decimal(request.form.get('price', '0'))
            product.cost = Decimal(request.form.get('cost', '0') or '0')
            product.low_stock_threshold = request.form.get('low_stock_threshold', 5, type=int)
            db.session.commit()
            flash('Produk berhasil diperbarui.', 'success')
            return redirect(url_for('products.index'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')

    return render_template(
        'products/form.html',
        title='Ubah Produk',
        categories=categories,
        product=product,
        next_url='',
    )


@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Produk dihapus.', 'info')
    return redirect(url_for('products.index'))
