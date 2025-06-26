"""
MCP Sequential Thinking Tools 통합 유틸리티
Smithery에서 다운받은 Sequential Thinking Tools 활용
"""

import subprocess
import json
import os
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SequentialThinkingMCP:
    """MCP Sequential Thinking Tools와의 간단한 인터페이스"""
    
    def __init__(self):
        self.mcp_available = self._check_mcp_availability()
        
    def _check_mcp_availability(self) -> bool:
        """MCP Sequential Thinking Tools 사용 가능성 확인"""
        try:
            # mcp.json 파일 존재 확인
            mcp_config = os.path.join(os.path.dirname(__file__), '..', 'mcp.json')
            if not os.path.exists(mcp_config):
                logger.warning("mcp.json not found")
                return False
            
            # 환경변수 확인
            if not os.getenv('OPENAI_API_KEY'):
                logger.warning("OPENAI_API_KEY not set")
                return False
                
            return True
        except Exception as e:
            logger.error(f"MCP availability check failed: {e}")
            return False
    
    def think_step_by_step(self, query: str, context: str = "") -> str:
        """단계별 사고를 통한 응답 생성"""
        if not self.mcp_available:
            return self._fallback_response(query, context)
        
        try:
            # MCP Sequential Thinking 호출
            thinking_prompt = f"""
당신은 케노피(Kenopi) 생활용품 브랜드의 전문 고객지원 담당자입니다.

다음 단계로 생각해주세요:

1. 🔍 고객 질문 분석
   - 고객이 실제로 원하는 것은 무엇인가요?
   - 어떤 감정 상태인가요? (불만, 궁금, 걱정 등)

2. 💡 최적 해결책 탐색
   - 케노피 정책에 맞는 해결 방법은?
   - 고객에게 가장 도움이 되는 방법은?

3. ✨ 친절한 응답 구성
   - 이해하기 쉬운 설명
   - 구체적인 행동 지침
   - 추가 도움 제안

컨텍스트: {context}
고객 질문: {query}

단계별로 생각하여 친절하고 정확한 답변을 만들어주세요.
"""
            
            result = self._call_mcp_tool(thinking_prompt)
            return result.get('final_answer', self._fallback_response(query, context))
            
        except Exception as e:
            logger.error(f"MCP thinking failed: {e}")
            return self._fallback_response(query, context)
    
    def analyze_and_respond(self, query: str, context: str = "") -> Dict[str, Any]:
        """질문 분석 후 최적 응답 생성"""
        if not self.mcp_available:
            return {
                "response": self._fallback_response(query, context),
                "thinking_used": False,
                "complexity": "unknown"
            }
        
        try:
            # 복잡도 분석
            complexity = self._analyze_complexity(query)
            
            # 복잡도에 따른 사고 방식 선택
            if complexity == "high":
                result = self._enhanced_thinking(query, context)
            elif complexity == "medium":
                result = self.think_step_by_step(query, context)
            else:
                result = self._quick_thinking(query, context)
            
            return {
                "response": result,
                "thinking_used": True,
                "complexity": complexity
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "response": self._fallback_response(query, context),
                "thinking_used": False,
                "complexity": "error"
            }
    
    def _analyze_complexity(self, query: str) -> str:
        """질문 복잡도 분석"""
        complex_indicators = [
            "어떻게", "왜", "방법", "절차", "단계", "비교", "차이", 
            "장단점", "문제해결", "환불", "교환", "불량"
        ]
        
        query_lower = query.lower()
        complex_count = sum(1 for indicator in complex_indicators if indicator in query_lower)
        
        if complex_count >= 2 or len(query) > 50:
            return "high"
        elif complex_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _enhanced_thinking(self, query: str, context: str) -> str:
        """복잡한 문제에 대한 향상된 사고"""
        enhanced_prompt = f"""
복잡한 고객 문의를 해결하기 위해 다음과 같이 종합적으로 접근하세요:

🔍 **문제 분석**
- 고객의 정확한 니즈 파악
- 관련된 케노피 정책 검토
- 가능한 해결 옵션들 나열

💭 **다각도 검토**
방법 A: 즉시 해결 가능한 방법
방법 B: 단계적 해결 방법
방법 C: 장기적 만족도를 위한 방법

✅ **최적 솔루션 선택**
- 고객에게 가장 유리한 방법
- 실행 가능성 검토
- 명확한 안내

컨텍스트: {context}
고객 문의: {query}

각 단계를 거쳐 최고의 고객 경험을 제공하는 답변을 만들어주세요.
"""
        
        result = self._call_mcp_tool(enhanced_prompt)
        return result.get('final_answer', self._fallback_response(query, context))
    
    def _quick_thinking(self, query: str, context: str) -> str:
        """간단한 질문에 대한 빠른 응답"""
        quick_prompt = f"""
케노피 고객지원 담당자로서 다음 질문에 친절하고 정확하게 답변해주세요:

질문: {query}
컨텍스트: {context}

응답 시 다음을 포함해주세요:
- 명확하고 이해하기 쉬운 설명
- 필요한 경우 구체적인 절차 안내
- 추가 도움이 필요한지 문의
"""
        
        result = self._call_mcp_tool(quick_prompt)
        return result.get('final_answer', self._fallback_response(query, context))
    
    def _call_mcp_tool(self, prompt: str) -> Dict[str, Any]:
        """MCP Sequential Thinking Tool 호출"""
        try:
            # MCP 도구를 사용한 추론 호출
            # 실제 MCP 서버와 통신하는 부분
            mcp_request = {
                "thought": prompt,
                "next_thought_needed": True,
                "thought_number": 1,
                "total_thoughts": 5
            }
            
            # MCP 서버 호출 (subprocess를 통한 npx 실행)
            cmd = [
                "npx", "-y", "@smithery/sequential-thinking-tools",
                "--input", json.dumps(mcp_request)
            ]
            
            env = os.environ.copy()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if result.returncode == 0:
                # 성공적인 응답 파싱
                response_data = json.loads(result.stdout)
                return response_data
            else:
                logger.error(f"MCP tool error: {result.stderr}")
                return {"final_answer": ""}
                
        except subprocess.TimeoutExpired:
            logger.error("MCP tool timeout")
            return {"final_answer": ""}
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return {"final_answer": ""}
    
    def _fallback_response(self, query: str, context: str) -> str:
        """MCP 실패 시 기본 응답"""
        return f"""안녕하세요! 케노피 고객지원팀입니다.

고객님의 문의: "{query}"

죄송하지만 현재 시스템에 일시적인 문제가 있어 상세한 분석이 어렵습니다. 
하지만 최선을 다해 도움을 드리겠습니다.

{context}

추가 문의사항이 있으시면 언제든 말씀해 주세요.
더 정확한 답변이 필요하시면 고객센터(1588-1234)로 연락 주시기 바랍니다."""

# 전역 인스턴스
thinking_mcp = SequentialThinkingMCP() 