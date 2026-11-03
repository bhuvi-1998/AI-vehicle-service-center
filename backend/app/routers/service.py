from fastapi import APIRouter, Depends, HTTPException
from backend.app.security import get_current_admin

from backend.app.schemas.service import (
    ServiceCreate,
    ServiceUpdate
)

from backend.app.services.service import (
    create_service,
    get_all_services,
    update_service,
    delete_service
)


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/services")
def add_service(service: ServiceCreate):

    try:

        service_id = create_service(service)

        return {
            "message": "Service added successfully",
            "service_id": service_id
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/services")
def get_services():

    try:

        return get_all_services()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/services/{service_id}")
def edit_service(
    service_id: int,
    service: ServiceUpdate
):

    try:

        updated = update_service(
            service_id,
            service
        )

        if not updated:

            raise HTTPException(
                status_code=404,
                detail="Service not found"
            )

        return {
            "message": "Service updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("/services/{service_id}")
def remove_service(service_id: int):

    try:

        deleted = delete_service(service_id)

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Service not found"
            )

        return {
            "message": "Service deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )