# Stage 1: build the Next.js static export
FROM node:22-alpine AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

# Stage 2: Python runtime serving API + static site
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir .

COPY specs/ specs/
COPY data/ data/
COPY evals/ evals/
COPY --from=web /web/out apps/web/out

RUN useradd -m -u 1000 user && chown -R user /app
USER user
ENV STATIC_DIR=/app/apps/web/out
EXPOSE 7860

# Bind to the platform-injected PORT (Render) with 7860 as the local default
CMD ["sh", "-c", "uvicorn earned_media.api.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
