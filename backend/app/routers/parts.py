from fastapi import APIRouter, Depends, HTTPException
from backend.app.security import get_current_admin

from backend.app.schemas.parts import (
    PartCreate,
    PartUpdate
)

from backend.app.services.parts import (
    create_part,
    get_all_parts,
    update_part,
    delete_part
)


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/parts")
def add_part(part: PartCreate):

    try:

        part_id = create_part(part)

        return {
            "message": "Part added successfully",
            "part_id": part_id
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/parts")
def get_parts():

    try:

        return get_all_parts()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/parts/{part_id}")
def edit_part(
    part_id: int,
    part: PartUpdate
):

    try:

        updated = update_part(
            part_id,
            part
        )

        if not updated:

            raise HTTPException(
                status_code=404,
                detail="Part not found"
            )

        return {
            "message": "Part updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("/parts/{part_id}")
def remove_part(part_id: int):

    try:

        deleted = delete_part(part_id)

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Part not found"
            )

        return {
            "message": "Part deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )