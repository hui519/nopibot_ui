# 🤖 Kenopi CS Chatbot - 할루시네이션 방지 시스템

케노피(Kenopi) 스타일링 양우산 브랜드의 **할루시네이션 완전 차단** CS 챗봇입니다.

## 🎯 핵심 특징

### ✨ **의도 파악 & 확인 시스템**
- **17가지 의도 자동 파악**: 환불, 교환, 반품, 배송비, 고객센터, 스크래치 등
- **확인 질문 시스템**: "환불하고 싶어" → "환불 정책이 궁금하신가요?"
- **100% 할루시네이션 차단**: FAQ에 없는 정보는 절대 생성하지 않음

### 🚀 **기술 스택**
- **Backend**: FastAPI + Python 3.11
- **Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind CSS
- **AI Model**: GPT-4o (OpenAI API 키 없어도 FAQ 기반 작동)
- **UI Components**: Shadcn/ui

## 📋 **사용 예시**

```
👤 사용자: "환불하고 싶어"
🤖 노피: "환불 정책이 궁금하신가요? (네/예 라고 답해주시면 자세히 안내해드릴게요!)"

👤 사용자: "네"
🤖 노피: "네, 알려드릴게요! 😊
상품 수령 후 7일 이내에 교환 또는 반품 의사를 알려주신 경우, 
상품 회수 후 3~5일 이내 결제하신 방법으로 환불됩니다. 
단, 단순 변심의 경우 배송비는 고객님 부담입니다."
```

## 🛠️ **설치 및 실행**

### 🖥️ **로컬 개발 환경**

#### 1. 프로젝트 클론
```bash
git clone https://github.com/YOUR_USERNAME/nopibot_ui.git
cd nopibot_ui
```

#### 2. 백엔드 설정 (uv 사용)
```bash
cd backend
# uv로 의존성 설치
uv sync

# 환경변수 설정 (선택사항)
export OPENAI_API_KEY="your-openai-api-key"  # 없어도 FAQ 기반으로 작동

# 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 프론트엔드 설정
```bash
cd ../frontend
npm install

# 개발 서버 실행
npm run dev
```

#### 4. 접속
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 🐳 **Docker 실행**

```bash
# Docker Compose로 전체 스택 실행
docker-compose up --build

# 개별 서비스 실행
docker-compose up backend  # 백엔드만
docker-compose up frontend # 프론트엔드만
```

### ☁️ **GCP 배포**

#### 사전 준비
1. **GCP 프로젝트 생성** 및 결제 활성화
2. **gcloud CLI 설치** 및 인증
3. **Docker 설치** 및 실행

#### 배포 실행
```bash
# 환경변수 설정
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_REGION="asia-northeast3"  # 서울 리전

# 배포 스크립트 실행
./deploy.sh
```

#### 환경변수 설정 (배포 후)
```bash
# OpenAI API 키 설정
gcloud run services update kenopi-backend \
  --set-env-vars='OPENAI_API_KEY=your-openai-api-key' \
  --region asia-northeast3

# LangSmith 설정 (선택사항)
gcloud run services update kenopi-backend \
  --set-env-vars='LANGSMITH_API_KEY=your-langsmith-key,LANGSMITH_PROJECT=kenopi-cs' \
  --region asia-northeast3
```

#### GCP 리소스 정리
```bash
# Cloud Run 서비스 삭제
gcloud run services delete kenopi-backend --region asia-northeast3
gcloud run services delete kenopi-frontend --region asia-northeast3

# Container Registry 이미지 삭제
gcloud container images delete gcr.io/PROJECT_ID/kenopi-backend:latest
gcloud container images delete gcr.io/PROJECT_ID/kenopi-frontend:latest
```

## 🎨 **주요 기능**

### 🧠 **의도 파악 시스템**
17가지 의도를 키워드 기반으로 정확하게 파악:
- **환불**: 환불, 돈, 돌려, 취소, 안받, 반납
- **교환**: 교환, 바꾸, 다른걸로, 사이즈, 색깔
- **반품**: 반품, 보내, 돌려보내, 안받, 취소
- **배송비**: 배송비, 택배비, 비용, 얼마, 가격
- **고객센터**: 연락, 전화, 문의, 고객센터, 상담
- **스크래치**: 스크래치, 긁힘, 상처, 흠집
- 기타 12가지 의도...

### ✅ **확인 응답 처리**
- "네", "예", "맞아요", "그렇습니다" 등 긍정 응답 자동 인식
- 이전 봇 메시지에서 의도 추출하여 정확한 FAQ 답변 제공

### 🚫 **할루시네이션 방지**
1. **정확한 FAQ 매칭** (유사도 0.8 이상)
2. **의도 파악 및 확인 질문**
3. **FAQ 기반 답변 제공**
4. **의도 파악 실패 시 정중한 거절**

## 📊 **API 엔드포인트**

### 기본 채팅
```bash
POST /kenopi/chat
{
  "messages": [
    {"role": "user", "content": "환불하고 싶어"}
  ]
}
```

### 고급 분석 (디버그용)
```bash
POST /kenopi/chat/advanced
# 의도 파악 과정과 분석 정보 포함
```

### 시스템 상태 확인
```bash
GET /kenopi/thinking/status
# 자동 모드 선택 시스템 상태
```

## 📁 **프로젝트 구조**

```
nopibot_ui/
├── backend/
│   ├── data/
│   │   └── kenopi_faq.csv           # FAQ 데이터베이스 (23개 항목)
│   ├── routers/
│   │   └── kenopi.py                # API 라우터
│   ├── kenopi_chatbot.py            # 핵심 챗봇 로직
│   ├── kenopi_prompt.py             # 프롬프트 시스템
│   ├── main.py                      # FastAPI 앱
│   └── requirements.txt             # Python 의존성
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # 루트 레이아웃
│   │   └── page.tsx                 # 메인 페이지
│   ├── src/
│   │   └── Chatbot.tsx              # 채팅 인터페이스
│   ├── components/ui/               # UI 컴포넌트
│   └── package.json                 # Node.js 의존성
└── README.md
```

## 🎯 **테스트 케이스**

### ✅ 성공 케이스
- **"환불하고 싶어"** → 의도 파악 → 확인 질문 → FAQ 답변
- **"고객센터 연락처"** → 의도 파악 → 확인 질문 → FAQ 답변
- **"스크래치 난 제품"** → 의도 파악 → 확인 질문 → FAQ 답변

### 🚫 할루시네이션 방지
- **"케노피에서 스마트폰도 파나요?"** → 브랜드 의도 파악 → 확인 질문
- **"우주선 배송 가능한가요?"** → 의도 파악 실패 → 정중한 거절

## 🔧 **개발자 정보**

- **개발 환경**: macOS, Python 3.11, Node.js 18+
- **디버그 로그**: 터미널에서 의도 파악 과정 실시간 확인 가능
- **확장성**: 새로운 의도 추가 시 `intent_keywords` 딕셔너리만 수정

## 📞 **고객센터 정보**

- **전화번호**: 010-2747-9567
- **운영시간**: 평일 10시-17시
- **브랜드**: 케노피(Kenopi) - 스타일링 양우산 전문

---

**할루시네이션 Zero, 고객 만족 100%** 🎊 