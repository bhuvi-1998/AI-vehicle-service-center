# Database Design

Database name: `vehicle_service_center`

The canonical fresh-install schema is stored in `database/schema.sql`.
It defines the 12 tables listed below.

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

1. Pending → Confirmed or Cancelled
2. Confirmed → Vehicle Received or Cancelled
3. Vehicle Received → In Progress
4. In Progress → Ready for Pickup
5. Ready for Pickup → Completed

Completed and Cancelled appointments are terminal.

## Inventory and Billing

Estimate line items record proposed parts and amounts.
Creating an estimate does not itself deduct inventory.

Final invoice creation uses the invoice workflow to validate and deduct
the quantities of parts included in the invoice. Inventory updates must
be performed through the application's protected backend operations.

## Fresh Installation vs Existing Database

`database/schema.sql` is intended to create a fresh database structure.
Its `CREATE TABLE IF NOT EXISTS` statements do not add missing columns
to tables that already exist.

Do not treat this file as an upgrade script for an existing database.
Use the appropriate migration script and back up the database before
making structural changes.
