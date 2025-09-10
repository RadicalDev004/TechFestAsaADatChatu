from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from fastapi.responses import Response
from openai import OpenAI
from Backend.config.constants import MODEL_CONFIG, PROMPT_CONFIG, EXPLAIN_PROMPT
from Backend.services.chatbot_service import create_agent
from Database.db_history import (
    create_conversation,
    list_conversations,
    get_conversation,
    delete_conversation,
    add_message,
    list_messages,
    rename_conversation,
    title_from_text,
)
from Backend.models.schemas import (
    ConversationOut,
    MessageIn,
    MessageOut,
    ConversationWithMessages,
)
from Backend.core.deps import get_current_clinic
from Backend.utils.tools import bots, is_image

router = APIRouter(prefix="/api", tags=["chatbot"])
CurrentClinic = Annotated[dict, Depends(get_current_clinic)]

@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation_route(current: CurrentClinic):
    """Create a new conversation for the current clinic."""
    conv_id = create_conversation(clinic_id=current["clinic_id"], title="New conversation")

    bots[conv_id] = create_agent(MODEL_CONFIG, PROMPT_CONFIG)

    conv = get_conversation(conversation_id=conv_id, clinic_id=current["clinic_id"])
    if not conv:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create conversation")
    return ConversationOut(id=conv.id, title=conv.title)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations_route(current: CurrentClinic):
    """List conversations for the current clinic (most-recent first)."""
    convs = list_conversations(clinic_id=current["clinic_id"])
    return [ConversationOut(id=c.id, title=c.title) for c in convs]



@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation_route(conversation_id: int, current: CurrentClinic):
    """Fetch a conversation (ownership enforced) with its messages."""
    conv = get_conversation(conversation_id=conversation_id, clinic_id=current["clinic_id"])
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msgs = list_messages(conversation_id=conv.id)
    return ConversationWithMessages(
        conversation=ConversationOut(id=conv.id, title=conv.title),
        messages=[MessageOut(id=m["id"], role=m["role"], content=m["content"]) for m in msgs],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationWithMessages)
def send_message_route(conversation_id: int, payload: MessageIn, current: CurrentClinic):
    """Append a user message to a conversation you own and return the thread."""
    conv = get_conversation(conversation_id=conversation_id, clinic_id=current["clinic_id"])
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content required")

    # Add user message
    add_message(conversation_id=conv.id, clinic_id=current["clinic_id"], role="user", content=content)

    if conv.id not in bots:
        bots[conv.id] = create_agent(MODEL_CONFIG, PROMPT_CONFIG)

    chat_fn = bots[conv.id] # get the callable conversation function
    try:
        bot_reply = chat_fn(content)
        if is_image(bot_reply):
            explanation = chat_fn(EXPLAIN_PROMPT)
            bot_reply = f"{bot_reply}\n\n{explanation}"
    except Exception as e:
        raise HTTPException(status_code=500, detail="Assistant failed to reply") from e

    add_message(conversation_id=conv.id, clinic_id=current["clinic_id"], role="assistant", content=bot_reply)

    if conv.title == "New conversation":
        rename_conversation(conversation_id=conv.id, clinic_id=current["clinic_id"], new_title=title_from_text(content))

    conv = get_conversation(conversation_id=conversation_id, clinic_id=current["clinic_id"])
    msgs = list_messages(conversation_id=conv.id)
    return ConversationWithMessages(
        conversation=ConversationOut(id=conv.id, title=conv.title),
        messages=[MessageOut(id=m["id"], role=m["role"], content=m["content"]) for m in msgs],
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation_route(conversation_id: int, current: CurrentClinic):
    """Delete a conversation you own (cascades to messages)."""
    conv = get_conversation(conversation_id=conversation_id, clinic_id=current["clinic_id"])
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    delete_conversation(conversation_id=conv.id, clinic_id=current["clinic_id"])

    bots.pop(conv.id, None)
    return {"ok": True}

@router.get("/conversations/{conversation_id}/tts")
def text_to_speech_route(conversation_id: int, current: CurrentClinic):
    """Convert the last assistant message in a conversation to speech."""
    conv = get_conversation(conversation_id=conversation_id, clinic_id=current["clinic_id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = list_messages(conversation_id=conv.id)

    last_assistant_msg = next((m for m in reversed(msgs) if m["role"] == "assistant"), None)
    if not last_assistant_msg:
        raise HTTPException(status_code=400, detail="No assistant message to synthesize")

    text_input = (last_assistant_msg.get("content") or "").strip()
    if not text_input:
        raise HTTPException(status_code=400, detail="Assistant message is empty")

    client = OpenAI()

    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text_input
        ) as resp:
            audio_bytes = resp.read()
    except Exception:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-realtime-preview-2024-12-17",
            voice="alloy",
            input=text_input
        ) as resp:
            audio_bytes = resp.read()

    return Response(content=audio_bytes, media_type="audio/mpeg")