#!/usr/bin/env python3
"""
MCP Sequential Thinking Tools 통합 테스트 스크립트
케노피 챗봇의 Sequential Thinking 기능 검증
"""

import sys
import os
import json
from pathlib import Path

# 백엔드 경로 추가
sys.path.append(str(Path(__file__).parent / "backend"))

def test_mcp_availability():
    """MCP 사용 가능성 테스트"""
    print("🔍 MCP Sequential Thinking Tools 사용 가능성 검사...")
    
    try:
        from backend.sequential_thinking_mcp import thinking_mcp
        
        if thinking_mcp.mcp_available:
            print("✅ MCP Sequential Thinking Tools 사용 가능")
            return True
        else:
            print("❌ MCP Sequential Thinking Tools 사용 불가")
            print("   - mcp.json 파일 확인")
            print("   - OPENAI_API_KEY 환경변수 확인")
            return False
            
    except ImportError as e:
        print(f"❌ MCP 모듈 임포트 실패: {e}")
        return False

def test_basic_thinking():
    """기본 사고 기능 테스트"""
    print("\n🧠 기본 Sequential Thinking 기능 테스트...")
    
    try:
        from backend.sequential_thinking_mcp import thinking_mcp
        
        test_query = "케노피 제품 환불 방법을 알려주세요"
        test_context = "고객이 환불 절차에 대해 문의했습니다."
        
        result = thinking_mcp.analyze_and_respond(test_query, test_context)
        
        if result["thinking_used"]:
            print("✅ Sequential Thinking 정상 작동")
            print(f"   복잡도: {result.get('complexity', 'unknown')}")
            print(f"   응답 길이: {len(result.get('response', ''))}")
            return True
        else:
            print("⚠️ Sequential Thinking 비활성화 - Fallback 모드 사용")
            return False
            
    except Exception as e:
        print(f"❌ Sequential Thinking 테스트 실패: {e}")
        return False

def test_chatbot_integration():
    """챗봇 통합 테스트"""
    print("\n🤖 챗봇 통합 테스트...")
    
    try:
        from backend.kenopi_chatbot import generate_response, generate_advanced_response
        
        test_messages = [
            {"role": "user", "content": "안녕하세요!"},
            {"role": "bot", "content": "안녕하세요! 케노피 고객지원팀입니다."},
            {"role": "user", "content": "제품 교환은 어떻게 하나요?"}
        ]
        
        # 기본 응답 테스트
        basic_response = generate_response(test_messages, use_thinking=False)
        if basic_response:
            print("✅ 기본 응답 모드 정상 작동")
        
        # Sequential Thinking 응답 테스트
        thinking_response = generate_response(test_messages, use_thinking=True)
        if thinking_response:
            print("✅ Sequential Thinking 모드 정상 작동")
        
        # 고급 응답 테스트
        advanced_result = generate_advanced_response(test_messages)
        if advanced_result and advanced_result.get("response"):
            print("✅ 고급 분석 모드 정상 작동")
            if advanced_result.get("thinking_process"):
                print("   - 사고 과정 분석 포함")
            if advanced_result.get("complexity"):
                print(f"   - 복잡도 분석: {advanced_result['complexity']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 챗봇 통합 테스트 실패: {e}")
        return False

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("\n🌐 API 엔드포인트 테스트...")
    
    try:
        import requests
        import time
        
        base_url = "http://localhost:8000"
        
        # 서버 실행 여부 확인
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI 서버 실행 중")
            else:
                print("⚠️ FastAPI 서버 응답 이상")
                return False
        except requests.exceptions.RequestException:
            print("❌ FastAPI 서버 미실행 - 서버를 먼저 시작해주세요")
            print("   명령어: cd backend && uvicorn main:app --reload")
            return False
        
        # 상태 확인 API 테스트
        try:
            response = requests.get(f"{base_url}/kenopi/thinking/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                print("✅ Sequential Thinking 상태 API 정상")
                print(f"   상태: {status_data.get('status', 'unknown')}")
                
                # Sequential Thinking 기능 확인
                st_info = status_data.get('sequential_thinking', {})
                if st_info.get('available'):
                    print("   🧠 Sequential Thinking 사용 가능")
                else:
                    print("   ⚠️ Sequential Thinking 사용 불가")
            else:
                print("❌ 상태 API 응답 오류")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 상태 API 테스트 실패: {e}")
            return False
        
        # 챗봇 API 테스트
        try:
            test_payload = {
                "messages": [{"role": "user", "content": "테스트 메시지입니다"}]
                # auto_mode는 제거 - 항상 자동 모드 사용
            }
            
            response = requests.post(
                f"{base_url}/kenopi/chat",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                print("✅ 챗봇 API 정상 작동")
                print(f"   선택된 모드: {chat_data.get('selected_mode', 'unknown')}")
                print(f"   응답 길이: {len(chat_data.get('response', ''))}")
                
                # 고급 API도 테스트
                advanced_response = requests.post(
                    f"{base_url}/kenopi/chat/advanced",
                    json=test_payload,
                    timeout=30
                )
                
                if advanced_response.status_code == 200:
                    adv_data = advanced_response.json()
                    print("✅ 고급 API 정상 작동")
                    print(f"   자동 선택된 모드: {adv_data.get('selected_mode')}")
                    print(f"   복잡도: {adv_data.get('complexity')}")
                    print(f"   질문 유형: {adv_data.get('question_type')}")
                    
            else:
                print(f"❌ 챗봇 API 오류: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 챗봇 API 테스트 실패: {e}")
            return False
        
        return True
        
    except ImportError:
        print("⚠️ requests 모듈이 필요합니다: pip install requests")
        return False

def check_mcp_config():
    """MCP 설정 파일 검증"""
    print("\n📝 MCP 설정 파일 검증...")
    
    # mcp.json 파일 확인
    mcp_file = Path("mcp.json")
    if not mcp_file.exists():
        print("❌ mcp.json 파일이 없습니다")
        print("   Sequential Thinking Tools를 다운로드하고 설정하세요!")
        return False
    
    try:
        with open(mcp_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ mcp.json 파일 존재")
        
        # 설정 내용 확인
        tools = config.get('mcpServers', {})
        if 'sequential-thinking-tools' in tools:
            print("✅ Sequential Thinking Tools 설정 확인")
            
            tool_config = tools['sequential-thinking-tools']
            if 'command' in tool_config and 'args' in tool_config:
                print("✅ 실행 명령 설정 확인")
            else:
                print("⚠️ 실행 명령 설정 누락")
            
            if 'env' in tool_config:
                env_vars = tool_config['env']
                if 'OPENAI_API_KEY' in env_vars or 'ANTHROPIC_API_KEY' in env_vars:
                    print("✅ API 키 환경변수 설정 확인")
                else:
                    print("⚠️ API 키 환경변수 설정 누락")
        else:
            print("❌ Sequential Thinking Tools 설정 누락")
            return False
        
        return True
        
    except json.JSONDecodeError:
        print("❌ mcp.json 파일 형식 오류")
        return False
    except Exception as e:
        print(f"❌ mcp.json 검증 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 케노피 Sequential Thinking MCP 통합 테스트")
    print("=" * 50)
    
    tests = [
        ("MCP 설정 파일", check_mcp_config),
        ("MCP 사용 가능성", test_mcp_availability),
        ("Sequential Thinking 기능", test_basic_thinking),
        ("챗봇 통합", test_chatbot_integration),
        ("API 엔드포인트", test_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트 시작...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n전체 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! Sequential Thinking 챗봇이 준비되었습니다.")
        print("\n🚀 사용 방법:")
        print("1. 백엔드 서버 시작: cd backend && uvicorn main:app --reload")
        print("2. 프론트엔드 시작: cd frontend && npm run dev")
        print("3. http://localhost:3000 에서 챗봇 사용")
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패. 문제를 해결한 후 다시 테스트하세요.")
        print("\n💡 문제 해결 가이드:")
        print("- mcp.json 파일이 올바르게 설정되었는지 확인")
        print("- OPENAI_API_KEY 환경변수가 설정되었는지 확인") 
        print("- Sequential Thinking Tools가 설치되었는지 확인")
        print("- FastAPI 서버가 실행 중인지 확인")

if __name__ == "__main__":
    main() 