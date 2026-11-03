import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class TestAPISmoke(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_home_endpoint(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Vehicle Service Center API",
        )

    def test_password_reset_routes_are_registered(self):
        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)

        paths = response.json()["paths"]

        self.assertIn("/password-reset/request", paths)
        self.assertIn("/password-reset/complete", paths)

    def test_password_reset_rejects_invalid_account_type(self):
        response = self.client.post(
            "/password-reset/request",
            json={
                "email": "test@example.com",
                "account_type": "unauthorized",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_password_reset_rejects_short_password(self):
        response = self.client.post(
            "/password-reset/complete",
            json={
                "token": "invalid-test-token-123456789",
                "new_password": "123",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_vehicle_api_requires_admin_authentication(self):
        response = self.client.get("/vehicles")

        self.assertIn(response.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()