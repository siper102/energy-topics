FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENV PYTHONPATH=/app/src
ENV BENTOML_HOME=/app/ml_service/data/bentoml

# Use the entrypoint script to handle auto-training
ENTRYPOINT ["./entrypoint.sh"]
