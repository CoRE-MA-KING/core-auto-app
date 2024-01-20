from enum import auto, Enum
from typing import Optional, Tuple
from pydantic import BaseModel


class Command(Enum):
    NONE = auto()
    QUIT = auto()


class Detection(BaseModel):
    xyxy: Tuple[float]
    score: float
    class_id: int


class TargetState(BaseModel):
    track_id: int
    detection: Detection
    position: Optional[Tuple[float]]
