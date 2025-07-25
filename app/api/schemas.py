from enum import Enum
from pydantic import BaseModel
from typing import List

class OrderType(str, Enum):
    loading = "loading"
    unloading = "unloading"
    place_changing = "place_changing"

class BucketReference(BaseModel):
    bucket_id: int

class OrderCreate(BaseModel):
    priority: int
    order_type: OrderType  # ✅ Add this
    buckets: List[BucketReference]
