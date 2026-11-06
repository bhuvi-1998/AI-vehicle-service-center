# AI Vehicle Service Center

A web-based application for managing vehicle service-center operations.
It includes administrator and customer workflows, a FastAPI backend,
a Supabase-hosted PostgreSQL database, with optional MySQL support, and chatbot functionality.

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
| Production database | PostgreSQL (Supabase) |
| Database drivers | Psycopg 3 and PyMySQL |
| Frontend | HTML, CSS, JavaScript |
| Authentication | JWT |
| AI assistant | Ollama (local and cloud) |
| PDF generation | ReportLab |
| Email | SMTP |

## Project Structure

```text
AI-vehicle-service-center/
|-- backend/
|   `-- app/
|       |-- database/
|       |-- routers/
|       |-- schemas/
|       |-- services/
|       |   `-- ollama_client.py
|       |-- security.py
|       `-- main.py
|-- database/
|   |-- schema.postgresql.sql
|   `-- schema.sql
|-- docs/
|   |-- api.md
|   |-- database.md
|   |-- requirements.md
|   `-- workflow.md
|-- frontend/
|   |-- chatbot/
|   |-- customer-portal/
|   |-- js/
|   |   |-- api.js
|   |   `-- config.js
|   `-- pages/
|-- .env.example
|-- .gitignore
|-- .python-version
|-- requirements.txt
`-- README.md
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
Configure your Supabase PostgreSQL and SMTP settings and generate a unique JWT secret. Local MySQL is also supported.

Never commit `.env` or share its contents.

### 3. Prepare the database

The project includes two fresh-install schemas:

- PostgreSQL: `database/schema.postgresql.sql`
- MySQL: `database/schema.sql`

Use the schema matching your selected database. These files
are for fresh installations, not upgrades to existing databases.
Back up existing data before applying any migration.

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

Both customer and administrator chatbots use the shared backend service:
`backend/app/services/ollama_client.py`.

### Local Development

Local development uses Ollama with the llama3.2:3b model.
Install Ollama, download the model using ollama pull llama3.2:3b,
and keep the local Ollama service running.

Configure OLLAMA_MODE=local.

### Production with Ollama Cloud

Production can use Ollama Cloud with the Gemma 4 model.
Configure these variables in the private backend hosting settings:

```ini
APP_ENV=production
OLLAMA_MODE=cloud
OLLAMA_CLOUD_MODEL=gemma4
OLLAMA_API_KEY=your_private_ollama_cloud_api_key
```

Never commit a real API key to GitHub or place it in frontend JavaScript.
Ollama Cloud usage may incur token-based charges.
Check current pricing at https://ollama.com/pricing.

The cloud connection must pass a live API test before production chatbot functionality is considered ready.

Administrative database operations remain controlled by authenticated backend routes.

## Documentation

- [API Reference](docs/api.md)
- [Database Design](docs/database.md)
- [Requirements and Setup](docs/requirements.md)
- [Application Workflow](docs/workflow.md)

## Important Notes

- Production deployment requires configured hosting, database, email, and Ollama Cloud settings.
- Do not commit `.env`, passwords, app passwords, JWT secrets, or tokens.
- Back up the database before applying migrations.
- Do not execute the fresh-install schema as an assumed database upgrade.
