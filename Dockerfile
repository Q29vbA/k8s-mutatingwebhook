FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 5000

# certs placed in path by secret injection
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--ssl-keyfile", "/certs/tls.key", "--ssl-certfile", "/certs/tls.crt"]
