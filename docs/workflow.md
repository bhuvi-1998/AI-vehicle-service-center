# Application Workflow

## Main Components

The application has a browser-based frontend, a FastAPI backend,
a MySQL database, and optional integrations for email, PDF creation
and local AI assistance.

## Customer Workflow

1. A customer registers an account.
2. The application sends an email-verification message.
3. The customer verifies the email address and logs in.
4. The customer registers or selects a vehicle.
5. The customer selects an available service and requests an appointment.
6. The customer views appointment details and status in the portal.
7. The customer uses permitted booking-management options.
8. The customer can ask the customer assistant about supported records.

## Administrator Workflow

1. The administrator signs in.
2. The administrator manages customer, vehicle, service and technician records.
3. The administrator reviews incoming appointments.
4. The administrator confirms appointments and updates their status
   through allowed transitions.
5. The administrator assigns a suitable technician.
6. The administrator manages spare-parts stock.
7. The administrator prepares an estimate where required.
8. After service completion, the administrator creates the final invoice.
9. The invoice workflow validates and deducts included parts from stock.
10. The administrator records the payment method and payment status.
11. The administrator reviews business and inventory summaries.

## Appointment Status Flow

```text
Pending
   |
   v
Confirmed
   |
   v
Vehicle Received
   |
   v
In Progress
   |
   v
Ready for Pickup
   |
   v
Completed
```

Pending and Confirmed appointments may also be cancelled through
the permitted cancellation workflow.

## AI Assistant

The customer and administrator assistants use separate authorization
and backend workflows.

The backend must validate permissions and business rules before
performing an operation. Operations that change records require
the application's confirmation flow where implemented.

The assistant's available actions are limited to those implemented
by the application. It should not be treated as unrestricted database
or operating-system access.

## Supporting Services

- FastAPI exposes the backend API.
- MySQL stores application records.
- SMTP supports verification and password-recovery emails.
- ReportLab generates PDF documents.
- Ollama provides local model inference for the AI assistant.
