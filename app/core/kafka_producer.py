import json
from kafka import KafkaProducer
from app.core.config import settings
from app.core.kafka_topics import KafkaTopic
_producer = None

def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            acks="all",
            retries=8,
            linger_ms=20,
            compression_type="gzip",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer



def send_to_kafka(topic: KafkaTopic, data: dict):
    producer = get_producer()
    future = producer.send(topic=topic.value, value=data)
    result = future.get(timeout=10)
    print(f"Sent to Kafka: {result}")
    producer.flush()
