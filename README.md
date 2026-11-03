# Vehicle Service Center Management System

A web-based application for managing vehicle service-center operations.
It includes administrator and customer workflows, a FastAPI backend,
a MySQL database, and chatbot functionality.

## Main Features

### Administrator

- Manage customers, vehicles, services, and technicians.
- View and manage customer appointments.
- Assign technicians to appointments.
- Track appointment status through permitted status transitions.
- Manage spare-parts inventory.
- Create service estimates and generate estimate PDFs.
- Generate final invoices and invoice PDFs.
- Record payment methods and payment status.
- Use the admin AI assistant for supported lookups and operations.
- View business and inventory summaries.

### Customer

- Register and verify an email address.
- Log in to the customer portal.
- Manage vehicles and customer profile information.
- Book and view appointments.
- Use permitted appointment cancellation and rescheduling features.
- Ask the customer assistant about supported appointment information.
- Use email-based account recovery.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | MySQL |
| Database driver | PyMySQL |
| Frontend | HTML, CSS, JavaScript |
| Authentication | JWT |
| AI assistant | Ollama, llama3.2:3b |
| PDF generation | ReportLab |
| Email | SMTP |

## Project Structure

```text
vehical-service-center/
├── backend/
│   └── app/
│       ├── routers/
│       ├── schemas/
│       ├── services/
│       ├── database/
│       ├── security.py
│       └── main.py
├── database/
│   └── schema.sql
├── docs/
│   ├── api.md
│   ├── database.md
│   ├── requirements.md
│   └── workflow.md
├── frontend/
│   ├── chatbot/
│   ├── customer-portal/
│   ├── js/
│   └── pages/
├── migrate_vehicle_categories.py
├── requirements.txt
├── .env.example
└── README.md
```

## Local Setup

### 1. Prepare the environment

Open PowerShell in the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and edit `.env` in VS Code.
Enter your own MySQL and SMTP settings and generate a unique JWT secret.

Never commit `.env` or share its contents.

### 3. Prepare the database

For a **new database setup**, review and execute `database/schema.sql`
using MySQL Workbench or your MySQL client.

This file describes the complete schema for a fresh installation.
It is not an upgrade script for an existing database. Use the project's
migration scripts when upgrading an existing installation.

### 4. Start the backend

Run from the project root:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Backend address: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### 5. Start the frontend

Open a second PowerShell terminal:

```powershell
Set-Location "frontend"
python -m http.server 5503
```

### 6. Open the application

Administrator login:

`http://127.0.0.1:5503/pages/login.html`

Customer portal:

`http://127.0.0.1:5503/customer-portal/index.html`

## AI Assistant

The local AI integration uses Ollama and the `llama3.2:3b` model.
Ollama must be installed, the model must be available locally, and its
local service must be running for the AI features to respond.

The assistant can only perform operations that are implemented and
authorized by the backend.

## Documentation

- [API Reference](docs/api.md)
- [Database Design](docs/database.md)
- [Requirements and Setup](docs/requirements.md)
- [Application Workflow](docs/workflow.md)

## Important Notes

- This is a local development setup, not a production deployment guide.
- Do not commit `.env`, passwords, app passwords, JWT secrets, or tokens.
- Back up the database before applying migrations.
- Do not execute the fresh-install schema as an assumed database upgrade.
