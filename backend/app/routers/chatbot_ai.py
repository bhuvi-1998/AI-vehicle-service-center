
import requests

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.security import get_current_customer

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


class ChatbotMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


@router.post("/message")
def chatbot_message(
    payload: ChatbotMessage,
    current_customer: dict = Depends(get_current_customer),
):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant for a vehicle "
                            "service center. Answer questions about vehicle "
                            "maintenance, common vehicle problems, servicing, "
                            "and general service-center information. "
                            "Be friendly and concise. Do not claim to access "
                            "customer appointments, private records, payments, "
                            "or live service status. The application handles "
                            "appointment lookups separately. For serious "
                            "vehicle safety issues, recommend a qualified "
                            "mechanic."
                        ),
                    },
                    {
                        "role": "user",
                        "content": payload.message,
                    },
                ],
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()
        reply = data.get("message", {}).get("content", "").strip()

        if not reply:
            raise HTTPException(
                status_code=502,
                detail="The AI assistant returned an empty response.",
            )

        return {"reply": reply}

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="The local AI assistant is unavailable. Please try again.",
        )
