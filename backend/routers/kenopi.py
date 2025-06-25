from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from kenopi_chatbot import generate_response

router = APIRouter(prefix="/kenopi", tags=["Kenopi CS"])

class ChatMsg(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    messages: List[ChatMsg]

@router.post("/chat")
async def kenopi_chat(req: ChatReq):
    """케노피 CS 챗봇 엔드포인트"""
    reply = generate_response([m.dict() for m in req.messages])
    return {"response": reply} 