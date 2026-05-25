FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

COPY . .

RUN mkdir -p /app/uploads /app/data/faiss_index

# Pre-compile PyTorch / sentence-transformers bytecode so first container
# start doesn't spend 3-5 minutes generating .pyc files
RUN python -c "import torch; import sentence_transformers; import faiss; print('Bytecode warmed')"

EXPOSE 8000

CMD sh -c "python seed.py; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"
