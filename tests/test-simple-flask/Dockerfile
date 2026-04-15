FROM python:3.9-slim
RUN pip install flask
WORKDIR /app
COPY app.py index.html /app/
CMD ["python", "app.py"]
