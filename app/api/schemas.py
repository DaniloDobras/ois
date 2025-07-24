from pydantic import BaseModel
from typing import List

class PositionCreate(BaseModel):
    position_x: int
    position_y: int
    position_z: int

class BucketCreate(BaseModel):
    material_type: str
    material_qty: int
    position: PositionCreate

class OrderCreate(BaseModel):
    priority: int
    buckets: List[BucketCreate]
