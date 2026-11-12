
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.security import get_current_customer
from backend.app.services.ollama_client import OllamaClientError, generate_chat_reply

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])



class ChatbotMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


@router.post("/message")
def chatbot_message(
    payload: ChatbotMessage,
    current_customer: dict = Depends(get_current_customer),
):
    messages = [
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
    ]

    try:
        reply = generate_chat_reply(messages)
        return {"reply": reply}

    except OllamaClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
