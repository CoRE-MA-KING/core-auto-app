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
    """ロボットの状態ID"""

    UNKNOWN = 0
    INITIALIZING = 1
    NORMAL = 2
    DEFEATED = 3
    EMERGENCY = 4
    COMM_ERROR = 5


class RobotState(BaseModel):
    """マイコンと通信して取得したロボットの状態"""

    state_id: RobotStateId = RobotStateId.UNKNOWN
    ready_to_fire: bool = False
    pitch_deg: float = 0  # deg
    muzzle_velocity: float = 0  # mm/s
    record_video: bool = False
    reboot_pc: bool = False
