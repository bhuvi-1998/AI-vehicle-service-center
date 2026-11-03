from fastapi import APIRouter, Depends, HTTPException
from backend.app.security import get_current_admin

from backend.app.schemas.customer import CustomerCreate, CustomerUpdate
from backend.app.services.customer import (
    create_customer,
    get_all_customers,
    update_customer,
    delete_customer
)


router = APIRouter(
    dependencies=[Depends(get_current_admin)]
)


@router.post("/customers")
def add_customer(customer: CustomerCreate):

    try:
        customer_id = create_customer(customer)

        return {
            "message": "Customer added successfully",
            "customer_id": customer_id
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/customers")
def get_customers():

    try:
        return get_all_customers()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/customers/{customer_id}")
def edit_customer(
    customer_id: int,
    customer: CustomerUpdate
):

    try:
        updated = update_customer(
            customer_id,
            customer
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

        return {
            "message": "Customer updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("/customers/{customer_id}")
def remove_customer(customer_id: int):

    try:
        deleted = delete_customer(customer_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

        return {
            "message": "Customer deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )