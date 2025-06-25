from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import os
from difflib import SequenceMatcher
import csv
from pathlib import Path

from kenopi_prompt import KENOPI_SYSTEM_PROMPT

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

llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-3.5-turbo",
    temperature=0.5,
)

# Load FAQ dataset at import time
FAQ_PATH = Path(__file__).parent / "data" / "kenopi_faq.csv"
FAQ_LIST = []
if FAQ_PATH.exists():
    with FAQ_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("question") and row.get("answer"):
                FAQ_LIST.append({"question": row["question"], "answer": row["answer"]})

SIM_THRESHOLD = 0.5

def _search_faq(query: str):
    """FAQ에서 유사한 질문을 찾아 답변 반환"""
    best = None
    best_score = 0
    for item in FAQ_LIST:
        score = SequenceMatcher(None, query.lower(), item["question"].lower()).ratio()
        if score > best_score:
            best_score = score
            best = item
    if best_score >= SIM_THRESHOLD:
        return best["answer"]
    return None

def generate_response(history: list[dict[str, str]]) -> str:
    """
    케노피 CS 챗봇 응답 생성
    history: [{role: 'user'|'bot', content: str}, ...]
    """
    messages = [SystemMessage(content=KENOPI_SYSTEM_PROMPT)]
    
    # 대화 히스토리를 LangChain 메시지로 변환
    for m in history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))

    # FAQ 검색 및 컨텍스트 추가
    if history:
        faq_answer = _search_faq(history[-1]["content"])
        if faq_answer:
            messages.insert(1, SystemMessage(content=f"다음은 자주 묻는 질문에 대한 답변입니다:\n{faq_answer}"))

    # LLM 호출 및 응답 생성
    answer = llm.invoke(messages)
    return answer.content