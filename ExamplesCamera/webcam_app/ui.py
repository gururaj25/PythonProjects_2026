import tkinter as tk
from tkinter import messagebox  # Fix for Error 2
from PIL import Image, ImageTk
from camera import Camera
from sequence_validator import SequenceValidator
import cv2  # Fix for Error 1

class WebcamApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Initialize camera
        self.camera = Camera()

        # Initialize sequence validator
        self.validator = SequenceValidator()

        # Create a canvas to display the video feed
        self.canvas = tk.Canvas(window, width=self.camera.width, height=self.camera.height)
        self.canvas.pack()

        # Button to validate the sequence
        self.btn_validate = tk.Button(window, text="Validate Sequence", width=50, command=self.validate_sequence)
        self.btn_validate.pack(anchor=tk.CENTER, expand=True)

        # Start the video feed
        self.update()
        self.window.mainloop()

    def update(self):
        # Capture frame-by-frame
        frame = self.camera.capture_frame()

        if frame is not None:
            # Detect sequence
            self.validator.detect_sequence(frame)

            # Convert the frame to RGB and display it in the UI
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        # Repeat the update every 10 milliseconds
        self.window.after(10, self.update)

    def validate_sequence(self):
        # Validate the detected sequence
        if self.validator.validate():
            messagebox.showinfo("Success", "Successful validation!")  # Fix for Error 2
        else:
            messagebox.showerror("Error", "Validation failed. Incorrect sequence.")  # Fix for Error 2

    def __del__(self):
        # Release the camera when the app is closed
        self.camera.release()