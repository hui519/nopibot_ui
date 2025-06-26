#!/bin/bash

# GCP 케노피 챗봇 배포 스크립트
set -e

# 설정 변수들
PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
REGION=${GCP_REGION:-"asia-northeast3"}  # 서울 리전
SERVICE_NAME_BACKEND="kenopi-backend"
SERVICE_NAME_FRONTEND="kenopi-frontend"

echo "🚀 케노피 챗봇 GCP 배포 시작..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# 1. Docker 이미지 빌드 및 푸시
echo "📦 Docker 이미지 빌드 중..."

# 백엔드 이미지 빌드
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME_BACKEND:latest ./backend

# 프론트엔드 이미지 빌드  
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest ./frontend

echo "🔼 Docker 이미지 푸시 중..."

# 이미지 푸시
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME_BACKEND:latest
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest

# 2. Cloud Run에 백엔드 배포
echo "🎯 백엔드 Cloud Run 배포 중..."
gcloud run deploy $SERVICE_NAME_BACKEND \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME_BACKEND:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="PYTHONUNBUFFERED=1" \
  --project $PROJECT_ID

# 백엔드 URL 가져오기
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME_BACKEND --region $REGION --format 'value(status.url)' --project $PROJECT_ID)
echo "✅ 백엔드 배포 완료: $BACKEND_URL"

# 3. Cloud Run에 프론트엔드 배포
echo "🎯 프론트엔드 Cloud Run 배포 중..."
gcloud run deploy $SERVICE_NAME_FRONTEND \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME_FRONTEND:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 3000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="NODE_ENV=production,NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --project $PROJECT_ID

# 프론트엔드 URL 가져오기
FRONTEND_URL=$(gcloud run services describe $SERVICE_NAME_FRONTEND --region $REGION --format 'value(status.url)' --project $PROJECT_ID)
echo "✅ 프론트엔드 배포 완료: $FRONTEND_URL"

echo ""
echo "🎉 배포 완료!"
echo "🌐 프론트엔드: $FRONTEND_URL"
echo "🔧 백엔드 API: $BACKEND_URL"
echo ""
echo "📝 환경변수 설정이 필요한 경우:"
echo "gcloud run services update $SERVICE_NAME_BACKEND --set-env-vars='OPENAI_API_KEY=your-key' --region $REGION" 