from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from langsmith import Client
from routers.kenopi import router as kenopi_router

# 환경 변수 로드 (루트 디렉토리의 .env 파일)
load_dotenv("../.env")

# Map custom LangSmith env vars to LangChain expected
if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
if os.getenv("LANGSMITH_ENDPOINT") and not os.getenv("LANGCHAIN_ENDPOINT"):
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")
tracing_flag = os.getenv("LANGSMITH_TRACING_V2") or os.getenv("LANGWSMITH_TRACING_V2")
if tracing_flag and not os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = tracing_flag

app = FastAPI(title="Kenopi CS Chatbot API", version="1.0.0")

# include kenopi router
app.include_router(kenopi_router)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LangSmith client status check
LS_ENABLED = False
try:
    if os.getenv("LANGSMITH_API_KEY"):
        client = Client()
        print(f"[Main] LangSmith client enabled for project: {os.getenv('LANGSMITH_PROJECT','kenopi-cs-chatbot')}")
        LS_ENABLED = True
    else:
        print("[Main] LangSmith API key not found")
except Exception:
    print("[Main] LangSmith client NOT enabled")
    LS_ENABLED = False

@app.get("/")
async def root():
    return {"message": "Kenopi CS Chatbot API is running!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "langsmith_enabled": LS_ENABLED,
    }

# Pydantic 모델 (일반 채팅용 - 제한된 응답)
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """일반 채팅 - 케노피 CS로 안내"""
    return ChatResponse(
        response="안녕하세요! 저는 케노피(Kenopi) 전용 고객지원 챗봇입니다. "
                "일반적인 질문에는 답변드릴 수 없으며, 케노피 제품 관련 문의만 도와드릴 수 있습니다. "
                "케노피 관련 문의는 /kenopi/chat 엔드포인트를 이용해 주세요."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 