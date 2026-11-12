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


def create_estimate_pdf(estimate):

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
        "EstimateTitle",
        parent=styles["Title"],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=5
    )

    subtitle_style = ParagraphStyle(
        "EstimateSubtitle",
        parent=styles["Heading2"],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "EstimateHeading",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6
    )

    right_style = ParagraphStyle(
        "RightAligned",
        parent=styles["BodyText"],
        alignment=TA_RIGHT
    )

    bold_style = ParagraphStyle(
        "BoldText",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold"
    )

    def paragraph(value, style=None):
        text = "" if value is None else str(value)

        return Paragraph(
            escape(text),
            style or styles["BodyText"]
        )

    def amount(value):
        return f"INR {float(value):,.2f}"

    def date_text(value):
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M") \
                if hasattr(value, "hour") else value.strftime("%Y-%m-%d")

        return str(value or "")

    story = []

    story.append(
        paragraph("Vehicle Service Center", title_style)
    )

    story.append(
        paragraph("SERVICE ESTIMATE", subtitle_style)
    )

    story.append(
        paragraph(
            f"Estimate Number: {estimate['estimate_id']}"
        )
    )

    story.append(
        paragraph(
            f"Estimate Date: {date_text(estimate['estimate_date'])}"
        )
    )

    story.append(Spacer(1, 6))

    story.append(
        paragraph("Customer and Vehicle Details", heading_style)
    )

    details = [
        [
            paragraph("Customer", bold_style),
            paragraph(estimate["customer_name"]),
            paragraph("Phone", bold_style),
            paragraph(estimate["customer_phone"])
        ],
        [
            paragraph("Email", bold_style),
            paragraph(estimate["customer_email"]),
            paragraph("Address", bold_style),
            paragraph(estimate["customer_address"])
        ],
        [
            paragraph("Appointment", bold_style),
            paragraph(estimate["appointment_id"]),
            paragraph("Appointment Date", bold_style),
            paragraph(
                date_text(estimate["appointment_date"])
            )
        ],
        [
            paragraph("Vehicle Number", bold_style),
            paragraph(estimate["vehicle_number"]),
            paragraph("Vehicle", bold_style),
            paragraph(
                f"{estimate['brand']} {estimate['model']}"
            )
        ]
    ]

    details_table = Table(
        details,
        colWidths=[26 * mm, 48 * mm, 32 * mm, 49 * mm]
    )

    details_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(details_table)

    story.append(
        paragraph("Service", heading_style)
    )

    service_table = Table(
        [
            [
                paragraph("Description", bold_style),
                paragraph("Estimated Amount", bold_style)
            ],
            [
                paragraph(estimate["service_name"]),
                paragraph(
                    amount(estimate["service_amount"]),
                    right_style
                )
            ]
        ],
        colWidths=[100 * mm, 55 * mm]
    )

    service_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(service_table)

    story.append(
        paragraph("Parts", heading_style)
    )

    parts_rows = [[
        paragraph("Part", bold_style),
        paragraph("Part Number", bold_style),
        paragraph("Qty", bold_style),
        paragraph("Unit Price", bold_style),
        paragraph("Amount", bold_style)
    ]]

    for part in estimate["parts"]:

        parts_rows.append([
            paragraph(part["part_name"]),
            paragraph(part["part_number"]),
            paragraph(part["quantity"]),
            paragraph(amount(part["unit_price"]), right_style),
            paragraph(amount(part["line_total"]), right_style)
        ])

    if not estimate["parts"]:
        parts_rows.append([
            paragraph("No parts included in this estimate."),
            paragraph(""),
            paragraph(""),
            paragraph(""),
            paragraph("")
        ])

    parts_table = Table(
        parts_rows,
        colWidths=[
            43 * mm,
            32 * mm,
            13 * mm,
            32 * mm,
            35 * mm
        ],
        repeatRows=1
    )

    parts_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (4, -1), "RIGHT"),
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
                paragraph("Service Amount", bold_style),
                paragraph(
                    amount(estimate["service_amount"]),
                    right_style
                )
            ],
            [
                paragraph("Parts Amount", bold_style),
                paragraph(
                    amount(estimate["parts_amount"]),
                    right_style
                )
            ],
            [
                paragraph("Estimated Total", bold_style),
                paragraph(
                    amount(estimate["total_amount"]),
                    right_style
                )
            ]
        ],
        colWidths=[100 * mm, 55 * mm]
    )

    totals.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 2), (-1, 2), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(totals)

    if estimate.get("notes"):
        story.append(
            paragraph("Notes", heading_style)
        )

        story.append(
            paragraph(estimate["notes"])
        )

    story.append(Spacer(1, 16))

    story.append(
        paragraph(
            "This document is a service estimate, not a final invoice. "
            "Final charges may change based on the work approved and "
            "the parts actually used."
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer