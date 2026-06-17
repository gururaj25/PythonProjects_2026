# sequence_validator.py
import cv2
import numpy as np

# Define the sequence of operations (e.g., colors to detect)
SEQUENCE = ["red", "green", "blue"]

class SequenceValidator:
    def __init__(self):
        self.detected_sequence = []

    def detect_sequence(self, frame):
        # Example: Detect colors in the frame
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define color ranges (example: red, green, blue)
        color_ranges = {
            "red": ([0, 100, 100], [10, 255, 255]),
            "green": ([35, 100, 100], [85, 255, 255]),
            "blue": ([100, 100, 100], [130, 255, 255]),
        }

        for color, (lower, upper) in color_ranges.items():
            # Create a mask for the color
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv_frame, lower, upper)

            # If the color is detected, add it to the sequence
            if np.any(mask):
                if color not in self.detected_sequence:
                    self.detected_sequence.append(color)

    def validate(self):
        # Check if the detected sequence matches the expected sequence
        return self.detected_sequence == SEQUENCE