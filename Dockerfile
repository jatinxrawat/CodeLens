# ==========================================
# Stage 1: Build React TypeScript Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python Backend & Final Image
# ==========================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install system build dependencies and git for GitPython
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and test fixtures
COPY app/ ./app/
COPY tests/ ./tests/
COPY pyproject.toml .env.example README.md ./

# Create data directories
RUN mkdir -p data/repositories data/indexes

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /build/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
