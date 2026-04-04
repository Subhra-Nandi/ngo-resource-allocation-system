FROM python:3.11-slim

# Install system deps needed by Tesseract OCR (Phase 2) and psycopg2
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ben \
    tesseract-ocr-hin \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (Docker layer caching — only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway sets $PORT dynamically)
EXPOSE 8000

# Start command — Railway overrides this with the railway.toml startCommand
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]