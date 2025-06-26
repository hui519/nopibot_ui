FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# 환경변수 설정
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies only (not the project itself)
RUN uv sync --no-install-project --frozen

# Copy source code
COPY . .

# Install the project itself
RUN uv sync --frozen

EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 프로덕션 환경에서는 reload 없이 실행
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]