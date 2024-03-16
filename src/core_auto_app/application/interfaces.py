from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

from core_auto_app.domain.messages import Command, RobotState


class ApplicationInterface(ABC):
    """Interface for the CoRE auto-pilot application."""

    @abstractmethod
    def spin(self) -> None:
        pass


class Camera(ABC):
    """Interface for RGB-D camera."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_images(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Get both color and depth images."""
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class ColorCamera(ABC):
    """Interface for color camera."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_image(self) -> Optional[np.ndarray]:
        """Get color image."""
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class CameraFactory(ABC):
    """Interface for camera factory."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def create(self, record: bool) -> Camera:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class Presenter(ABC):
    """Interface for displaying results."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def show(self, image: np.ndarray) -> None:
        pass

    @abstractmethod
    def get_ui_command(self) -> Command:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class RobotDriver(ABC):
    """Interface for communicating with robot"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def get_robot_state(self) -> RobotState:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
