from fastapi import APIRouter, Depends, HTTPException
from backend.app.security import get_current_admin

from backend.app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate
)

from backend.app.services.appointment import (
    create_appointment,
    get_all_appointments,
    update_appointment,
    delete_appointment
)


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/appointments")
def add_appointment(
    appointment: AppointmentCreate
):

    try:

        appointment_id = create_appointment(
            appointment
        )

        return {
            "message": "Appointment added successfully",
            "appointment_id": appointment_id
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/appointments")
def get_appointments():

    try:

        return get_all_appointments()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/appointments/{appointment_id}")
def edit_appointment(
    appointment_id: int,
    appointment: AppointmentUpdate
):

    try:

        updated = update_appointment(
            appointment_id,
            appointment
        )

        if not updated:

            raise HTTPException(
                status_code=404,
                detail="Appointment not found"
            )

        return {
            "message": "Appointment updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("/appointments/{appointment_id}")
def remove_appointment(
    appointment_id: int
):

    try:

        deleted = delete_appointment(
            appointment_id
        )

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Appointment not found"
            )

        return {
            "message": "Appointment deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )