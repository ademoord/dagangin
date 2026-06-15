from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from config import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy='dynamic')


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    sku = db.Column(db.String(32), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    unit = db.Column(db.String(32), default='pcs')
    price = db.Column(db.Numeric(12, 0), default=0, nullable=False)
    cost = db.Column(db.Numeric(12, 0), default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sale_lines = db.relationship('SaleLine', backref='product', lazy='dynamic')
    stock_movements = db.relationship('StockMovement', backref='product', lazy='dynamic')


class Partner(db.Model):
    """Unified contact master — customer and/or vendor (ERP-style Partner)."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    address = db.Column(db.Text)
    is_customer = db.Column(db.Boolean, default=False, nullable=False)
    is_supplier = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='partner', lazy='dynamic')
    purchase_orders = db.relationship('PurchaseOrder', backref='partner', lazy='dynamic')

    @property
    def type_labels(self):
        labels = []
        if self.is_customer:
            labels.append('Pelanggan')
        if self.is_supplier:
            labels.append('Vendor')
        return labels or ['-']

    @property
    def type_summary(self):
        return ' & '.join(self.type_labels) if self.type_labels != ['-'] else '-'

    def __repr__(self):
        return f'<Partner {self.name}>'


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subtotal = db.Column(db.Numeric(12, 0), default=0)
    discount = db.Column(db.Numeric(12, 0), default=0)
    total = db.Column(db.Numeric(12, 0), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='sales')
    lines = db.relationship('SaleLine', backref='sale', lazy='joined', cascade='all, delete-orphan')


class SaleLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 0), nullable=False)
    line_total = db.Column(db.Numeric(12, 0), nullable=False)


class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')
    subtotal = db.Column(db.Numeric(12, 0), default=0)
    total = db.Column(db.Numeric(12, 0), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = db.relationship('POLine', backref='purchase_order', lazy='joined', cascade='all, delete-orphan')


class POLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(12, 0), nullable=False)
    line_total = db.Column(db.Numeric(12, 0), nullable=False)

    product = db.relationship('Product')


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')
    subtotal = db.Column(db.Numeric(12, 0), default=0)
    total = db.Column(db.Numeric(12, 0), default=0)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    lines = db.relationship('InvoiceLine', backref='invoice', lazy='joined', cascade='all, delete-orphan')


class InvoiceLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 0), nullable=False)
    line_total = db.Column(db.Numeric(12, 0), nullable=False)

    product = db.relationship('Product')


class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    movement_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(32))
    reference_id = db.Column(db.Integer)
    notes = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


PO_STATUS_LABELS = {
    'draft': ('Draf', 'muted'),
    'sent': ('Terkirim', 'success'),
    'processing': ('Diproses', 'info'),
    'completed': ('Selesai', 'success'),
    'cancelled': ('Dibatalkan', 'danger'),
}

INVOICE_STATUS_LABELS = {
    'draft': ('Draf', 'muted'),
    'sent': ('Terkirim', 'info'),
    'paid': ('Lunas', 'success'),
    'pending': ('Tertunda', 'warning'),
    'overdue': ('Terlambat', 'danger'),
}

PARTNER_TYPE_FILTERS = {
    'all': 'Semua',
    'customer': 'Pelanggan',
    'supplier': 'Vendor',
}
