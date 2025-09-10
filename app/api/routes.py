from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette import status

from app.api.schemas import OrderCreate, BucketActionOut, PositionCreate
from app.db.database import SessionLocal
from app.db.models import Order, Bucket, Position, BucketAction
from app.core.kafka_producer import send_to_kafka

import pandas as pd

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
        # loading
        if order.order_type == "loading":
            bucket = Bucket()
            db.add(bucket)
            db.flush()
        else:
            # unloading / place_changing
            if not action.bucket_id:
                raise HTTPException(
                    status_code=422,
                    detail="Missing bucket_id for non-loading order"
                )
            bucket = db.query(Bucket).filter(Bucket.id == action.bucket_id).first()
            if not bucket:
                raise HTTPException(
                    status_code=404,
                    detail=f"Bucket {action.bucket_id} not found"
                )

        source_pos = None
        if order.order_type in {"loading", "place_changing"}:
            if not action.source_position_id:
                raise HTTPException(
                    status_code=422,
                    detail="Missing source_position_id for action"
                )
            source_pos = db.query(Position).filter(Position.id == action.source_position_id).first()
            if not source_pos:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source position {action.source_position_id} not found"
                )

        target_pos = None
        if order.order_type in {"unloading", "place_changing"}:
            if not action.target_position_id:
                raise HTTPException(
                    status_code=422,
                    detail="Missing target_position_id for action"
                )
            target_pos = db.query(Position).filter(Position.id == action.target_position_id).first()
            if not target_pos:
                raise HTTPException(
                    status_code=404,
                    detail=f"Target position {action.target_position_id} not found"
                )

        bucket_action = BucketAction(
            order_id=new_order.id,
            bucket_id=bucket.id,
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


@router.get("/bucket-actions", response_model=List[BucketActionOut])
def get_all_bucket_actions(db: Session = Depends(get_db)):
    return db.query(BucketAction).all()


@router.post("/upload-positions")
async def upload_positions(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    filename = file.filename.lower()
    if not (
            filename.endswith(".csv")
            or filename.endswith(".xlsx")
            or filename.endswith(".xls")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only CSV or Excel files are supported"
        )

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)

        required_cols = {"position_x", "position_y", "position_z"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {missing}"
            )

        df = df.astype(object).where(pd.notnull(df), None)
        records = df.to_dict(orient="records")
        db.bulk_insert_mappings(Position, records)
        db.commit()
        db.execute(text(
            "SELECT setval('positions_id_seq', (SELECT MAX(id) FROM positions))"
        ))
        db.commit()

        return {"message": f"Inserted {len(records)} rows into database"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-position", response_model=dict)
def create_position(position: PositionCreate, db: Session = Depends(get_db)):
    try:
        new_position = Position(
            position_x=position.position_x,
            position_y=position.position_y,
            position_z=position.position_z
        )
        db.add(new_position)
        db.commit()
        db.refresh(new_position)

        return {
            "message": "Position inserted successfully",
            "id": new_position.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
