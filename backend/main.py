from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="AI Chatbot API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

# OpenAI 클라이언트 초기화
try:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
        temperature=0.7
    )
except Exception as e:
    print(f"OpenAI 클라이언트 초기화 실패: {e}")
    llm = None

@app.get("/")
async def root():
    return {"message": "AI Chatbot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "openai_configured": llm is not None}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not llm:
            raise HTTPException(status_code=500, detail="OpenAI 클라이언트가 초기화되지 않았습니다.")
        
        # 메시지 변환
        messages = []
        for msg in request.messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role in ["assistant", "bot"]:
                messages.append(AIMessage(content=msg.content))
        
        # AI 응답 생성
        response = llm.invoke(messages)
        
        return ChatResponse(response=response.content)
    
    except Exception as e:
        return ChatResponse(
            response="",
            error=f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 