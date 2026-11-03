import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from backend.app.schemas.invoice import InvoiceCreate
from backend.app.services.invoice import create_invoice


class TestInvoiceService(unittest.TestCase):

    def test_discount_cannot_exceed_subtotal(self):
        # Mock the database connection: no real database is modified.
        connection = MagicMock()
        cursor = MagicMock()

        connection.cursor.return_value.__enter__.return_value = cursor

        # Simulate a completed appointment with a service price of 100.
        # The appointment has no existing invoice.
        cursor.fetchone.side_effect = [
            {
                "appointment_id": 1,
                "status": "Completed",
                "service_name": "Test Service",
                "price": Decimal("100.00"),
            },
            None,
        ]

        invoice_data = InvoiceCreate(
            appointment_id=1,
            discount_amount=Decimal("101.00"),
        )

        with patch(
            "backend.app.services.invoice.get_connection",
            return_value=connection,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Discount cannot exceed the subtotal",
            ):
                create_invoice(invoice_data)

        # The rejected invoice must not be committed.
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()

        # No invoice record should have been inserted.
        executed_queries = [
            str(call.args[0]).upper()
            for call in cursor.execute.call_args_list
        ]

        self.assertFalse(
            any("INSERT INTO INVOICES" in query
                for query in executed_queries)
        )


if __name__ == "__main__":
    unittest.main()
