FROM python:3.12-slim
WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["uvicorn", "edupulse.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "30", "--limit-concurrency", "10"]
