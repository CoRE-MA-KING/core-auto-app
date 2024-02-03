import sys
from typing import Optional

import numpy as np
from unittest.mock import MagicMock

# https://github.com/open-mmlab/mmengine/issues/1175#issuecomment-1571527356
sys.modules["torch.distributed"] = MagicMock()
from mmdet.apis import DetInferencer  # noqa: E402


class ObjectDetector:
    def __init__(self, weight_path: Optional[str] = None, device="cuda:0"):
        # Initialize the DetInferencer
        self.inferencer = DetInferencer(
            model="yolox_s_8x8_300e_coco", weights=weight_path, device=device
        )

    def infer(self, image: np.array):
        # Perform inference
        results = self.inferencer(image)

        print(results)

        return results
