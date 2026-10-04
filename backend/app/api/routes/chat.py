from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.chat.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatSessionCreate(BaseModel):
    document_id: int
    title: Optional[str] = "New Chat"

class ChatMessageCreate(BaseModel):
    content: str

class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quote: Optional[str]
    locator: Optional[str]
    page_id: Optional[int]

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    citations: List[CitationResponse] = []

class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    title: str


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RAGService(db)
    try:
        session = service.create_session(request.document_id, current_user.id, request.title)
        return session
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def send_message(
    session_id: int,
    request: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RAGService(db)
    try:
        result = service.send_message(session_id, current_user.id, request.content)
        msg = result["message"]
        citations = result["citations"]
        
        return {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "citations": citations
        }
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
