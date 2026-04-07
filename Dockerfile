FROM python:3.11-slim
WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["uvicorn", "edupulse.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
