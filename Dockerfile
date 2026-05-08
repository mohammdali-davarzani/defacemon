FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY defacemon/ ./defacemon/
COPY defacemon.py .

ENV PYTHONUNBUFFERED=1

EXPOSE 9191 9192

CMD ["python", "defacemon.py", "serve", \
     "--control-host", "0.0.0.0", \
     "--control-port", "9191", \
     "--metrics-host", "0.0.0.0", \
     "--metrics-port", "9192", \
     "--baseline-dir", "/data"]
