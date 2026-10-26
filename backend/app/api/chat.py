from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from app.services.agent import generate_chat_response, get_system_prompt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models import UserProfile

router = APIRouter()

class SingleMessage(BaseModel):
    model_config = ConfigDict(extra='ignore') 
    role: str
    content: str

class ChatRequest(BaseModel):
    session_token: str
    messages: List[SingleMessage]

@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 1. Fetch the user's profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.session_token == request.session_token)
    )
    profile = result.scalars().first()
    
    # 2. Generate the dynamic prompt
    system_prompt = get_system_prompt(profile)
    
    # 3. Convert Pydantic message objects to dictionaries 
    formatted_messages = [msg.model_dump() for msg in request.messages]
    
    # 4. Prepend system prompt to the formatted messages
    messages_with_context = [system_prompt] + formatted_messages
    
    # 5. Send to OpenAI
    response_text = await generate_chat_response(messages_with_context)
    
    # Fallback just in case the LLM returns an empty string
    return {"reply": response_text or "Empty response from AI."}