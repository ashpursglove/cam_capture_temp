import sys
import cv2
import time
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QComboBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class WebcamApp(QWidget):
    def __init__(self):
        super().__init__()

        self.cap = None
        self.init_camera()

        self.label = QLabel(self)
        self.label.setFixedSize(480, 360)  # Smaller display preview
        self.mode_selector = QComboBox(self)
        self.mode_selector.addItems(["Image", "Video"])
        self.capture_button = QPushButton("Capture", self)
        self.capture_button.clicked.connect(self.handle_capture)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.mode_selector)
        layout.addWidget(self.capture_button)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.recording = False
        self.ffmpeg_process = None

        self.output_folder = os.path.join(os.getcwd(), "recordings")
        os.makedirs(self.output_folder, exist_ok=True)

        self.setWindowTitle("Webcam Capture")
        self.setGeometry(100, 100, 500, 460)  # Smaller window


    def init_camera(self):
        self.cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            sys.exit()
        self.set_max_resolution()

    def release_camera(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def set_max_resolution(self):
        resolutions = [(1920, 1080), (1280, 720), (640, 480)]
        for w, h in resolutions:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if (actual_w, actual_h) == (w, h):
                print(f"Using resolution: {w}x{h}")
                break
                
                
                
                
                
                
                
                
    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert and resize for preview only
                preview = cv2.resize(frame, (480, 360), interpolation=cv2.INTER_AREA)
                preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                h, w, ch = preview.shape
                q_img = QImage(preview.data, w, h, ch * w, QImage.Format_RGB888)
                self.label.setPixmap(QPixmap.fromImage(q_img))



    def handle_capture(self):
        mode = self.mode_selector.currentText()
        if mode == "Image":
            self.capture_image()
        elif mode == "Video":
            if not self.recording:
                self.start_video_recording()
            else:
                self.stop_video_recording()

    def capture_image(self):
        ret, frame = self.cap.read()
        if ret:
            filename = os.path.join(self.output_folder, f"image_{int(time.time())}.png")
            cv2.imwrite(filename, frame)
            print(f"Image saved to {filename}")

    def start_video_recording(self):
        self.timer.stop()
        self.release_camera()

        filename = os.path.join(self.output_folder, f"video_{int(time.time())}.mp4")
        command = [
            'ffmpeg',
            '-y',
            '-f', 'v4l2',
            '-framerate', '30',
            '-input_format', 'mjpeg',
            '-video_size', '1920x1080',
            '-i', '/dev/video0',
            '-f', 'alsa',
            '-i', 'hw:2,0',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-vcodec', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '18',
            '-acodec', 'aac',
            '-pix_fmt', 'yuv420p',
            filename
        ]

        try:
            print(f"Recording to: {filename}")
            self.ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)
            self.recording = True
            self.capture_button.setText("Stop Recording")
        except Exception as e:
            print(f"Error starting video recording: {e}")

    def stop_video_recording(self):
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.write(b'q\n')
                self.ffmpeg_process.stdin.flush()
                self.ffmpeg_process.wait()
                print("Recording stopped and finalized.")
            except Exception as e:
                print(f"Error stopping FFmpeg: {e}")
            finally:
                self.ffmpeg_process = None

        self.recording = False
        self.capture_button.setText("Capture")
        self.init_camera()
        self.timer.start(30)

    def closeEvent(self, event):
        self.timer.stop()
        self.release_camera()
        if self.recording:
            self.stop_video_recording()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebcamApp()
    window.show()
    sys.exit(app.exec_())
    
    
    
    

