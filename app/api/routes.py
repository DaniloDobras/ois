from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api.schemas import OrderCreate
from app.db.database import SessionLocal
from app.db.models import Order, Bucket, Position, BucketAction
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
        order_type=order.order_type,
    )

    db.add(new_order)
    db.flush()

    kafka_payload = {
        "order_id": new_order.id,
        "priority": new_order.priority,
        "order_type": new_order.order_type,
        "actions": []
    }

    for action in order.actions:
        bucket = db.query(Bucket).filter(Bucket.id == action.bucket_id).first()
        if not bucket:
            raise HTTPException(status_code=404, detail=f"Bucket {action.bucket_id} not found")

        source_pos = None
        if order.order_type in {"loading", "place_changing"}:
            if not action.source_position_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"Missing source_position_id for bucket {action.bucket_id}")
            source_pos = db.query(Position).filter(
                Position.id == action.source_position_id).first()
            if not source_pos:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source position {action.source_position_id} not found")

        target_pos = None
        if order.order_type in {"unloading", "place_changing"}:
            if not action.target_position_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"Missing target_position_id for bucket {action.bucket_id}")
            target_pos = (db.query(Position).
                          filter(
                Position.id == action.target_position_id).first()
                          )
            if not target_pos:
                raise HTTPException(
                    status_code=404,
                    detail=f"Target position {action.target_position_id} not found")

        bucket_action = BucketAction(
            order_id=new_order.id,
            bucket_id=action.bucket_id,
            source_position_id=action.source_position_id,
            target_position_id=action.target_position_id
        )
        db.add(bucket_action)

        kafka_payload["actions"].append({
            "bucket_id": bucket.id,
            "source_position": {
                "id": source_pos.id,
                "x": source_pos.position_x,
                "y": source_pos.position_y,
                "z": source_pos.position_z,
            } if source_pos else None,
            "target_position": {
                "id": target_pos.id,
                "x": target_pos.position_x,
                "y": target_pos.position_y,
                "z": target_pos.position_z,
            } if target_pos else None
        })

    db.commit()
    send_to_kafka(kafka_payload)
    return {"status": "order received", "order_id": new_order.id}


