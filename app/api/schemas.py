from enum import Enum
from pydantic import BaseModel
from typing import List

class OrderType(str, Enum):
    LOADING = "loading"
    UNLOADING = "unloading"
    PLACE_CHANGING = "place_changing"

class BucketReference(BaseModel):
    bucket_id: int

class OrderCreate(BaseModel):
    priority: int
    order_type: OrderType
    buckets: List[BucketReference]
