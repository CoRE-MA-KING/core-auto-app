from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

from core_auto_app.domain.messages import Command


class ApplicationInterface(ABC):
    """Interface for the CoRE auto-pilot application."""

    @abstractmethod
    def spin(self) -> None:
        pass


class Camera(ABC):
    """Interface for camera."""

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
