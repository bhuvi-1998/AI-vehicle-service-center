# Requirements and Setup

## Software

- Python installed and available in PowerShell.
- MySQL Server.
- Visual Studio Code.
- A modern web browser.
- Ollama and the configured model for local AI assistant functionality.
- SMTP account details for email verification and password recovery.

## Python Dependencies

The project dependencies are listed in `requirements.txt`.

| Package | Purpose |
|---|---|
| `fastapi` | Backend API framework |
| `uvicorn` | ASGI server |
| `PyMySQL` | MySQL connectivity |
| `python-dotenv` | Loading environment variables from `.env` |
| `PyJWT` | JWT token handling |
| `reportlab` | PDF generation |
| `httpx2` | HTTP client package currently listed by the project |
| `openai` | OpenAI Python SDK currently listed by the project |
| `requests` | HTTP requests used by backend chatbot modules |

Install dependencies from the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Environment Configuration

Create `.env` from `.env.example`.

Configure these values locally:

- MySQL host, username, password and database name.
- JWT signing secret.
- SMTP host, port, username and app password.
- Sender email address.
- Frontend base URLs.
- Email-verification and password-reset expiry durations.

Never put real credentials in `.env.example` or source control.

## Local Development Ports

| Component | Local address |
|---|---|
| FastAPI backend | `http://127.0.0.1:8000` |
| FastAPI Swagger UI | `http://127.0.0.1:8000/docs` |
| Static frontend | `http://127.0.0.1:5503` |
| Ollama API | `http://localhost:11434` |

The frontend server must be started from the `frontend` directory.
The backend server must be started from the project root.

## Important

The SQL schema is for a fresh database installation.
Existing databases require the appropriate migration procedure.

Email and AI features require their external local or SMTP services
to be configured and running.
