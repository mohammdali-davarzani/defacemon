# Defacemon: production image with Python + Chromium for headless discovery
FROM python:3.12-slim-bookworm

# Chromium and minimal deps for headless Chrome (no X11)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY defacemon/ ./defacemon/
COPY defacemon.py .

# Production: headless Chrome, bind all interfaces
ENV DEFACEMON_HEADLESS=1
ENV PYTHONUNBUFFERED=1

# Control port 9191, metrics 9192; baseline data via volume
EXPOSE 9191 9192

# Run server; use 0.0.0.0 so CLI can connect from host/other containers
CMD ["python", "defacemon.py", "serve", \
     "--control-host", "0.0.0.0", \
     "--control-port", "9191", \
     "--metrics-host", "0.0.0.0", \
     "--metrics-port", "9192", \
     "--baseline-dir", "/data"]
