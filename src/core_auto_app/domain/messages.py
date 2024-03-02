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


class RobotStateId(Enum):
    """ロボットの状態ID

    Todo:
        状態を追加する
    """
    UNKNOWN = 0


class RobotState(BaseModel):
    """マイコンと通信して取得したロボットの状態"""
    state_id: RobotStateId = RobotStateId.UNKNOWN
    pitch_deg: float = 0.0
    muzzle_velocity: float = 0.0
