FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

WORKDIR /code

# Install only the public v2 serving runtime.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Whitelist the serving application. Research source, training scripts, and
# model artifacts are deliberately outside the production image context.
COPY backend/app ./backend/app

EXPOSE 7860

ARG ALTERSCORE_RELEASE_SHA=local
ENV ALTERSCORE_RELEASE_SHA=${ALTERSCORE_RELEASE_SHA}
ARG ALTERSCORE_SIGNING_KEY_VERSION=local
ENV ALTERSCORE_SIGNING_KEY_VERSION=${ALTERSCORE_SIGNING_KEY_VERSION}

# Container health follows the public readiness contract, so a missing
# signing configuration or serving-store failure cannot appear healthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import json, sys, urllib.request; payload=json.load(urllib.request.urlopen('http://localhost:7860/api/ready', timeout=8)); checks=payload.get('checks', []); expected=('instrument', 'scorer', 'signing', 'attempt_store', 'verification_store', 'rate_limits'); sys.exit(0 if payload.get('status') == 'ready' and tuple(check.get('name') for check in checks) == expected and all(check.get('status') == 'pass' for check in checks) else 1)"

ENV ALTERSCORE_ENV=production
ENV ALTERSCORE_API_VERSION=0.2.0
ENV ALTERSCORE_CORS_ORIGINS=https://alterscore.vercel.app
ENV ALTERSCORE_CORS_ORIGIN_REGEX=https://alterscore-[a-z0-9-]+\.vercel\.app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
