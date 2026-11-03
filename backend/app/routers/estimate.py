from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.security import get_current_admin

from backend.app.schemas.estimate import EstimateCreate
from backend.app.services.estimate import (
    create_estimate,
    get_all_estimates,
    get_estimate_details
)
from backend.app.services.estimate_pdf import create_estimate_pdf


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/estimates")
def add_estimate(data: EstimateCreate):

    try:
        estimate_id = create_estimate(data)

        return {
            "message": "Service estimate created successfully.",
            "estimate_id": estimate_id
        }

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to create the estimate. Check the backend logs."
        )


@router.get("/estimates")
def list_estimates():

    try:
        return get_all_estimates()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to load estimates."
        )


@router.get("/estimates/{estimate_id}")
def get_estimate(estimate_id: int):

    estimate = get_estimate_details(estimate_id)

    if not estimate:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found."
        )

    return estimate


@router.get("/estimates/{estimate_id}/pdf")
def download_estimate_pdf(estimate_id: int):

    estimate = get_estimate_details(estimate_id)

    if not estimate:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found."
        )

    pdf_buffer = create_estimate_pdf(estimate)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="service-estimate-{estimate_id}.pdf"'
        }
    )