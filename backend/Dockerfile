FROM python:3.11-slim

# System dependencies
# libpq-dev + gcc = PostgreSQL + compiled packages
# tesseract-ocr + language packs = OCR for Phase 2
# ffmpeg = required by Whisper for audio processing
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    tesseract-ocr \
    tesseract-ocr-ben \
    tesseract-ocr-hin \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip + install setuptools first
# This fixes the pkg_resources error you hit locally
RUN pip install --upgrade pip setuptools wheel

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]