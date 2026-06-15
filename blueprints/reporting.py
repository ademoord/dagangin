from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from sqlalchemy import func

from config import db
from helpers import format_rupiah, now_wib
from models import Product, Partner, PurchaseOrder, Sale, SaleLine, StockMovement

reporting_bp = Blueprint('reporting', __name__, url_prefix='/reporting')


def _date_range():
    period = request.args.get('period', '30')
    end = now_wib().replace(hour=23, minute=59, second=59)
    if period == '7':
        start = end - timedelta(days=6)
    elif period == 'month':
        start = end.replace(day=1, hour=0, minute=0, second=0)
    else:
        start = end - timedelta(days=29)
    start = start.replace(hour=0, minute=0, second=0)
    return start, end


def _compute_kpis(start, end):
    sales = Sale.query.filter(Sale.created_at >= start, Sale.created_at <= end).all()
    total_sales = sum(float(s.total or 0) for s in sales)
    order_count = len(sales)
    avg_tx = total_sales / order_count if order_count else 0

    gross_profit = Decimal('0')
    for sale in sales:
        for line in sale.lines:
            cost = float(line.product.cost or 0) if line.product else 0
            gross_profit += Decimal(str(float(line.line_total) - cost * line.quantity))

    prev_start = start - (end - start) - timedelta(seconds=1)
    prev_end = start - timedelta(seconds=1)
    prev_sales = Sale.query.filter(Sale.created_at >= prev_start, Sale.created_at <= prev_end).all()
    prev_total = sum(float(s.total or 0) for s in prev_sales)
    prev_count = len(prev_sales)
    prev_avg = prev_total / prev_count if prev_count else 0
    prev_profit = Decimal('0')
    for sale in prev_sales:
        for line in sale.lines:
            cost = float(line.product.cost or 0) if line.product else 0
            prev_profit += Decimal(str(float(line.line_total) - cost * line.quantity))

    def pct_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    return {
        'total_sales': total_sales,
        'sales_change': pct_change(total_sales, prev_total),
        'gross_profit': float(gross_profit),
        'profit_change': pct_change(float(gross_profit), float(prev_profit)),
        'order_count': order_count,
        'orders_change': pct_change(order_count, prev_count),
        'avg_transaction': avg_tx,
        'avg_change': pct_change(avg_tx, prev_avg),
    }


@reporting_bp.route('/')
@login_required
def index():
    start, end = _date_range()
    kpis = _compute_kpis(start, end)
    period = request.args.get('period', '30')

    return render_template(
        'reporting/index.html',
        title='Laporan',
        kpis=kpis,
        period=period,
        start=start,
        end=end,
    )


@reporting_bp.route('/api/sales-chart')
@login_required
def sales_chart():
    start, end = _date_range()
    days = (end.date() - start.date()).days + 1
    labels = []
    values = []

    for i in range(days):
        day = start.date() + timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        total = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(
            Sale.created_at >= day_start,
            Sale.created_at <= day_end,
        ).scalar()
        labels.append(day.strftime('%d/%m'))
        values.append(float(total or 0))

    return jsonify({'labels': labels, 'values': values})


@reporting_bp.route('/api/stock-chart')
@login_required
def stock_chart():
    start, end = _date_range()
    top_products = db.session.query(
        Product.name,
        func.sum(case_qty('in')).label('stock_in'),
        func.sum(case_qty('out')).label('stock_out'),
    ).join(StockMovement).filter(
        StockMovement.created_at >= start,
        StockMovement.created_at <= end,
    ).group_by(Product.id).order_by(
        func.sum(StockMovement.quantity).desc()
    ).limit(5).all()

    labels = [row[0] for row in top_products]
    stock_in = [float(row[1] or 0) for row in top_products]
    stock_out = [float(row[2] or 0) for row in top_products]

    return jsonify({'labels': labels, 'stock_in': stock_in, 'stock_out': stock_out})


def case_qty(movement_type):
    from sqlalchemy import case
    return case(
        (StockMovement.movement_type == movement_type, StockMovement.quantity),
        else_=0,
    )


@reporting_bp.route('/api/purchase-chart')
@login_required
def purchase_chart():
    start, end = _date_range()
    rows = db.session.query(
        Partner.name,
        func.coalesce(func.sum(PurchaseOrder.total), 0),
    ).join(PurchaseOrder).filter(
        PurchaseOrder.created_at >= start,
        PurchaseOrder.created_at <= end,
        PurchaseOrder.status != 'cancelled',
    ).group_by(Partner.id).all()

    return jsonify({
        'labels': [r[0] for r in rows],
        'values': [float(r[1] or 0) for r in rows],
    })


@reporting_bp.route('/api/sparkline/<metric>')
@login_required
def sparkline(metric):
    start, end = _date_range()
    days = min(7, (end.date() - start.date()).days + 1)
    values = []

    for i in range(days):
        day = (end.date() - timedelta(days=days - 1 - i))
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        if metric == 'sales':
            val = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(
                Sale.created_at >= day_start, Sale.created_at <= day_end,
            ).scalar()
        elif metric == 'orders':
            val = Sale.query.filter(
                Sale.created_at >= day_start, Sale.created_at <= day_end,
            ).count()
        elif metric == 'profit':
            val = 0
            for sale in Sale.query.filter(Sale.created_at >= day_start, Sale.created_at <= day_end).all():
                for line in sale.lines:
                    cost = float(line.product.cost or 0) if line.product else 0
                    val += float(line.line_total) - cost * line.quantity
        else:
            sales = Sale.query.filter(Sale.created_at >= day_start, Sale.created_at <= day_end).all()
            val = sum(float(s.total or 0) for s in sales) / len(sales) if sales else 0

        values.append(float(val or 0))

    return jsonify({'values': values})


@reporting_bp.route('/export')
@login_required
def export_csv():
    import csv
    import io
    from flask import Response

    start, end = _date_range()
    sales = Sale.query.filter(Sale.created_at >= start, Sale.created_at <= end).order_by(Sale.created_at).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['No Transaksi', 'Tanggal', 'Subtotal', 'Diskon', 'Total'])
    for sale in sales:
        writer.writerow([
            sale.sale_number,
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
            float(sale.subtotal or 0),
            float(sale.discount or 0),
            float(sale.total or 0),
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=dagangin-sales.csv'},
    )
