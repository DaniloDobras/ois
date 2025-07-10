from kafka import KafkaProducer
import json
from .config import settings

_producer = None  # private module-level singleton


def get_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return _producer


def send_to_kafka(data: dict):
    producer = get_producer()
    future = producer.send(settings.KAFKA_TOPIC, value=data)
    result = future.get(timeout=10)  # will raise exception if send fails
    print(f"Sent to Kafka: {result}")
    producer.flush()

