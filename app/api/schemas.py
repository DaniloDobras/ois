from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class OrderType(str, Enum):
    LOADING = "loading"
    UNLOADING = "unloading"
    PLACE_CHANGING = "place_changing"


class BucketActionCreate(BaseModel):
    bucket_id: Optional[int] = None
    source_position_id: Optional[int] = None
    target_position_id: Optional[int] = None


class OrderCreate(BaseModel):
    priority: int
    order_type: OrderType
    actions: List[BucketActionCreate]
