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

## Run with Docker

```bash
docker-compose up --build
```

This will start the FastAPI app along with Kafka, PostgreSQL, etc., as defined in `docker-compose.yml`.

---

## Run Alembic Migrations

### Initialize the database:

```bash
alembic upgrade head
```

### Create a new migration:

```bash
alembic revision --autogenerate -m "your message"
```

---

## API Example

### POST `/orders`

Send an order to the service.

#### Request

```http
POST /orders
Content-Type: application/json

{
  "bucketId": "B123",
  "materialId": "M456",
  "qty": 10
}
```

#### Response

```json
{
  "message": "Order received"
}
```

---

## Kafka Output

Once the order is processed, a Kafka message is published:

```json
{
  "bucketId": "B123",
  "materialId": "M456",
  "qty": 10,
  "timestamp": "2025-07-21T10:30:00Z",
  "status0": "accepted"
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
