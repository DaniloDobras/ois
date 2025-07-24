from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.api.schemas import OrderCreate
from app.db.database import SessionLocal
from app.db.models import Order, Position, Bucket
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
    new_order = Order(priority=order.priority)
    db.add(new_order)
    db.flush()  # So new_order.id is available

    for bucket_data in order.buckets:
        pos = Position(
            position_x=bucket_data.position.position_x,
            position_y=bucket_data.position.position_y,
            position_z=bucket_data.position.position_z
        )
        db.add(pos)
        db.flush()  # So pos.id is available

        bucket = Bucket(
            material_type=bucket_data.material_type,
            material_qty=bucket_data.material_qty,
            position_id=pos.id,
            order_id=new_order.id
        )
        db.add(bucket)

    db.commit()

    # Optionally send to Kafka
    send_to_kafka(order.dict())  # Or customize message if needed

    return {"status": "order received"}
