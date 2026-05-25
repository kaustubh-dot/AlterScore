FROM python:3.12-slim

# Install system compilation packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the complete codebase (including model artifacts)
COPY . .

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Establish production environment parameters
ENV ALTERSCORE_ENV=production
ENV ALTERSCORE_API_VERSION=0.2.0
ENV ALTERSCORE_REPO_ROOT=.
ENV ALTERSCORE_MODEL_MANIFEST=models/registry/production_manifest.json
ENV ALTERSCORE_REQUEST_LOG_PATH=/tmp/requests.jsonl
ENV ALTERSCORE_LOG_LEVEL=INFO
ENV ALTERSCORE_CORS_ORIGINS=*

# Launch ASGI server on required HF Space port
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
