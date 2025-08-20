FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .

FROM base AS prod
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS dev
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]