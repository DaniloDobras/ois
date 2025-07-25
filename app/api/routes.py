from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api.schemas import OrderCreate
from app.db.database import SessionLocal
from app.db.models import Order, Bucket, Position
from app.core.kafka_producer import send_to_kafka

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/order", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    new_order = Order(
        priority=order.priority,
        order_type=order.order_type
    )

    db.add(new_order)
    db.flush()  # So new_order.id is available

    for bucket_ref in order.buckets:
        bucket = db.query(Bucket).filter(
            Bucket.id == bucket_ref.bucket_id).first()
        if not bucket:
            raise HTTPException(status_code=404,
                                detail=f"Bucket {bucket_ref.bucket_id} not found")

        # Just update the order_id for the existing bucket
        bucket.order_id = new_order.id

    # Prepare enriched Kafka payload
    kafka_payload = {
        "order_id": new_order.id,
        "priority": new_order.priority,
        "buckets": []
    }

    for bucket_ref in order.buckets:
        bucket = db.query(Bucket).filter(
            Bucket.id == bucket_ref.bucket_id).first()
        if not bucket:
            raise HTTPException(status_code=404,
                                detail=f"Bucket {bucket_ref.bucket_id} not found")

        # Fetch related position
        position = db.query(Position).filter(
            Position.id == bucket.position_id).first()
        if not position:
            raise HTTPException(status_code=404,
                                detail=f"Position for bucket {bucket.id} not found")

        # Attach order to the existing bucket
        bucket.order_id = new_order.id

        # Add to Kafka payload
        kafka_payload["buckets"].append({
            "bucket_id": bucket.id,
            "material_type": bucket.material_type,
            "material_qty": bucket.material_qty,
            "position": {
                "position_x": position.position_x,
                "position_y": position.position_y,
                "position_z": position.position_z,
            }
        })

    db.commit()

    # Send enriched message
    send_to_kafka(kafka_payload)

    return {"status": "order received", "order_id": new_order.id}

