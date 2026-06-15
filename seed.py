from decimal import Decimal

from config import app, db
from models import (
    Category,
    Invoice,
    InvoiceLine,
    Partner,
    Product,
    PurchaseOrder,
    POLine,
    Sale,
    SaleLine,
    User,
)


def seed_if_local():
    if User.query.first():
        return

    admin = User(username='admin', role='admin')
    admin.set_password('dagangin123')
    db.session.add(admin)

    categories = {}
    for name in ['Makanan', 'Minuman', 'Snack']:
        cat = Category(name=name)
        db.session.add(cat)
        categories[name] = cat
    db.session.flush()

    products_data = [
        ('Nasi Goreng', 'MKN-001', 'Makanan', 25, 'porsi', 18000, 12000),
        ('Mie Goreng', 'MKN-002', 'Makanan', 30, 'porsi', 15000, 10000),
        ('Es Teh Manis', 'MNM-001', 'Minuman', 50, 'gelas', 5000, 2000),
        ('Kopi Susu', 'MNM-002', 'Minuman', 40, 'gelas', 12000, 6000),
        ('Kerupuk', 'SNK-001', 'Snack', 8, 'pack', 3000, 1500),
        ('Pisang Goreng', 'SNK-002', 'Snack', 15, 'porsi', 8000, 4000),
    ]

    for name, sku, cat_name, stock, unit, price, cost in products_data:
        db.session.add(Product(
            name=name,
            sku=sku,
            category_id=categories[cat_name].id,
            stock=stock,
            unit=unit,
            price=price,
            cost=cost,
            low_stock_threshold=5,
        ))

    partners_data = [
        ('PT Sumber Pangan', '081234567890', None, 'Jl. Pasar Induk No. 12', False, True),
        ('CV Minuman Segar', '081987654321', 'minuman@email.com', 'Jl. Raya Bekasi KM 5', False, True),
        ('Warung Bu Siti', '081111111111', None, 'Jl. Melati No. 3', True, False),
        ('Kantin SMK 1', '082222222222', 'kantin@smk1.sch.id', 'SMK Negeri 1', True, False),
        ('Toko Berkah', '083333333333', None, 'Jl. Merdeka No. 88', True, True),
    ]

    for name, phone, email, address, is_customer, is_supplier in partners_data:
        db.session.add(Partner(
            name=name,
            phone=phone,
            email=email,
            address=address,
            is_customer=is_customer,
            is_supplier=is_supplier,
        ))

    db.session.commit()
    _seed_sample_transactions()


def _seed_sample_transactions():
    from datetime import timedelta
    from helpers import generate_number, now_wib
    from models import StockMovement
    from services.cart import record_stock_movement

    if Sale.query.first():
        return

    admin = User.query.filter_by(username='admin').first()
    products = Product.query.all()
    vendor = Partner.query.filter(Partner.is_supplier.is_(True)).first()
    customer = Partner.query.filter(Partner.is_customer.is_(True)).first()

    now = now_wib()

    for i in range(5):
        sale = Sale(
            sale_number=generate_number('SL', i),
            user_id=admin.id,
            subtotal=Decimal('33000'),
            discount=Decimal('0'),
            total=Decimal('33000'),
            created_at=now - timedelta(days=i),
        )
        db.session.add(sale)
        db.session.flush()

        p = products[i % len(products)]
        db.session.add(SaleLine(
            sale_id=sale.id,
            product_id=p.id,
            quantity=2,
            unit_price=p.price,
            line_total=Decimal(str(float(p.price) * 2)),
        ))
        record_stock_movement(p.id, 'out', 2, 'sale', sale.id)

    po = PurchaseOrder(
        po_number=generate_number('PO', 0),
        partner_id=vendor.id,
        status='completed',
        subtotal=Decimal('120000'),
        total=Decimal('120000'),
        created_at=now - timedelta(days=3),
    )
    db.session.add(po)
    db.session.flush()
    p = products[0]
    db.session.add(POLine(
        po_id=po.id,
        product_id=p.id,
        quantity=10,
        unit_cost=Decimal('12000'),
        line_total=Decimal('120000'),
    ))
    record_stock_movement(p.id, 'in', 10, 'po', po.id)

    inv = Invoice(
        invoice_number=generate_number('INV', 0),
        partner_id=customer.id,
        status='sent',
        subtotal=Decimal('36000'),
        total=Decimal('36000'),
        issue_date=now - timedelta(days=2),
        due_date=now + timedelta(days=12),
    )
    db.session.add(inv)
    db.session.flush()
    p = products[1]
    db.session.add(InvoiceLine(
        invoice_id=inv.id,
        product_id=p.id,
        quantity=2,
        unit_price=p.price,
        line_total=Decimal(str(float(p.price) * 2)),
    ))

    db.session.commit()
