from core_auto_app.domain.object_detector import ObjectDetector
import numpy as np


def test_detect():
    detector = ObjectDetector()

    image = np.zeros((3, 480, 640), dtype=np.uint8)
    result = detector.detect(image)
