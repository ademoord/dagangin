from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))


def now_wib():
    return datetime.now(WIB).replace(tzinfo=None)


def format_rupiah(amount):
    if amount is None:
        return 'Rp 0'
    return 'Rp {:,.0f}'.format(float(amount)).replace(',', '.')


ID_MONTHS = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
]


def format_date_id(dt, with_time=False):
    if not dt:
        return '-'
    if with_time:
        return '{} {} {} {:02d}:{:02d}'.format(
            dt.day, ID_MONTHS[dt.month - 1], dt.year, dt.hour, dt.minute,
        )
    return '{} {} {}'.format(dt.day, ID_MONTHS[dt.month - 1], dt.year)


def stock_status(product):
    if product.stock <= 0:
        return 'habis', 'Habis', 'danger'
    if product.stock <= product.low_stock_threshold:
        return 'low', 'Stok Rendah', 'warning'
    return 'ok', 'Aman', 'success'


def generate_number(prefix, last_id):
    return f'{prefix}-{datetime.now().strftime("%y%m")}-{last_id + 1:04d}'
