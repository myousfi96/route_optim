"""
schemas.py

We keep time_window_start, time_window_end, quantity
"""

from pydantic import BaseModel, Field, validator

class OptimizeRequest(BaseModel):
    latitude: float
    longitude: float
    time_window_start: float = Field(..., ge=0)
    time_window_end: float   = Field(..., ge=0)
    quantity: float          = Field(..., ge=1)

    @validator("time_window_end")
    def ensure_tw_end_gt_start(cls, v, values):
        tw_start = values.get("time_window_start")
        if v <= tw_start:
            raise ValueError("time_window_end must be greater than time_window_start")
        return v
