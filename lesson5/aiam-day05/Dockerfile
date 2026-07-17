FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY security/ ./security/
COPY tests/ ./tests/
COPY main.py app.py ./

ENV PYTHONUNBUFFERED=1
ENV HMAC_SECRET=day05-secret
EXPOSE 8084

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8084", "--workers", "1"]
