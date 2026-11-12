
import unittest

from pydantic import ValidationError

from backend.app.schemas.customer import CustomerCreate, CustomerUpdate
from backend.app.schemas.vehicle import VehicleCreate, VehicleUpdate
from backend.app.schemas.service import ServiceCreate, ServiceUpdate
from backend.app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
)
from backend.app.schemas.parts import PartCreate, PartUpdate
from backend.app.schemas.estimate import EstimateCreate, EstimatePartInput
from backend.app.schemas.invoice import (
    InvoiceCreate,
    InvoicePartInput,
    InvoicePaymentUpdate,
)


class TestCustomerSchemas(unittest.TestCase):

    def test_valid_customer(self):
        customer = CustomerCreate(
            customer_name="Test Customer",
            phone="9000000000",
            email="customer@example.com",
            address="Test address",
        )
        self.assertEqual(customer.customer_name, "Test Customer")

    def test_optional_customer_fields(self):
        customer = CustomerCreate(
            customer_name="Test Customer",
            phone="9000000000",
        )
        self.assertIsNone(customer.email)
        self.assertIsNone(customer.address)

    def test_missing_required_customer_field(self):
        with self.assertRaises(ValidationError):
            CustomerCreate(customer_name="Test Customer")

    def test_customer_update(self):
        customer = CustomerUpdate(
            customer_name="Updated Customer",
            phone="9000000001",
        )
        self.assertEqual(customer.phone, "9000000001")


class TestVehicleSchemas(unittest.TestCase):

    def test_valid_vehicle_categories(self):
        for category in ("Car", "Bike", "Superbike"):
            with self.subTest(category=category):
                vehicle = VehicleCreate(
                    customer_id=1,
                    vehicle_number="TEST123",
                    brand="Test Brand",
                    model="Test Model",
                    vehicle_type=category,
                )
                self.assertEqual(vehicle.vehicle_type, category)

    def test_invalid_vehicle_category(self):
        with self.assertRaises(ValidationError):
            VehicleCreate(
                customer_id=1,
                vehicle_number="TEST123",
                brand="Test Brand",
                model="Test Model",
                vehicle_type="Truck",
            )

    def test_default_vehicle_category(self):
        vehicle = VehicleCreate(
            customer_id=1,
            vehicle_number="TEST123",
            brand="Test Brand",
            model="Test Model",
        )
        self.assertEqual(vehicle.vehicle_type, "Car")

    def test_vehicle_update(self):
        vehicle = VehicleUpdate(
            customer_id=1,
            vehicle_number="TEST124",
            brand="Test Brand",
            model="Updated Model",
            vehicle_type="Bike",
        )
        self.assertEqual(vehicle.vehicle_type, "Bike")


class TestServiceSchemas(unittest.TestCase):

    def test_valid_service(self):
        service = ServiceCreate(
            service_name="Oil Change",
            description="Oil replacement service",
            price=500,
            vehicle_type="Car",
        )
        self.assertEqual(service.price, 500)

    def test_invalid_service_category(self):
        with self.assertRaises(ValidationError):
            ServiceCreate(
                service_name="Test Service",
                price=500,
                vehicle_type="Truck",
            )

    def test_service_update(self):
        service = ServiceUpdate(
            service_name="Updated Service",
            price=600,
            vehicle_type="Bike",
        )
        self.assertEqual(service.price, 600)


class TestAppointmentSchemas(unittest.TestCase):

    def test_valid_appointment(self):
        appointment = AppointmentCreate(
            customer_id=1,
            vehicle_id=1,
            service_id=1,
            appointment_date="2030-01-15",
            appointment_time="10:30",
        )
        self.assertEqual(str(appointment.appointment_date), "2030-01-15")

    def test_invalid_appointment_date(self):
        with self.assertRaises(ValidationError):
            AppointmentCreate(
                customer_id=1,
                vehicle_id=1,
                service_id=1,
                appointment_date="not-a-date",
                appointment_time="10:30",
            )

    def test_invalid_appointment_status(self):
        with self.assertRaises(ValidationError):
            AppointmentUpdate(
                customer_id=1,
                vehicle_id=1,
                service_id=1,
                appointment_date="2030-01-15",
                appointment_time="10:30",
                status="Unknown Status",
            )

    def test_valid_appointment_status(self):
        appointment = AppointmentUpdate(
            customer_id=1,
            vehicle_id=1,
            service_id=1,
            appointment_date="2030-01-15",
            appointment_time="10:30",
            status="Confirmed",
        )
        self.assertEqual(appointment.status, "Confirmed")


class TestPartsSchemas(unittest.TestCase):

    def test_valid_part_for_all_categories(self):
        part = PartCreate(
            part_name="Brake Pad",
            part_number="TEST-BP-001",
            quantity=5,
            price=1200,
            vehicle_type="All",
        )
        self.assertEqual(part.vehicle_type, "All")

    def test_invalid_part_category(self):
        with self.assertRaises(ValidationError):
            PartCreate(
                part_name="Test Part",
                part_number="TEST-001",
                quantity=5,
                price=100,
                vehicle_type="Truck",
            )

    def test_part_update(self):
        part = PartUpdate(
            part_name="Updated Part",
            part_number="TEST-002",
            quantity=10,
            price=200,
            vehicle_type="Bike",
        )
        self.assertEqual(part.quantity, 10)


class TestEstimateSchemas(unittest.TestCase):

    def test_valid_estimate(self):
        estimate = EstimateCreate(
            appointment_id=1,
            parts=[{"part_id": 1, "quantity": 2}],
        )
        self.assertEqual(estimate.parts[0].quantity, 2)

    def test_estimate_rejects_zero_quantity(self):
        with self.assertRaises(ValidationError):
            EstimatePartInput(part_id=1, quantity=0)

    def test_estimate_rejects_negative_part_id(self):
        with self.assertRaises(ValidationError):
            EstimatePartInput(part_id=-1, quantity=1)

    def test_estimate_rejects_invalid_appointment_id(self):
        with self.assertRaises(ValidationError):
            EstimateCreate(appointment_id=0)


class TestInvoiceSchemas(unittest.TestCase):

    def test_valid_invoice(self):
        invoice = InvoiceCreate(
            appointment_id=1,
            parts=[{"part_id": 1, "quantity": 2}],
            discount_amount="0.00",
        )
        self.assertEqual(invoice.parts[0].quantity, 2)

    def test_invoice_rejects_zero_quantity(self):
        with self.assertRaises(ValidationError):
            InvoicePartInput(part_id=1, quantity=0)

    def test_invoice_rejects_negative_quantity(self):
        with self.assertRaises(ValidationError):
            InvoicePartInput(part_id=1, quantity=-1)

    def test_invoice_rejects_negative_discount(self):
        with self.assertRaises(ValidationError):
            InvoiceCreate(
                appointment_id=1,
                discount_amount="-1.00",
            )

    def test_invoice_rejects_invalid_payment_method(self):
        with self.assertRaises(ValidationError):
            InvoicePaymentUpdate(payment_method="Cheque")


if __name__ == "__main__":
    unittest.main()
