# Kenopi CS 챗봇 실행 가이드

## 🛠️ 개발 환경

```bash
# 백엔드 (FastAPI)
cd backend
uv run uvicorn main:app --reload           # http://localhost:8000

# 프런트엔드 (Next.js)
cd frontend
npm run dev                         # http://localhost:3000
```

## 🚀 운영 환경

```bash
# Docker Compose (백엔드)
docker compose up --build -d        # 8000 포트 노출

# 또는 개별 이미지 실행
cd backend
docker build -t nopibot-backend .
docker run -d -p 8000:8000 --env-file ../.env nopibot-backend
```

## 📋 API 엔드포인트

- `POST /kenopi/chat`: 케노피 CS 전용 챗봇 (FAQ + AI 응답)
- `POST /chat`: 일반 채팅 (케노피 CS 안내 메시지만 반환)
- `GET /health`: 시스템 상태 확인

> `.env` 파일에 `OPENAI_API_KEY`, `LANGSMITH_API_KEY` 등을 설정한 뒤 실행하세요. 