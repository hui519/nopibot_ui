from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from kenopi_chatbot import generate_response, generate_advanced_response

router = APIRouter(prefix="/kenopi", tags=["Kenopi CS"])

class ChatMsg(BaseModel):
    role: str  # 'user' or 'bot'
    content: str

class ChatReq(BaseModel):
    messages: List[ChatMsg]
    # auto_mode는 제거 - 항상 자동 모드 사용

class ChatResponse(BaseModel):
    response: str
    selected_mode: Optional[str] = None  # AI가 선택한 모드 표시

class AdvancedChatResponse(BaseModel):
    response: str
    selected_mode: str
    complexity: Optional[str] = None
    question_type: Optional[str] = None
    urgency: Optional[str] = None
    quality_score: Optional[str] = None
    faq_matched: Optional[bool] = None
    auto_selection: bool = True

@router.post("/chat", response_model=ChatResponse)
async def kenopi_chat(req: ChatReq):
    """
    케노피 CS 챗봇 엔드포인트 (자동 모드 선택)
    
    AI가 질문의 복잡도를 분석하여 자동으로 최적의 모드를 선택합니다:
    - 간단한 질문 → 기본 모드 (빠른 응답)
    - 보통 질문 → 추론 모드 (단계적 사고)
    - 복잡한 질문 → 고급 모드 (종합 분석)
    """
    # 항상 자동 모드 사용
    reply = generate_response([m.dict() for m in req.messages], auto_mode=True)
    
    return ChatResponse(
        response=reply,
        selected_mode="auto"  # 자동 선택됨을 표시
    )

@router.post("/chat/advanced", response_model=AdvancedChatResponse)
async def kenopi_advanced_chat(req: ChatReq):
    """
    자동 모드 선택 + 상세 분석 정보 포함 엔드포인트
    
    AI가 자동으로 선택한 모드와 분석 과정을 함께 제공:
    - selected_mode: AI가 선택한 모드 (basic/thinking/enhanced)
    - complexity: 질문 복잡도 (low/medium/high)
    - question_type: 질문 유형 (greeting/inquiry/complaint/request)
    - urgency: 긴급도 (low/medium/high)
    - quality_score: 응답 품질 점수
    """
    result = generate_advanced_response([m.dict() for m in req.messages])
    
    return AdvancedChatResponse(
        response=result["response"],
        selected_mode=result.get("selected_mode", "basic"),
        complexity=result.get("complexity"),
        question_type=result.get("question_type"),
        urgency=result.get("urgency"),
        quality_score=result.get("quality_score"),
        faq_matched=result.get("faq_matched"),
        auto_selection=result.get("auto_selection", True)
    )

@router.get("/thinking/status")
async def get_thinking_status():
    """자동 모드 선택 시스템 상태 확인"""
    try:
        from sequential_thinking_mcp import thinking_mcp
        
        return {
            "status": "active",
            "auto_mode_selection": {
                "enabled": True,
                "description": "AI가 질문 복잡도를 분석하여 자동으로 최적 모드 선택"
            },
            "available_modes": {
                "basic": {
                    "name": "기본 모드",
                    "description": "간단한 질문, 인사말, FAQ 매칭 시 사용",
                    "icon": "💬"
                },
                "thinking": {
                    "name": "추론 모드", 
                    "description": "보통 복잡도 질문에 단계적 사고 적용",
                    "icon": "🧠"
                },
                "enhanced": {
                    "name": "고급 모드",
                    "description": "복잡한 문의, 불만, 긴급 상황 시 종합 분석",
                    "icon": "⚡"
                }
            },
            "selection_criteria": {
                "complexity_analysis": ["high", "medium", "low"],
                "question_types": ["greeting", "inquiry", "complaint", "request"],
                "urgency_levels": ["high", "medium", "low"],
                "additional_factors": ["FAQ 매칭", "대화 맥락", "문장 길이"]
            },
            "sequential_thinking": {
                "available": thinking_mcp.mcp_available,
                "features": [
                    "자동 복잡도 분석",
                    "질문 유형 분류",
                    "긴급도 판단",
                    "모드 자동 선택",
                    "품질 보증 시스템"
                ]
            },
            "model_info": {
                "engine": "MCP Sequential Thinking Tools",
                "fallback": "GPT-3.5-turbo",
                "auto_selection": True
            }
        }
    except ImportError:
        return {
            "status": "limited",
            "auto_mode_selection": {
                "enabled": False,
                "description": "Sequential Thinking MCP가 설치되지 않음"
            },
            "available_modes": {
                "basic": {
                    "name": "기본 모드",
                    "description": "기본 응답만 가능",
                    "icon": "💬"
                }
            }
        }

@router.post("/thinking/demo")
async def demo_auto_mode_selection(req: ChatReq):
    """
    자동 모드 선택 데모 (여러 질문 유형별 테스트)
    """
    if not req.messages:
        return {"error": "메시지가 필요합니다"}
    
    import time
    
    messages = [m.dict() for m in req.messages]
    query = messages[-1]["content"]
    
    # 자동 모드 선택 상세 분석
    start_time = time.time()
    result = generate_advanced_response(messages)
    processing_time = time.time() - start_time
    
    # 다른 모드들과 비교를 위한 기본 응답
    basic_start = time.time()
    basic_response = generate_response(messages, auto_mode=False)
    basic_time = time.time() - basic_start
    
    return {
        "query": query,
        "auto_selection_result": {
            "selected_mode": result.get("selected_mode"),
            "complexity": result.get("complexity"),
            "question_type": result.get("question_type"),
            "urgency": result.get("urgency"),
            "reasoning": f"'{query}' 분석 결과 {result.get('complexity')} 복잡도, {result.get('question_type')} 유형으로 판단되어 {result.get('selected_mode')} 모드가 선택되었습니다."
        },
        "responses": {
            "auto_selected": {
                "response": result["response"],
                "mode": result.get("selected_mode"),
                "processing_time": round(processing_time, 3),
                "quality_score": result.get("quality_score")
            },
            "basic_fallback": {
                "response": basic_response,
                "mode": "basic",
                "processing_time": round(basic_time, 3),
                "quality_score": "basic"
            }
        },
        "analysis": {
            "auto_selection_benefits": [
                "사용자가 모드를 선택할 필요 없음",
                "질문에 최적화된 응답 방식 자동 적용",
                "복잡한 질문에 더 신중한 분석",
                "간단한 질문에 빠른 응답"
            ],
            "selection_factors": result.get("analysis", {}),
            "performance": {
                "auto_time": processing_time,
                "basic_time": basic_time,
                "intelligence_overhead": round(processing_time - basic_time, 3)
            }
        }
    }

@router.get("/thinking/examples")
async def get_auto_mode_examples():
    """자동 모드 선택 예시들"""
    return {
        "examples": [
            {
                "query": "안녕하세요",
                "expected_mode": "basic",
                "reason": "간단한 인사말 - 빠른 응답"
            },
            {
                "query": "배송 기간이 얼마나 걸리나요?",
                "expected_mode": "thinking",
                "reason": "일반적인 문의 - 단계적 사고로 정확한 답변"
            },
            {
                "query": "제품이 불량인데 환불과 교환 중 어떤 게 더 유리한가요?",
                "expected_mode": "enhanced", 
                "reason": "복잡한 상황 - 다각도 분석 필요"
            },
            {
                "query": "급하게 처리해주세요! 제품에 문제가 있어요!",
                "expected_mode": "enhanced",
                "reason": "긴급 상황 + 불만 - 신중한 대응 필요"
            },
            {
                "query": "감사합니다",
                "expected_mode": "basic",
                "reason": "간단한 감사 인사 - 기본 응답"
            }
        ],
        "selection_logic": {
            "basic_mode": [
                "인사말 (안녕, 감사 등)",
                "FAQ 매칭되는 간단한 질문",
                "짧고 명확한 확인 질문"
            ],
            "thinking_mode": [
                "일반적인 문의 사항",
                "중간 길이의 질문",
                "설명이 필요한 내용"
            ],
            "enhanced_mode": [
                "복잡한 상황 분석 필요",
                "불만이나 문제 제기",
                "긴급 상황",
                "여러 옵션 비교 필요"
            ]
        }
    } 