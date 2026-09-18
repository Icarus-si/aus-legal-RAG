FROM python:3.11-slim

# Prevent Python from creating .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create a non-root user for the application
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Container-level health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
