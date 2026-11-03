from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.security import get_current_admin

from backend.app.schemas.invoice import (
    InvoiceCreate,
    InvoicePaymentUpdate
)

from backend.app.services.invoice import (
    create_invoice,
    get_all_invoices,
    get_invoice_details,
    mark_invoice_paid
)

from backend.app.services.invoice_pdf import create_invoice_pdf


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)

@router.post("/invoices")
def add_invoice(data: InvoiceCreate):

    try:
        invoice_id = create_invoice(data)

        return {
            "message": "Final invoice created successfully.",
            "invoice_id": invoice_id
        }

    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to create invoice. Check the backend logs."
        )


@router.get("/invoices")
def list_invoices():

    try:
        return get_all_invoices()

    except Exception as error:
        print("Invoice loading error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to load invoices."
        )

@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):

    invoice = get_invoice_details(invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    return invoice


@router.put("/invoices/{invoice_id}/payment")
def pay_invoice(invoice_id: int, data: InvoicePaymentUpdate):

    try:
        mark_invoice_paid(invoice_id, data.payment_method)

        return {
            "message": "Invoice marked as paid.",
            "invoice_id": invoice_id,
            "payment_method": data.payment_method,
            "payment_status": "Paid"
        }

    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to update invoice payment."
        )


@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int):

    invoice = get_invoice_details(invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    pdf_buffer = create_invoice_pdf(invoice)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="invoice-{invoice_id}.pdf"'
        }
    )