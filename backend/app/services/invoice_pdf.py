from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def create_invoice_pdf(invoice):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "InvoiceHeading",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6
    )

    bold_style = ParagraphStyle(
        "InvoiceBold",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold"
    )

    right_style = ParagraphStyle(
        "InvoiceRight",
        parent=styles["BodyText"],
        alignment=TA_RIGHT
    )

    def p(value, style=None):
        return Paragraph(
            escape("" if value is None else str(value)),
            style or styles["BodyText"]
        )

    def amount(value):
        return f"INR {float(value):,.2f}"

    def date_text(value):
        return str(value) if value is not None else ""

    story = []

    story.append(p("Vehicle Service Center", title_style))
    story.append(p("FINAL INVOICE / BILL", title_style))

    story.append(p(f"Invoice Number: {invoice['invoice_id']}"))
    story.append(p(f"Invoice Date: {date_text(invoice['invoice_date'])}"))
    story.append(p(f"Appointment Number: {invoice['appointment_id']}"))

    story.append(p("Customer and Vehicle Details", heading_style))

    details = [
        [
            p("Customer", bold_style),
            p(invoice["customer_name"]),
            p("Phone", bold_style),
            p(invoice["customer_phone"])
        ],
        [
            p("Email", bold_style),
            p(invoice["customer_email"]),
            p("Address", bold_style),
            p(invoice["customer_address"])
        ],
        [
            p("Vehicle Number", bold_style),
            p(invoice["vehicle_number"]),
            p("Vehicle", bold_style),
            p(f"{invoice['brand']} {invoice['model']}")
        ],
        [
            p("Appointment Date", bold_style),
            p(date_text(invoice["appointment_date"])),
            p("Payment Status", bold_style),
            p(invoice["payment_status"])
        ],
        [
            p("Payment Method", bold_style),
            p(invoice["payment_method"]),
            p("Service", bold_style),
            p(invoice["service_name"])
        ]
    ]

    details_table = Table(
        details,
        colWidths=[25 * mm, 45 * mm, 27 * mm, 73 * mm]
    )

    details_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(details_table)

    story.append(p("Service Charges", heading_style))

    service_table = Table(
        [
            [
                p("Service", bold_style),
                p("Amount", bold_style)
            ],
            [
                p(invoice["service_name"]),
                p(amount(invoice["service_amount"]), right_style)
            ]
        ],
        colWidths=[115 * mm, 55 * mm]
    )

    service_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(service_table)

    story.append(p("Parts Used", heading_style))

    parts_rows = [[
        p("Part", bold_style),
        p("Part Number", bold_style),
        p("Quantity", bold_style),
        p("Unit Price", bold_style),
        p("Amount", bold_style)
    ]]

    for part in invoice["parts"]:
        parts_rows.append([
            p(part["part_name"]),
            p(part["part_number"]),
            p(part["quantity"]),
            p(amount(part["unit_price"]), right_style),
            p(amount(part["line_total"]), right_style)
        ])

    if not invoice["parts"]:
        parts_rows.append([
            p("No parts charged"),
            p(""),
            p(""),
            p(""),
            p("")
        ])

    parts_table = Table(
        parts_rows,
        colWidths=[48 * mm, 27 * mm, 20 * mm, 37 * mm, 33 * mm],
        repeatRows=1
    )

    parts_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(parts_table)
    story.append(Spacer(1, 12))

    totals = Table(
        [
            [
                p("Service Amount", bold_style),
                p(amount(invoice["service_amount"]), right_style)
            ],
            [
                p("Parts Amount", bold_style),
                p(amount(invoice["parts_amount"]), right_style)
            ],
            [
                p("Discount", bold_style),
                p(amount(invoice["discount_amount"]), right_style)
            ],
            [
                p("Final Total", bold_style),
                p(amount(invoice["total_amount"]), right_style)
            ]
        ],
        colWidths=[115 * mm, 55 * mm]
    )

    totals.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 3), (-1, 3), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(totals)

    if invoice.get("notes"):
        story.append(p("Notes", heading_style))
        story.append(p(invoice["notes"]))

    story.append(Spacer(1, 16))
    story.append(p("Thank you for choosing our service center."))

    document.build(story)

    buffer.seek(0)

    return buffer