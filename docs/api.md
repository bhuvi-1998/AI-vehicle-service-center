# API Reference

This document is generated from the FastAPI application's OpenAPI specification.

Local interactive API documentation: `http://127.0.0.1:8000/docs`

Base URL: `http://127.0.0.1:8000`

Protected endpoints require the authentication mechanism implemented by
the application. JWT-protected requests use an Authorization Bearer token.

## Endpoints

### `GET /`

**Purpose:** Home

**Responses:**

- `200` — Successful Response

### `PUT /admin-chatbot/appointments/{appointment_id}/schedule`

**Purpose:** Reschedule Admin Appointment

**Group:** Admin AI Assistant

**Parameters:**

- `appointment_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /admin-chatbot/appointments/{appointment_id}/status`

**Purpose:** Update Admin Appointment Status

**Group:** Admin AI Assistant

**Parameters:**

- `appointment_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /admin-chatbot/appointments/{appointment_id}/technician`

**Purpose:** Assign Admin Appointment Technician

**Group:** Admin AI Assistant

**Parameters:**

- `appointment_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /admin-chatbot/appointments/{appointment_id}/technician-recommendations`

**Purpose:** Recommend Appointment Technicians

**Group:** Admin AI Assistant

**Parameters:**

- `appointment_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /admin-chatbot/message`

**Purpose:** Admin Chatbot Message

**Group:** Admin AI Assistant

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /admin-chatbot/parts/{part_id}/stock`

**Purpose:** Adjust Admin Part Stock

**Group:** Admin AI Assistant

**Parameters:**

- `part_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /admin/login`

**Purpose:** Login Admin

**Group:** Admin Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /admin/me`

**Purpose:** Get Admin Profile

**Group:** Admin Authentication

**Responses:**

- `200` — Successful Response

### `PUT /admin/me`

**Purpose:** Update Admin Profile

**Group:** Admin Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /admins`

**Purpose:** Create Admin

**Group:** Admin Authentication

Bootstrap the first admin account only.
Once an admin exists, this public setup endpoint is disabled.

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /appointments`

**Purpose:** Get Appointments

**Responses:**

- `200` — Successful Response

### `POST /appointments`

**Purpose:** Add Appointment

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `DELETE /appointments/{appointment_id}`

**Purpose:** Remove Appointment

**Parameters:**

- `appointment_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /appointments/{appointment_id}`

**Purpose:** Edit Appointment

**Parameters:**

- `appointment_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /chatbot/message`

**Purpose:** Chatbot Message

**Group:** AI Chatbot

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /customer-auth/login`

**Purpose:** Login Customer

**Group:** Customer Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /customer-auth/me`

**Purpose:** Get Customer Profile

**Group:** Customer Authentication

**Responses:**

- `200` — Successful Response

### `PUT /customer-auth/me`

**Purpose:** Update Customer Profile

**Group:** Customer Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /customer-auth/register`

**Purpose:** Register Customer

**Group:** Customer Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /customer-auth/resend-verification`

**Purpose:** Resend Verification

**Group:** Customer Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /customer-auth/verify-email`

**Purpose:** Verify Customer Email

**Group:** Customer Authentication

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /customer-portal/appointments`

**Purpose:** List My Appointments

**Group:** Customer Portal

**Responses:**

- `200` — Successful Response

### `POST /customer-portal/appointments`

**Purpose:** Book My Service

**Group:** Customer Portal

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /customer-portal/appointments/{appointment_id}/cancel`

**Purpose:** Cancel My Appointment

**Group:** Customer Portal

**Parameters:**

- `appointment_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /customer-portal/appointments/{appointment_id}/reschedule`

**Purpose:** Reschedule My Appointment

**Group:** Customer Portal

**Parameters:**

- `appointment_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /customer-portal/services`

**Purpose:** List Booking Services

**Group:** Customer Portal

**Responses:**

- `200` — Successful Response

### `GET /customer-portal/vehicles`

**Purpose:** List My Vehicles

**Group:** Customer Portal

**Responses:**

- `200` — Successful Response

### `POST /customer-portal/vehicles`

**Purpose:** Add My Vehicle

**Group:** Customer Portal

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /customers`

**Purpose:** Get Customers

**Responses:**

- `200` — Successful Response

### `POST /customers`

**Purpose:** Add Customer

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `DELETE /customers/{customer_id}`

**Purpose:** Remove Customer

**Parameters:**

- `customer_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /customers/{customer_id}`

**Purpose:** Edit Customer

**Parameters:**

- `customer_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /estimates`

**Purpose:** List Estimates

**Responses:**

- `200` — Successful Response

### `POST /estimates`

**Purpose:** Add Estimate

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /estimates/{estimate_id}`

**Purpose:** Get Estimate

**Parameters:**

- `estimate_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /estimates/{estimate_id}/pdf`

**Purpose:** Download Estimate Pdf

**Parameters:**

- `estimate_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /invoices`

**Purpose:** List Invoices

**Responses:**

- `200` — Successful Response

### `POST /invoices`

**Purpose:** Add Invoice

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /invoices/{invoice_id}`

**Purpose:** Get Invoice

**Parameters:**

- `invoice_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /invoices/{invoice_id}/payment`

**Purpose:** Pay Invoice

**Parameters:**

- `invoice_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /invoices/{invoice_id}/pdf`

**Purpose:** Download Invoice Pdf

**Parameters:**

- `invoice_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /parts`

**Purpose:** Get Parts

**Responses:**

- `200` — Successful Response

### `POST /parts`

**Purpose:** Add Part

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `DELETE /parts/{part_id}`

**Purpose:** Remove Part

**Parameters:**

- `part_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /parts/{part_id}`

**Purpose:** Edit Part

**Parameters:**

- `part_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /password-reset/complete`

**Purpose:** Complete Password Reset

**Group:** Password Recovery

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `POST /password-reset/request`

**Purpose:** Request Password Reset

**Group:** Password Recovery

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /public/services`

**Purpose:** Get Public Services

**Group:** Public Services

**Responses:**

- `200` — Successful Response

### `GET /services`

**Purpose:** Get Services

**Responses:**

- `200` — Successful Response

### `POST /services`

**Purpose:** Add Service

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `DELETE /services/{service_id}`

**Purpose:** Remove Service

**Parameters:**

- `service_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /services/{service_id}`

**Purpose:** Edit Service

**Parameters:**

- `service_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /technicians`

**Purpose:** Get Technicians

**Responses:**

- `200` — Successful Response

### `POST /technicians`

**Purpose:** Add Technician

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `DELETE /technicians/{technician_id}`

**Purpose:** Remove Technician

**Parameters:**

- `technician_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /technicians/{technician_id}`

**Purpose:** Edit Technician

**Parameters:**

- `technician_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `GET /vehicles`

**Purpose:** Get Vehicles

**Responses:**

- `200` — Successful Response

### `POST /vehicles`

**Purpose:** Add Vehicle

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `DELETE /vehicles/{vehicle_id}`

**Purpose:** Remove Vehicle

**Parameters:**

- `vehicle_id` (path, required)

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

### `PUT /vehicles/{vehicle_id}`

**Purpose:** Edit Vehicle

**Parameters:**

- `vehicle_id` (path, required)

**Request body:**

- `application/json`

**Responses:**

- `200` — Successful Response
- `422` — Validation Error

## Notes

- The interactive Swagger UI displays the request and response schemas.
- Authentication requirements and authorization rules are enforced by the backend.
- Do not assume that an endpoint is publicly accessible merely because it appears here.
