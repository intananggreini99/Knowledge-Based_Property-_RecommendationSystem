FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies app/, scripts/, and the bundled data/ folder into the image so the
# service is fully self-contained on Railway (no volume mounts needed).
COPY . .

# Railway (and most PaaS) inject a $PORT the app must bind to. Default to 8000
# so local `docker run`/docker-compose keeps working unchanged.
ENV PORT=8000
EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
