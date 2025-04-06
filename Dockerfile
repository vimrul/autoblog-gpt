FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow, psycopg2, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app
ENV FLASK_RUN_PORT=8080
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]
