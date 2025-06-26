from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import os
from difflib import SequenceMatcher
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

from kenopi_prompt import (
    KENOPI_SYSTEM_PROMPT, 
    KENOPI_THINKING_PROMPT,
    EMOTION_RESPONSIVE_PROMPT,
    QUALITY_ASSURANCE_PROMPT
)

# Sequential Thinking MCP 통합
try:
    from sequential_thinking_mcp import thinking_mcp
    THINKING_AVAILABLE = True
    print("[Kenopi Chatbot] 🧠 Sequential Thinking MCP loaded successfully")
except ImportError as e:
    print(f"[Kenopi Chatbot] ⚠️ Sequential Thinking not available: {e}")
    THINKING_AVAILABLE = False

# Map custom LANGSMITH_* env vars to LangChain expected keys
if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
if os.getenv("LANGSMITH_ENDPOINT") and not os.getenv("LANGCHAIN_ENDPOINT"):
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")
# Handle tracing flag (사용자 오타 포함)
tracing_flag = os.getenv("LANGSMITH_TRACING_V2") or os.getenv("LANGWSMITH_TRACING_V2")
if tracing_flag and not os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = tracing_flag

project_name_env = os.getenv("LANGSMITH_PROJECT", "kenopi-cs")

# Enable LangSmith tracing via environment variables
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print(f"[Kenopi Chatbot] LangSmith tracing enabled for project: {project_name_env}")
else:
    print("[Kenopi Chatbot] LangSmith tracing disabled")

# LangChain 설정 (OpenAI API 키가 있을 때만)
try:
    if os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            temperature=0.3,
        )
        print("INFO: GPT-4o 모델로 설정되었습니다.")
    else:
        llm = None
        print("WARNING: OpenAI API 키가 없습니다. FAQ 전용 모드로 실행됩니다.")
except Exception as e:
    llm = None
    print(f"WARNING: OpenAI 설정 실패: {e}. FAQ 전용 모드로 실행됩니다.")

# Load FAQ dataset at import time
FAQ_PATH = Path(__file__).parent / "data" / "kenopi_faq.csv"
FAQ_LIST = []
if FAQ_PATH.exists():
    with FAQ_PATH.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # 헤더 스킵
        for row in reader:
            if len(row) >= 3 and row[1] and row[2]:  # 첫 번째는 번호, 두 번째는 질문, 세 번째는 답변
                FAQ_LIST.append({"question": row[1], "answer": row[2]})

SIM_THRESHOLD = 0.5

def _search_faq(query: str):
    """FAQ에서 유사한 질문을 찾아 답변 반환 - 정확한 매칭만"""
    best = None
    best_score = 0
    for item in FAQ_LIST:
        score = SequenceMatcher(None, query.lower(), item["question"].lower()).ratio()
        if score > best_score:
            best_score = score
            best = item
    
    # 정확한 매칭만 허용 (0.8 이상)
    if best_score >= 0.8:
        return {"answer": best["answer"], "question": best["question"], "score": best_score}
    return None

def _find_intent_match(query: str):
    """질문 의도를 파악해서 FAQ 주제와 매칭"""
    query_lower = query.lower()
    
    # 의도별 키워드 매핑
    intent_keywords = {
        "환불": ["환불", "돈", "돌려", "취소", "안받", "반납"],
        "교환": ["교환", "바꾸", "다른걸로", "사이즈", "색깔"],
        "반품": ["반품", "보내", "돌려보내", "안받", "취소"],
        "배송비": ["배송비", "택배비", "비용", "얼마", "가격"],
        "고객센터": ["연락", "전화", "문의", "고객센터", "상담"],
        "스크래치": ["스크래치", "긁힘", "상처", "흠집"],
        "자수": ["자수", "로고", "브랜드"],
        "물샘": ["물", "새", "비", "방수"],
        "냄새": ["냄새", "향", "냄"],
        "스트랩": ["스트랩", "끈", "고리", "연결"],
        "길이조절": ["길이", "조절", "늘리", "줄이"],
        "배송": ["배송", "언제", "출발", "도착"],
        "주문확인": ["주문", "확인", "내역"],
        "AS": ["AS", "품질", "보증", "하자"],
        "브랜드": ["케노피", "브랜드", "회사"],
        "대량주문": ["대량", "기업", "많이"],
        "해외배송": ["해외", "외국", "국제"]
    }
    
    # 각 의도별로 키워드 매칭 점수 계산
    intent_scores = {}
    for intent, keywords in intent_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in query_lower:
                score += 1
        if score > 0:
            intent_scores[intent] = score
    
    # 가장 높은 점수의 의도 반환
    if intent_scores:
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0]
    
    return None

def generate_response(history: list[dict[str, str]], auto_mode: bool = True) -> str:
    """
    케노피 CS 챗봇 응답 생성 - 의도 파악 및 확인 시스템 (할루시네이션 방지)
    history: [{role: 'user'|'bot', content: str}, ...]
    auto_mode: 자동 모드 선택 여부 (기본값: True)
    """
    if not history:
        return "안녕하세요! 케노피 고객지원팀 노피🤖입니다. 무엇을 도와드릴까요?"
    
    latest_query = history[-1]["content"]
    
    # 🎯 1단계: 정확한 FAQ 매칭 시도
    faq_result = _search_faq(latest_query)
    if faq_result:
        return f"안녕하세요! 노피🤖입니다. 😊\n\n{faq_result['answer']}"
    
    # ✅ 2단계: 확인 응답 처리 (네/예/맞아요 등)
    if _is_confirmation(latest_query) and len(history) >= 2:
        previous_bot_message = None
        for i in range(len(history) - 2, -1, -1):
            if history[i]["role"] == "bot":
                previous_bot_message = history[i]["content"]
                break
        
        if previous_bot_message:
            intent = _extract_intent_from_confirmation(previous_bot_message)
            if intent:
                faq_answer = _get_faq_by_intent(intent)
                if faq_answer:
                    return f"네, 알려드릴게요! 😊\n\n{faq_answer}"
    
    # 🤔 3단계: 의도 파악 및 확인 질문
    intent = _find_intent_match(latest_query)
    if intent:
        return _get_confirmation_question(intent, latest_query)
    
    # 🚫 4단계: 의도도 파악 안되면 정중하게 거절
    return _get_rejection_response(latest_query)

def _is_confirmation(query: str) -> bool:
    """사용자 응답이 확인(긍정) 응답인지 판단"""
    query_lower = query.lower().strip()
    positive_responses = [
        "네", "예", "맞아요", "맞습니다", "그렇습니다", "맞다", "응", "어", "그래", "그렇다",
        "yes", "y", "ok", "okay", "좋아", "좋습니다", "알려줘", "알려주세요", "궁금해", "궁금합니다"
    ]
    return query_lower in positive_responses

def _extract_intent_from_confirmation(bot_message: str) -> str:
    """봇의 확인 질문에서 의도 추출"""
    if "환불 정책이 궁금하신가요?" in bot_message:
        return "환불"
    elif "교환 방법이 궁금하신가요?" in bot_message:
        return "교환"
    elif "반품 방법이나 주소가 궁금하신가요?" in bot_message:
        return "반품"
    elif "배송비가 궁금하신가요?" in bot_message:
        return "배송비"
    elif "고객센터 연락처가 궁금하신가요?" in bot_message:
        return "고객센터"
    elif "스크래치 관련 정책이 궁금하신가요?" in bot_message:
        return "스크래치"
    elif "자수 로고 부분 관련 문의인가요?" in bot_message:
        return "자수"
    elif "방수 관련 문의인가요?" in bot_message:
        return "물샘"
    elif "냄새 관련 문의인가요?" in bot_message:
        return "냄새"
    elif "스트랩/키링 연결 방법이 궁금하신가요?" in bot_message:
        return "스트랩"
    elif "길이 조절이 궁금하신가요?" in bot_message:
        return "길이조절"
    elif "배송 일정이 궁금하신가요?" in bot_message:
        return "배송"
    elif "주문 확인 방법이 궁금하신가요?" in bot_message:
        return "주문확인"
    elif "AS나 품질보증이 궁금하신가요?" in bot_message:
        return "AS"
    elif "브랜드 정보가 궁금하신가요?" in bot_message:
        return "브랜드"
    elif "대량 주문이나 기업 구매가 궁금하신가요?" in bot_message:
        return "대량주문"
    elif "해외 배송이 궁금하신가요?" in bot_message:
        return "해외배송"
    return None

def _get_faq_by_intent(intent: str) -> str:
    """의도에 따른 FAQ 답변 반환"""
    intent_to_faq_keywords = {
        "환불": ["환불", "돈"],
        "교환": ["교환"],
        "반품": ["반품", "주소"],
        "배송비": ["배송비"],
        "고객센터": ["고객센터", "연락처"],
        "스크래치": ["스크래치"],
        "자수": ["자수"],
        "물샘": ["방수", "물"],
        "냄새": ["냄새"],
        "스트랩": ["스트랩", "키링"],
        "길이조절": ["길이"],
        "배송": ["배송", "언제"],
        "주문확인": ["주문", "확인"],
        "AS": ["AS", "품질"],
        "브랜드": ["케노피", "브랜드"],
        "대량주문": ["대량", "기업"],
        "해외배송": ["해외"]
    }
    
    keywords = intent_to_faq_keywords.get(intent, [])
    
    # FAQ에서 키워드가 포함된 질문 찾기
    for item in FAQ_LIST:
        for keyword in keywords:
            if keyword in item["question"]:
                return item["answer"]
    
    return None

def _get_confirmation_question(intent: str, original_query: str) -> str:
    """의도에 따른 확인 질문 생성"""
    confirmation_questions = {
        "환불": "환불 정책이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "교환": "교환 방법이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "반품": "반품 방법이나 주소가 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "배송비": "반품/교환 시 배송비가 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "고객센터": "고객센터 연락처가 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "스크래치": "제품 스크래치 관련 정책이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "자수": "자수 로고 부분 관련 문의인가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "물샘": "우산 방수 관련 문의인가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "냄새": "제품 냄새 관련 문의인가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "스트랩": "스트랩/키링 연결 방법이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "길이조절": "스트랩 길이 조절이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "배송": "배송 일정이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "주문확인": "주문 확인 방법이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "AS": "AS나 품질보증이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "브랜드": "케노피 브랜드 정보가 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "대량주문": "대량 주문이나 기업 구매가 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)",
        "해외배송": "해외 배송이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)"
    }
    
    return confirmation_questions.get(intent, 
        "어떤 정보가 필요하신지 좀 더 구체적으로 말씀해주시면 도와드릴게요! 😊")

def _get_rejection_response(user_question: str) -> str:
    """FAQ에 없는 질문에 대한 정중한 거절 응답"""
    return (
        "죄송합니다. 해당 질문에 대한 정보는 현재 제공해드리지 않고 있습니다.\n\n"
        "케노피 고객센터(010-2747-9567, 평일 10시-17시)로 문의해주시면 "
        "정확한 답변을 받으실 수 있습니다."
    )

def _generate_auto_response(history: List[Dict[str, str]]) -> str:
    """자동 모드 선택을 통한 응답 생성"""
    try:
        latest_query = history[-1]["content"]
        
        # 질문 복잡도 및 유형 분석
        complexity_analysis = _analyze_query_complexity_detailed(latest_query)
        complexity = complexity_analysis["complexity"]
        question_type = complexity_analysis["type"]
        urgency = complexity_analysis["urgency"]
        
        # FAQ 검색 및 컨텍스트 구성
        faq_answer = _search_faq(latest_query)
        conversation_context = _build_conversation_context(history)
        
        # 자동 모드 선택 로직
        selected_mode = _select_optimal_mode(complexity, question_type, urgency, bool(faq_answer))
        
        print(f"[Auto Mode] 질문: '{latest_query[:50]}...' | 복잡도: {complexity} | 선택된 모드: {selected_mode}")
        
        # 선택된 모드에 따른 응답 생성
        if selected_mode == "basic":
            return _generate_basic_response(history)
        elif selected_mode == "thinking":
            return _generate_thinking_response_with_mode(history, "thinking")
        elif selected_mode == "enhanced":
            return _generate_thinking_response_with_mode(history, "enhanced")
        else:
            return _generate_basic_response(history)
            
    except Exception as e:
        print(f"[Auto Response Error] {e}")
        return _generate_basic_response(history)

def _analyze_query_complexity_detailed(query: str) -> Dict[str, Any]:
    """상세한 질문 복잡도 및 유형 분석"""
    
    # 복잡도 지표들
    complexity_indicators = {
        "high": [
            "어떻게", "왜", "이유", "방법", "절차", "단계", "과정", 
            "비교해", "차이", "장단점", "문제해결", "불량", "고장",
            "환불", "교환", "반품", "AS", "수리", "보상", "배상"
        ],
        "medium": [
            "언제", "어디서", "얼마", "가격", "비용", "기간", "시간",
            "정책", "규정", "조건", "방법", "안내", "설명"
        ],
        "low": [
            "안녕", "감사", "네", "예", "아니오", "확인", "알려주세요",
            "문의", "연락처", "전화번호"
        ]
    }
    
    # 긴급도 지표
    urgency_indicators = {
        "high": ["긴급", "급해", "빨리", "즉시", "당장", "지금", "문제", "고장", "불량"],
        "medium": ["오늘", "이번주", "빠른", "가능한"],
        "low": ["언제", "나중에", "여유"]
    }
    
    # 질문 유형 분석
    question_types = {
        "complaint": ["불만", "화", "짜증", "문제", "불량", "고장", "잘못"],
        "inquiry": ["문의", "궁금", "알고싶", "확인", "정보"],
        "request": ["요청", "부탁", "도움", "처리", "해결"],
        "greeting": ["안녕", "처음", "반가", "감사"]
    }
    
    query_lower = query.lower()
    
    # 복잡도 계산
    high_count = sum(1 for indicator in complexity_indicators["high"] if indicator in query_lower)
    medium_count = sum(1 for indicator in complexity_indicators["medium"] if indicator in query_lower)
    low_count = sum(1 for indicator in complexity_indicators["low"] if indicator in query_lower)
    
    # 길이 기반 복잡도 조정
    length_factor = len(query)
    
    if high_count >= 2 or (high_count >= 1 and length_factor > 30):
        complexity = "high"
    elif high_count >= 1 or medium_count >= 2 or length_factor > 50:
        complexity = "medium"
    elif low_count >= 1 and length_factor < 20:
        complexity = "low"
    else:
        complexity = "medium"  # 기본값
    
    # 긴급도 분석
    urgency_high = sum(1 for indicator in urgency_indicators["high"] if indicator in query_lower)
    urgency_medium = sum(1 for indicator in urgency_indicators["medium"] if indicator in query_lower)
    
    if urgency_high >= 1:
        urgency = "high"
    elif urgency_medium >= 1:
        urgency = "medium"
    else:
        urgency = "low"
    
    # 질문 유형 분석
    question_type = "general"
    for q_type, indicators in question_types.items():
        if any(indicator in query_lower for indicator in indicators):
            question_type = q_type
            break
    
    return {
        "complexity": complexity,
        "type": question_type,
        "urgency": urgency,
        "length": length_factor,
        "indicators": {
            "high": high_count,
            "medium": medium_count,
            "low": low_count
        }
    }

def _select_optimal_mode(complexity: str, question_type: str, urgency: str, has_faq: bool) -> str:
    """최적 모드 자동 선택"""
    
    # 인사말이나 간단한 확인 질문
    if question_type == "greeting" and complexity == "low":
        return "basic"
    
    # FAQ가 있는 간단한 질문
    if has_faq and complexity == "low":
        return "basic"
    
    # 불만이나 긴급한 상황
    if question_type == "complaint" or urgency == "high":
        return "enhanced"  # 가장 신중한 모드
    
    # 복잡도 기반 선택
    if complexity == "high":
        return "enhanced"
    elif complexity == "medium":
        return "thinking"
    else:
        return "basic"

def _generate_thinking_response_with_mode(history: List[Dict[str, str]], mode: str) -> str:
    """지정된 모드로 Sequential Thinking 응답 생성"""
    try:
        latest_query = history[-1]["content"]
        
        # FAQ 검색 및 컨텍스트 구성
        faq_answer = _search_faq(latest_query)
        conversation_context = _build_conversation_context(history)
        
        # 모드별 프롬프트 구성
        if mode == "enhanced":
            context = f"""
{KENOPI_THINKING_PROMPT}

{EMOTION_RESPONSIVE_PROMPT}

{QUALITY_ASSURANCE_PROMPT}

**🔍 고급 분석 모드 활성화**
- 복잡한 문의나 중요한 상황으로 판단됨
- 다각도 검토 및 최적 솔루션 제시
- 고객 만족도 최우선 고려

대화 히스토리:
{conversation_context}

FAQ 매칭 결과:
{faq_answer if faq_answer else "매칭되는 FAQ 없음"}
            """.strip()
        else:  # thinking mode
            context = f"""
{KENOPI_THINKING_PROMPT}

{EMOTION_RESPONSIVE_PROMPT}

**🧠 단계별 추론 모드 활성화**
- 체계적인 분석을 통한 정확한 답변
- 단계별 사고 과정 적용

대화 히스토리:
{conversation_context}

FAQ 매칭 결과:
{faq_answer if faq_answer else "매칭되는 FAQ 없음"}
            """.strip()
        
        # MCP Sequential Thinking 분석 및 응답
        result = thinking_mcp.analyze_and_respond(latest_query, context)
        
        if result["thinking_used"]:
            response = result["response"]
            # 품질 검증
            if _validate_response_quality(response, latest_query):
                return _enhance_response_with_mode_info(response, mode)
            else:
                return _generate_basic_response(history)
        else:
            # Fallback to basic response
            return _generate_basic_response(history)
            
    except Exception as e:
        print(f"[Thinking Response Error] {e}")
        return _generate_basic_response(history)

def _enhance_response_with_mode_info(response: str, mode: str) -> str:
    """응답에 선택된 모드 정보 추가"""
    
    mode_info = {
        "basic": "💬 기본 모드",
        "thinking": "🧠 추론 모드", 
        "enhanced": "⚡ 고급 모드"
    }
    
    # 응답이 충분히 길면 모드 정보 추가하지 않음 (자연스러운 대화를 위해)
    if len(response) > 200:
        return response
    
    # 간단한 응답인 경우 모드 정보 추가
    if "고객센터" not in response and len(response) < 150:
        response += f"\n\n💡 **추가 도움이 필요하시면:**\n케노피 고객센터 📞 1588-1234 (평일 9시-18시)\n더 궁금한 사항이 있으시면 언제든 말씀해 주세요!"
    
    return response

def _generate_basic_response(history: List[Dict[str, str]]) -> str:
    """기존 방식의 기본 응답 생성 (Fallback)"""
    if not llm:
        # OpenAI가 없으면 FAQ 기반 응답
        if history:
            latest_query = history[-1]["content"]
            faq_result = _search_faq(latest_query)
            if faq_result:
                return f"안녕하세요! 노피🤖입니다. 😊\n\n{faq_result['answer']}"
        
        return _get_rejection_response(history[-1]["content"] if history else "")
    
    messages = [SystemMessage(content=KENOPI_SYSTEM_PROMPT)]
    
    for m in history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))

    # FAQ 검색 및 컨텍스트 추가
    if history:
        faq_answer = _search_faq(history[-1]["content"])
        if faq_answer:
            messages.insert(1, SystemMessage(content=f"FAQ 참고 답변:\n{faq_answer}"))

    # LLM 호출 및 응답 생성
    answer = llm.invoke(messages)
    return answer.content

def _build_conversation_context(history: List[Dict[str, str]]) -> str:
    """대화 히스토리를 컨텍스트로 구성"""
    if not history:
        return "첫 번째 문의입니다."
    
    context_parts = []
    # 최근 4개 대화만 포함 (컨텍스트 크기 제한)
    recent_history = history[-8:] if len(history) > 8 else history
    
    for i, msg in enumerate(recent_history):
        role = "고객" if msg["role"] == "user" else "케노피"
        context_parts.append(f"{role}: {msg['content']}")
    
    return "\n".join(context_parts)

def _validate_response_quality(response: str, query: str) -> bool:
    """응답 품질 기본 검증"""
    try:
        # 기본 품질 체크
        if not response or len(response.strip()) < 10:
            return False
        
        # 케노피 관련 컨텍스트 포함 여부
        kenopi_indicators = ["케노피", "고객", "도움", "안내", "문의", "서비스"]
        has_context = any(indicator in response for indicator in kenopi_indicators)
        
        # 적절한 길이 (너무 짧거나 너무 길지 않음)
        length_ok = 20 <= len(response) <= 1000
        
        return has_context and length_ok
        
    except Exception:
        return False

# 고급 응답 함수도 자동 모드 선택 지원
def generate_advanced_response(history: list[dict[str, str]]) -> Dict[str, Any]:
    """
    자동 모드 선택 기반 고급 응답 생성 (분석 정보 포함)
    """
    if not history:
        return {
            "response": "안녕하세요! 케노피 AI 고객지원팀입니다. 🧠 질문 복잡도에 따라 자동으로 최적의 방식으로 답변드리겠습니다.",
            "selected_mode": "auto",
            "complexity": "low",
            "quality_score": "high",
            "auto_selection": True
        }
    
    if not THINKING_AVAILABLE:
        return {
            "response": _generate_basic_response(history),
            "selected_mode": "basic",
            "complexity": "unknown",
            "quality_score": "basic",
            "auto_selection": False,
            "note": "Sequential Thinking 비활성화"
        }
    
    try:
        latest_query = history[-1]["content"]
        
        # 상세 분석
        complexity_analysis = _analyze_query_complexity_detailed(latest_query)
        complexity = complexity_analysis["complexity"]
        question_type = complexity_analysis["type"]
        urgency = complexity_analysis["urgency"]
        
        # FAQ 및 컨텍스트 구성
        faq_answer = _search_faq(latest_query)
        conversation_context = _build_conversation_context(history)
        
        # 자동 모드 선택
        selected_mode = _select_optimal_mode(complexity, question_type, urgency, bool(faq_answer))
        
        # 선택된 모드로 응답 생성
        if selected_mode == "basic":
            response = _generate_basic_response(history)
        else:
            response = _generate_thinking_response_with_mode(history, selected_mode)
        
        return {
            "response": response,
            "selected_mode": selected_mode,
            "complexity": complexity,
            "question_type": question_type,
            "urgency": urgency,
            "quality_score": "enhanced" if selected_mode in ["thinking", "enhanced"] else "basic",
            "faq_matched": bool(faq_answer),
            "auto_selection": True,
            "analysis": {
                "length": complexity_analysis["length"],
                "indicators": complexity_analysis["indicators"]
            }
        }
        
    except Exception as e:
        print(f"[Advanced Response Error] {e}")
        return {
            "response": _generate_basic_response(history),
            "selected_mode": "basic",
            "complexity": "error",
            "quality_score": "fallback",
            "auto_selection": False,
            "error": str(e)
        }