from fastapi import APIRouter, Depends, HTTPException
from backend.app.security import get_current_admin

from backend.app.schemas.technician import (
    TechnicianCreate,
    TechnicianUpdate
)

from backend.app.services.technician import (
    create_technician,
    get_all_technicians,
    update_technician,
    delete_technician
)


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/technicians")
def add_technician(technician: TechnicianCreate):

    try:

        technician_id = create_technician(technician)

        return {
            "message": "Technician added successfully",
            "technician_id": technician_id
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/technicians")
def get_technicians():

    try:

        return get_all_technicians()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/technicians/{technician_id}")
def edit_technician(
    technician_id: int,
    technician: TechnicianUpdate
):

    try:

        updated = update_technician(
            technician_id,
            technician
        )

        if not updated:

            raise HTTPException(
                status_code=404,
                detail="Technician not found"
            )

        return {
            "message": "Technician updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("/technicians/{technician_id}")
def remove_technician(technician_id: int):

    try:

        deleted = delete_technician(technician_id)

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Technician not found"
            )

        return {
            "message": "Technician deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )