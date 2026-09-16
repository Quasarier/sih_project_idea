FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COASTAL_WATCH_ALLOWED_ORIGINS=http://localhost:4173,http://localhost:5173

WORKDIR /app

COPY ml/requirements.txt /app/ml/requirements.txt
RUN pip install --no-cache-dir -r /app/ml/requirements.txt

COPY backend /app/backend
COPY ml /app/ml
COPY data /app/data
COPY simulation /app/simulation

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8001/health', timeout=3)"

CMD ["python", "backend/api/server.py"]
