# OIS - Order Integration Service

A FastAPI-based microservice for handling order ingestion, persistence, and Kafka-based messaging for downstream processing in a warehouse/logistics system.

---

## 📁 Project Structure

```
ois/
├── alembic/               # Database migration management
│   └── versions/          # Alembic migration scripts
├── app/                   # Main application code
│   ├── api/               # FastAPI routes
│   │   └── routes.py      # HTTP endpoints (e.g., order submission)
│   ├── core/              # Core logic and configuration
│   │   ├── config.py      # Environment and settings
│   │   └── kafka_producer.py  # Kafka producer utility
│   └── db/                # Database access layer
│       ├── models.py      # SQLAlchemy models
│       └── database.py    # DB session management
└── main.py            # FastAPI app entry point
```

---

## Features

* ✅ Order ingestion via REST API
* ✅ Order persistence with SQLAlchemy
* ✅ Kafka message publishing
* ✅ Alembic database migrations
* ✅ Configurable via `.env`
* ✅ Dockerized for easy deployment

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/DaniloDobras/ois.git
cd ois
```

### 2. Configure environment variables

Copy the template and edit:

```bash
cp .env.template .env
```

Edit `.env` to provide:

* `DATABASE_URL`
* `KAFKA_BOOTSTRAP_SERVERS`
* `KAFKA_TOPIC`

---

## 🧪 Development: Using `uv` as Package Manager

For local development, you can use [uv](https://github.com/astral-sh/uv) for faster dependency management. This is optional, but recommended for speedier installs and modern Python workflows.

### 1. Install uv (one-time setup)

```bash
pipx install uv  # Recommended
# or
pip install uv
```

### 2. Install dependencies with uv

- For standard dependencies:
  ```bash
  uv pip install -r requirements.txt
  ```
- For development (with extra tools):
  ```bash
  uv pip install -r requirements-dev.txt
  ```

> **Note:** The Docker image and production use traditional `pip` and `requirements.txt` only. `uv` is for local/dev use.

---

## Run with Docker

```bash
docker-compose up --build
```

This will start the FastAPI app along with Kafka, PostgreSQL, etc., as defined in `docker-compose.yml`.

---

## Run Alembic Migrations

### Initialize the database:

```bash
docker exec -it ois-service alembic upgrade head
```

### Create a new migration:

```bash
docker exec -it ois-service alembic revision --autogenerate -m "table added"
```

---

## API Example

### POST `/orders`

Send an order to the service.

#### Request

```http
POST /orders
Content-Type: application/json

LOADING

{
  "priority": 1,
  "order_type": "loading",
  "actions": [
    {
      "source_position_id": 4
    }
  ]
}

UNLOADING

POST /orders
Content-Type: application/json

{
  "priority": 2,
  "order_type": "unloading",
  "actions": [
    {
      "bucket_id": 2,
      "target_position_id": 4
    },
    {
      "bucket_id": 3,
      "target_position_id": 3
    }
  ]
}

```

#### Response

```json
{
    "status": "order received",
    "order_id": 5
}
```

---

## Kafka Output

Once the order is processed, a Kafka message is published:

```json
{
  "order_id": 42,
  "priority": 1,
  "buckets": [
    {
      "bucket_id": 1001,
      "material_type": "Steel",
      "material_qty": 2,
      "position": {
        "position_x": 10,
        "position_y": 5,
        "position_z": 0
      }
    },
    {
      "bucket_id": 1002,
      "material_type": "Aluminum",
      "material_qty": 3,
      "position": {
        "position_x": 12,
        "position_y": 7,
        "position_z": 0
      }
    }
  ]
}
```

---

##  Technologies

* [FastAPI](https://fastapi.tiangolo.com/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Alembic](https://alembic.sqlalchemy.org/)
* [Kafka](https://kafka.apache.org/)
* [Docker](https://www.docker.com/)
* PostgreSQL

---

## Sample `.env`

```env
DATABASE_URL=postgresql://user:password@db:5432/ois
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=orders
```

---
