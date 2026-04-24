FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ../backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright for scraping workers
RUN playwright install chromium --with-deps

# The /app volume is mounted from ./backend at runtime
