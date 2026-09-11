"""Pi-only evidence capability: its own source, never the owner admin key."""

import os
import secrets

from app.services import conversation_memory
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/runtime/conversation", tags=["conversation evidence"])


def require_conversation_key(
    key: str | None = Header(None, alias="X-MemoryGate-Conversation-Key"),
    requested_agent: str | None = Header(None, alias="X-Agent-Id"),
) -> str:
    expected = os.environ.get("MEMORYGATE_CONVERSATION_KEY", "")
    if len(expected) < 16 or not key or not secrets.compare_digest(expected, key):
        raise HTTPException(
            401,
            "Configure a dedicated MEMORYGATE_CONVERSATION_KEY; admin/read keys do not grant ingestion",
        )
    agent = os.environ.get("MEMORYGATE_CONVERSATION_AGENT_ID", "default")
    if requested_agent is not None and requested_agent != agent:
        raise HTTPException(
            403, "Match Pi's agent ID to MEMORYGATE_CONVERSATION_AGENT_ID before retrying"
        )
    return agent


class ConversationEvidence(BaseModel):
    model_config = {"extra": "forbid"}
    session_id: str = Field(pattern=r"^ses_[A-Za-z0-9_-]+$", max_length=100)
    content: str = Field(min_length=1, max_length=16000)
    created_at: float = Field(ge=0, le=4102444800)


@router.put("/{message_id}")
def ingest(
    message_id: str,
    payload: ConversationEvidence,
    agent_id: str = Depends(require_conversation_key),
):
    if not message_id.startswith("msg_") or len(message_id) > 100:
        raise HTTPException(422, "Use Pi's original stable message ID")
    return conversation_memory.ingest(agent_id, message_id, payload.model_dump())


@router.delete("/{message_id}")
def forget(message_id: str, agent_id: str = Depends(require_conversation_key)):
    if not message_id.startswith("msg_") or len(message_id) > 100:
        raise HTTPException(422, "Use Pi's original stable message ID")
    return conversation_memory.forget(agent_id, message_id)
