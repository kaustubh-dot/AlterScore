FROM python:3.12-slim

WORKDIR /code

# Install only the public v2 serving runtime.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Whitelist the serving application. Research source, training scripts, and
# model artifacts are deliberately outside the production image context.
COPY backend/app ./backend/app

EXPOSE 7860

# Liveness must not depend on signing readiness or research artifacts. The
# compatibility health route is intentionally a process probe; /api/ready is
# the public v2 readiness contract.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:7860/api/health', timeout=8).status == 200 else 1)"

ENV ALTERSCORE_ENV=production
ENV ALTERSCORE_API_VERSION=0.2.0
ENV ALTERSCORE_CORS_ORIGINS=https://alterscore.vercel.app
ENV ALTERSCORE_CORS_ORIGIN_REGEX=https://alterscore-[a-z0-9-]+\.vercel\.app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
