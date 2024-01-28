from typing import Optional

import numpy as np
import pyrealsense2 as rs

from core_auto_app.application.interfaces import Camera


class RealsenseCamera(Camera):
    def __init__(self, record_path: Optional[str] = None):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

        # Create an align object
        self.align = rs.align(align_to=rs.stream.color)

        # Save frames to a bag file if file path is specified
        if record_path:
            self.config.enable_record_to_file(record_path)

    def start(self):
        self.pipeline.start(self.config)

    def stop(self):
        self.pipeline.stop()

    def get_images(self):
        # Get new frames
        frames = self.pipeline.wait_for_frames()

        # Align the depth frame to color frame
        aligned_frames = self.align.process(frames)

        # Get aligned frames
        color_frame = aligned_frames.get_color_frame()
        aligned_depth_frame = aligned_frames.get_depth_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            return None, None

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        print(depth_image.shape)

        return color_image, depth_image

    def close(self):
        print("closing camera")
        if self.pipeline is not None:
            self.pipeline.stop()
