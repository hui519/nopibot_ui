#!/usr/bin/env python3
"""
자동 모드 선택 데모 스크립트
다양한 질문 유형으로 AI의 자동 모드 선택 기능을 테스트
"""

import requests
import time
import json

# 테스트할 다양한 질문들
TEST_QUESTIONS = [
    {
        "query": "안녕하세요",
        "expected_mode": "basic",
        "category": "인사말"
    },
    {
        "query": "감사합니다",
        "expected_mode": "basic", 
        "category": "간단한 감사"
    },
    {
        "query": "배송 기간이 얼마나 걸리나요?",
        "expected_mode": "thinking",
        "category": "일반 문의"
    },
    {
        "query": "제품 가격은 어떻게 되나요?",
        "expected_mode": "thinking",
        "category": "정보 요청"
    },
    {
        "query": "제품이 불량인데 환불과 교환 중 어떤 게 더 유리한가요?",
        "expected_mode": "enhanced",
        "category": "복잡한 상황"
    },
    {
        "query": "급하게 처리해주세요! 제품에 문제가 있어요!",
        "expected_mode": "enhanced",
        "category": "긴급 상황"
    },
    {
        "query": "케노피 제품 AS 정책에 대해 자세히 설명해주세요. 보증 기간은 어떻게 되고, 어떤 경우에 무료 수리가 가능한지, 그리고 유료 수리는 언제 필요한지 알고 싶습니다.",
        "expected_mode": "enhanced",
        "category": "복잡한 정책 문의"
    },
    {
        "query": "주문 취소하고 싶은데 어떻게 하나요?",
        "expected_mode": "thinking",
        "category": "절차 문의"
    },
    {
        "query": "화가 나요! 왜 이렇게 서비스가 별로인가요?",
        "expected_mode": "enhanced",
        "category": "불만 제기"
    },
    {
        "query": "연락처 알려주세요",
        "expected_mode": "basic",
        "category": "단순 정보"
    }
]

def test_auto_mode_selection():
    """자동 모드 선택 테스트"""
    base_url = "http://localhost:8000"
    
    print("🎯 자동 모드 선택 데모 테스트")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        print(f"\n📝 테스트 {i}: {test_case['category']}")
        print(f"질문: \"{test_case['query']}\"")
        print(f"예상 모드: {test_case['expected_mode']}")
        
        try:
            # API 호출
            start_time = time.time()
            response = requests.post(
                f"{base_url}/kenopi/chat/advanced",
                json={
                    "messages": [{"role": "user", "content": test_case['query']}]
                },
                timeout=30
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                selected_mode = data.get('selected_mode', 'unknown')
                complexity = data.get('complexity', 'unknown')
                question_type = data.get('question_type', 'unknown')
                urgency = data.get('urgency', 'unknown')
                quality_score = data.get('quality_score', 'unknown')
                
                # 결과 분석
                is_correct = selected_mode == test_case['expected_mode']
                status = "✅ 정확" if is_correct else "⚠️ 다름"
                
                print(f"🎯 선택된 모드: {selected_mode} {status}")
                print(f"📊 분석 결과:")
                print(f"   복잡도: {complexity}")
                print(f"   질문 유형: {question_type}")
                print(f"   긴급도: {urgency}")
                print(f"   품질 점수: {quality_score}")
                print(f"⏱️ 처리 시간: {processing_time:.3f}초")
                
                # 응답 일부 표시
                response_preview = data.get('response', '')[:100] + "..." if len(data.get('response', '')) > 100 else data.get('response', '')
                print(f"💬 응답 미리보기: {response_preview}")
                
                results.append({
                    "query": test_case['query'],
                    "category": test_case['category'],
                    "expected": test_case['expected_mode'],
                    "actual": selected_mode,
                    "correct": is_correct,
                    "complexity": complexity,
                    "question_type": question_type,
                    "urgency": urgency,
                    "processing_time": processing_time
                })
                
            else:
                print(f"❌ API 오류: {response.status_code}")
                results.append({
                    "query": test_case['query'],
                    "category": test_case['category'],
                    "expected": test_case['expected_mode'],
                    "actual": "error",
                    "correct": False,
                    "error": response.status_code
                })
                
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            results.append({
                "query": test_case['query'],
                "category": test_case['category'],
                "expected": test_case['expected_mode'],
                "actual": "error",
                "correct": False,
                "error": str(e)
            })
        
        # 서버 부하 방지를 위한 대기
        time.sleep(1)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 자동 모드 선택 테스트 결과 요약")
    print("=" * 60)
    
    correct_count = sum(1 for r in results if r.get('correct', False))
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"정확도: {correct_count}/{total_count} ({accuracy:.1f}%)")
    
    # 모드별 정확도
    mode_stats = {}
    for result in results:
        expected = result['expected']
        if expected not in mode_stats:
            mode_stats[expected] = {'total': 0, 'correct': 0}
        mode_stats[expected]['total'] += 1
        if result.get('correct', False):
            mode_stats[expected]['correct'] += 1
    
    print("\n📈 모드별 정확도:")
    for mode, stats in mode_stats.items():
        accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"   {mode}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
    
    # 처리 시간 통계
    processing_times = [r['processing_time'] for r in results if 'processing_time' in r]
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        print(f"\n⏱️ 처리 시간 통계:")
        print(f"   평균: {avg_time:.3f}초")
        print(f"   최대: {max_time:.3f}초")
        print(f"   최소: {min_time:.3f}초")
    
    # 틀린 예측 분석
    incorrect_results = [r for r in results if not r.get('correct', False) and 'error' not in r]
    if incorrect_results:
        print("\n⚠️ 예측이 틀린 케이스:")
        for result in incorrect_results:
            print(f"   \"{result['query'][:50]}...\" -> 예상: {result['expected']}, 실제: {result['actual']}")
    
    print(f"\n🎯 전체 성능: {'우수' if accuracy >= 80 else '보통' if accuracy >= 60 else '개선 필요'}")
    
    return results

def test_demo_api():
    """데모 API 테스트"""
    base_url = "http://localhost:8000"
    
    print("\n🚀 데모 API 테스트")
    print("=" * 40)
    
    try:
        # 예시 API 확인
        response = requests.get(f"{base_url}/kenopi/thinking/examples")
        if response.status_code == 200:
            examples = response.json()
            print("✅ 예시 API 정상 작동")
            print("📋 제공되는 예시들:")
            for example in examples.get('examples', []):
                print(f"   \"{example['query']}\" -> {example['expected_mode']} ({example['reason']})")
        
        # 상태 API 확인
        response = requests.get(f"{base_url}/kenopi/thinking/status")
        if response.status_code == 200:
            status = response.json()
            print("\n✅ 상태 API 정상 작동")
            auto_mode = status.get('auto_mode_selection', {})
            print(f"   자동 모드 선택: {'활성화' if auto_mode.get('enabled') else '비활성화'}")
            
            modes = status.get('available_modes', {})
            print("   사용 가능한 모드:")
            for mode_key, mode_info in modes.items():
                print(f"     {mode_info.get('icon', '')} {mode_info.get('name', mode_key)}: {mode_info.get('description', '')}")
        
    except Exception as e:
        print(f"❌ 데모 API 테스트 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🎯 케노피 자동 모드 선택 시스템 데모")
    print("=" * 50)
    
    # 서버 연결 확인
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            print("❌ FastAPI 서버가 실행되지 않았습니다.")
            print("   먼저 서버를 시작하세요: cd backend && uvicorn main:app --reload")
            return
    except:
        print("❌ FastAPI 서버에 연결할 수 없습니다.")
        print("   먼저 서버를 시작하세요: cd backend && uvicorn main:app --reload")
        return
    
    print("✅ 서버 연결 확인")
    
    # 데모 API 테스트
    test_demo_api()
    
    # 자동 모드 선택 테스트
    results = test_auto_mode_selection()
    
    print("\n🎉 데모 완료!")
    print("\n💡 실제 사용 시:")
    print("1. 프론트엔드 실행: cd frontend && npm run dev")
    print("2. http://localhost:3000 에서 자동 모드 선택 체험")
    print("3. '상세히' 버튼으로 AI의 분석 과정 확인 가능")

if __name__ == "__main__":
    main() 