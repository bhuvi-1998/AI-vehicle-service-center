# Database Design

Database name: `vehicle_service_center`

The project includes separate fresh-install schemas:
- PostgreSQL: database/schema.postgresql.sql
- MySQL: database/schema.sql

The tables below describe the application's data model.

## Tables

| Table | Purpose |
|---|---|
| `admins` | Administrator login accounts and roles |
| `customers` | Customer contact details, login and email-verification information |
| `services` | Services offered by the center and their prices |
| `technicians` | Technician details, specialization and supported vehicle category |
| `vehicles` | Vehicles registered by customers |
| `parts` | Spare-parts inventory and available quantities |
| `appointments` | Customer bookings, assigned technicians, date, time and status |
| `estimates` | Service estimates associated with appointments |
| `estimate_parts` | Spare-part line items included in an estimate |
| `invoices` | Final invoice and payment information |
| `invoice_parts` | Spare-part line items included in an invoice |
| `password_reset_tokens` | Hashed, expiring password-reset tokens |

## Main Relationships

- One customer can register multiple vehicles.
- One customer can create multiple appointments.
- One vehicle can be associated with multiple appointments.
- One service can be selected for multiple appointments.
- One technician can be assigned to multiple appointments.
- An appointment can have multiple estimates.
- An estimate can contain multiple estimate-part rows.
- An appointment can have at most one final invoice.
- An invoice can contain multiple invoice-part rows.
- A part can appear in multiple estimate and invoice line items.

`password_reset_tokens.account_id` is polymorphic: `account_type`
indicates whether the account belongs to an administrator or customer.
It does not use a conventional foreign key to either account table.

## Vehicle Categories

The `vehicle_type` columns support vehicle-category matching in:

- `services`
- `technicians`
- `vehicles`
- `parts`

The application uses categories such as Car, Bike and Superbike.
The `All` category is used where an item or technician supports all
vehicle categories.

## Appointment Status Workflow

The application validates status transitions in the backend.
The implemented sequence is:

1. Pending â†’ Confirmed or Cancelled
2. Confirmed â†’ Vehicle Received or Cancelled
3. Vehicle Received â†’ In Progress
4. In Progress â†’ Ready for Pickup
5. Ready for Pickup â†’ Completed

Completed and Cancelled appointments are terminal.

## Inventory and Billing

Estimate line items record proposed parts and amounts.
Creating an estimate does not itself deduct inventory.

Final invoice creation uses the invoice workflow to validate and deduct
the quantities of parts included in the invoice. Inventory updates must
be performed through the application's protected backend operations.

## Fresh Installation vs Existing Database

The PostgreSQL fresh-install schema is database/schema.postgresql.sql.
The MySQL fresh-install schema is database/schema.sql.

These schemas are intended for fresh installations, not upgrades.
Do not execute a fresh-install schema over an existing database containing application data.
Back up existing data and use a reviewed migration before changing an existing schema.

## PostgreSQL Connection Pooling

In PostgreSQL mode, FastAPI initializes a shared Psycopg connection pool during application startup and closes it during shutdown.

Existing database access functions borrow connections from the pool. Calling connection.close() returns a connection to the pool for reuse.

Default settings from .env.example:

- DB_POOL_MIN_SIZE=1
- DB_POOL_MAX_SIZE=5
- DB_POOL_TIMEOUT=10 seconds
- DB_POOL_STARTUP_TIMEOUT=20 seconds

The maximum pool size applies per backend process. Multiple workers or instances multiply the total database connections.

MySQL continues to use its existing direct connection behavior.
PostgreSQL pooling is provided by psycopg[binary,pool].
