from fastapi import APIRouter, Depends, HTTPException
from backend.app.security import get_current_admin

from backend.app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate
)

from backend.app.services.vehicle import (
    create_vehicle,
    get_all_vehicles,
    update_vehicle,
    delete_vehicle
)


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/vehicles")
def add_vehicle(vehicle: VehicleCreate):

    try:

        vehicle_id = create_vehicle(vehicle)

        return {
            "message": "Vehicle added successfully",
            "vehicle_id": vehicle_id
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/vehicles")
def get_vehicles():

    try:

        return get_all_vehicles()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/vehicles/{vehicle_id}")
def edit_vehicle(
    vehicle_id: int,
    vehicle: VehicleUpdate
):

    try:

        updated = update_vehicle(
            vehicle_id,
            vehicle
        )

        if not updated:

            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        return {
            "message": "Vehicle updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("/vehicles/{vehicle_id}")
def remove_vehicle(vehicle_id: int):

    try:

        deleted = delete_vehicle(vehicle_id)

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        return {
            "message": "Vehicle deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )