import cv2

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def capture_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def release(self):
        if self.cap.isOpened():
            self.cap.release()