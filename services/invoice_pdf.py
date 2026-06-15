import io

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from helpers import format_rupiah


DAGANGIN_GREEN = colors.HexColor('#2F645C')
DAGANGIN_MINT = colors.HexColor('#6FC0C6')
DAGANGIN_LIGHT = colors.HexColor('#E9F5F1')


def _fmt_date(dt):
    if not dt:
        return '-'
    months = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
    ]
    return '{} {} {}'.format(dt.day, months[dt.month - 1], dt.year)


def build_invoice_pdf(invoice):
    """Generate invoice PDF bytes for the given Invoice model."""
    buffer = io.BytesIO()
    business_name = current_app.config.get('BUSINESS_NAME', 'Dagangin')
    customer = invoice.partner

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title='Invoice {}'.format(invoice.invoice_number),
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=DAGANGIN_GREEN,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#5A5C5B'),
        spaceAfter=12,
    )
    greeting_style = ParagraphStyle(
        'Greeting',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=DAGANGIN_GREEN,
        spaceBefore=8,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
    )
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=colors.HexColor('#5A5C5B'),
        alignment=TA_CENTER,
        spaceBefore=16,
    )

    story = []

    story.append(Paragraph(business_name, title_style))
    story.append(Paragraph('Tagihan Pelanggan', subtitle_style))

    greeting = (
        'Hai <b>{}</b>, berikut tagihanmu ya! '
        'Silakan dicek detail pesanan di bawah ini.'
    ).format(customer.name)
    story.append(Paragraph(greeting, greeting_style))

    meta_data = [
        ['No. Faktur', invoice.invoice_number],
        ['Tanggal Tagihan', _fmt_date(invoice.issue_date)],
        ['Jatuh Tempo', _fmt_date(invoice.due_date)],
    ]
    meta_table = Table(meta_data, colWidths=[35 * mm, 120 * mm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), DAGANGIN_GREEN),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph('Data Pelanggan', section_style))
    customer_lines = [
        '<b>Nama:</b> {}'.format(customer.name),
    ]
    if customer.phone:
        customer_lines.append('<b>No. HP:</b> {}'.format(customer.phone))
    else:
        customer_lines.append('<b>No. HP:</b> -')
    if customer.address:
        customer_lines.append('<b>Alamat:</b> {}'.format(customer.address.replace('\n', ', ')))
    else:
        customer_lines.append('<b>Alamat:</b> -')

    for line in customer_lines:
        story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph('Rincian Pesanan', section_style))

    table_header = ['Barang', 'Harga/Unit', 'Jumlah', 'Subtotal']
    table_rows = [table_header]

    for line in invoice.lines:
        product_name = line.product.name if line.product else 'Produk'
        unit = line.product.unit if line.product and line.product.unit else 'pcs'
        table_rows.append([
            product_name,
            format_rupiah(line.unit_price),
            '{} {}'.format(line.quantity, unit),
            format_rupiah(line.line_total),
        ])

    items_table = Table(
        table_rows,
        colWidths=[70 * mm, 35 * mm, 25 * mm, 35 * mm],
        repeatRows=1,
    )
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DAGANGIN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, DAGANGIN_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#C7E8ED')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    total_qty = sum(line.quantity for line in invoice.lines)
    summary_rows = [
        ['Total Kuantitas', '{} item'.format(total_qty)],
        ['Total Tagihan', format_rupiah(invoice.total)],
    ]
    summary_table = Table(summary_rows, colWidths=[120 * mm, 45 * mm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), DAGANGIN_GREEN),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, DAGANGIN_MINT),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)

    if invoice.notes:
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            '<b>Catatan:</b> {}'.format(invoice.notes),
            body_style,
        ))

    story.append(Paragraph(
        'Kalau ada yang perlu ditanyakan, langsung hubungi kami aja ya. '
        'Terima kasih sudah order — sukses terus dagangnya!',
        footer_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
