from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from app.services.agent import generate_chat_response

router = APIRouter()

class SingleMessage(BaseModel):
    # Pydantic v2 syntax to safely ignore the "id" field sent by React
    model_config = ConfigDict(extra='ignore') 
    
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[SingleMessage]

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert the Pydantic objects back to the clean dictionaries the LLM expects
        clean_messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
        ]
        reply = await generate_chat_response(clean_messages)
        return {"reply": reply}
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))