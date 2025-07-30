from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class OrderType(str, Enum):
    LOADING = "loading"
    UNLOADING = "unloading"
    PLACE_CHANGING = "place_changing"


class BucketActionCreate(BaseModel):
    bucket_id: int
    source_position_id: Optional[int] = None  # Required for loading or place_changing
    target_position_id: Optional[int] = None  # Required for unloading or place_changing


class OrderCreate(BaseModel):
    priority: int
    order_type: OrderType
    actions: List[BucketActionCreate]
