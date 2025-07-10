from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Order
from app.core.kafka_producer import send_to_kafka

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/order")
def create_order(order: dict, db: Session = Depends(get_db)):
    new_order = Order(
        bucket_id=order["bucketId"],
        material_id=order["materialId"],
        qty=order["qty"]
    )
    db.add(new_order)
    db.commit()
    send_to_kafka(order)
    return {"status": "order received"}
