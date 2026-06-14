FROM python:3.12-slim

# Install system compilation packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Pre-fetch the sentence-transformer model into the image's local cache so the
# runtime (which loads with local_files_only=True) never attempts a network
# download during scoring. Keeps the real semantic embeddings in production
# instead of silently falling back to the deterministic hashed path.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the complete codebase (including model artifacts)
COPY . .

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Container healthcheck via the API's own health endpoint. Uses stdlib urllib so
# no extra packages (curl/wget) are needed in the slim image. Allows generous
# start-up time for model artifacts to load before the first probe counts.
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:7860/api/health', timeout=8).status == 200 else 1)"

# Establish production environment parameters
ENV ALTERSCORE_ENV=production
ENV ALTERSCORE_API_VERSION=0.2.0
ENV ALTERSCORE_REPO_ROOT=.
ENV ALTERSCORE_MODEL_MANIFEST=models/registry/production_manifest.json
# Request logs go to ephemeral /tmp (reset on container restart). Point this at
# a mounted volume (e.g. /data/requests.jsonl on HF Spaces persistent storage)
# if durable request logs are required.
ENV ALTERSCORE_REQUEST_LOG_PATH=/tmp/requests.jsonl
ENV ALTERSCORE_LOG_LEVEL=INFO
ENV ALTERSCORE_CORS_ORIGINS=https://alterscore.vercel.app
# Allow ephemeral Vercel preview deploys (per-branch/commit *.vercel.app hosts)
ENV ALTERSCORE_CORS_ORIGIN_REGEX=https://alterscore-[a-z0-9-]+\.vercel\.app

# Launch ASGI server on required HF Space port
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
