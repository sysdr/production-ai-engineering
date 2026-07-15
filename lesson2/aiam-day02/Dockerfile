FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tools/ ./tools/
COPY tests/ ./tests/
COPY main.py app.py ./

ENV PYTHONUNBUFFERED=1
EXPOSE 8081

# Single worker so in-memory METRICS update live on the dashboard
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1"]
