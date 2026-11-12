"""Shared connection for local Ollama and Ollama Cloud."""

import os
import requests


class OllamaClientError(Exception):
    """Safe error raised when an Ollama request fails."""


def generate_chat_reply(messages: list[dict[str, str]]) -> str:
    app_env = os.getenv("APP_ENV", "development").strip().lower()

    default_mode = "cloud" if app_env == "production" else "local"
    mode = os.getenv("OLLAMA_MODE", default_mode).strip().lower()

    if mode == "cloud":
        api_key = os.getenv("OLLAMA_API_KEY", "").strip()

        if not api_key:
            raise OllamaClientError(
                "OLLAMA_API_KEY is missing from the backend environment."
            )

        url = os.getenv(
            "OLLAMA_CLOUD_URL",
            "https://ollama.com/api/chat"
        ).strip()

        model = os.getenv("OLLAMA_CLOUD_MODEL", "gemma4").strip()

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

    elif mode == "local":
        url = os.getenv(
            "OLLAMA_LOCAL_URL",
            "http://localhost:11434/api/chat"
        ).strip()

        model = os.getenv(
            "OLLAMA_LOCAL_MODEL",
            "llama3.2:3b"
        ).strip()

        headers = {}

    else:
        raise OllamaClientError(
            "OLLAMA_MODE must be either 'local' or 'cloud'."
        )

    if not url or not model:
        raise OllamaClientError(
            "The Ollama URL or model configuration is empty."
        )

    try:
        response = requests.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "stream": False
            },
            timeout=(10, 120)
        )

        response.raise_for_status()
        data = response.json()

    except requests.Timeout as exc:
        raise OllamaClientError(
            "The Ollama service timed out. Please try again."
        ) from exc

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0

        if status in (401, 403):
            detail = (
                "Ollama Cloud authentication failed. "
                "Check OLLAMA_API_KEY."
                if mode == "cloud"
                else "Ollama rejected the local request."
            )
        elif status == 429:
            detail = (
                "Ollama rate limit or available usage limit reached."
            )
        else:
            detail = f"Ollama returned HTTP {status}."

        raise OllamaClientError(detail) from exc

    except ValueError as exc:
        raise OllamaClientError(
            "Ollama returned an invalid response."
        ) from exc

    except requests.RequestException as exc:
        raise OllamaClientError(
            "Unable to connect to the configured Ollama service."
        ) from exc

    message = data.get("message", {})
    reply = message.get("content", "") if isinstance(message, dict) else ""

    if not isinstance(reply, str) or not reply.strip():
        raise OllamaClientError(
            "The Ollama assistant returned an empty response."
        )

    return reply.strip()
