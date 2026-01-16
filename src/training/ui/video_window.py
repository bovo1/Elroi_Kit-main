import cv2
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint, QTimer

from utils.shared import video_path

class Video_Form(QtWidgets.QMainWindow):
    def __init__(self, video_path=video_path, window_size=(854, 480), frame_rate=20, keep_ratio=False):
        super(Video_Form, self).__init__()
        self.video_path = video_path
        self.window_size = window_size
        self.frame_rate = frame_rate
        self.keep_ratio = keep_ratio

        # read video
        self.cap = cv2.VideoCapture(self.video_path)

        # main window
        self.resize(self.window_size[0], self.window_size[1])
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        
        # video widget
        self.videowidget = QtWidgets.QLabel(self)
        self.videowidget.setGeometry(0, 0, self.window_size[0], self.window_size[1])

        # text widget
        self.textwidget = QtWidgets.QLabel(self)
        self.textwidget.setGeometry(345, 420, 200, 50)
        self.textwidget.setStyleSheet("background-color: transparent;")
        self.textwidget.setStyleSheet("color: white; font-size: 30px;")

        # timer
        self.video_timer = QTimer()
        self.video_timer.setTimerType(Qt.PreciseTimer)
        self.video_timer.timeout.connect(self.update_frame)

        self.text_timer = QTimer()
        self.text_timer.timeout.connect(self.update_text)
        
        self.text_init()

    def play(self, is_train):
        # self.to_center()
        self.text_init()
        if is_train:
            self.vis_text_list = ["AI Training", "AI Training.", "AI Training..", "AI Training..."]
        else:
            self.vis_text_list = ["AI Testing", "AI Testing.", "AI Testing..", "AI Testing..."]
        self.video_timer.start(int(1000.0 / self.frame_rate))
        self.text_timer.start(800)
    
    def pause(self):
        pass

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret == True:
            if self.cap.get(1) > self.cap.get(7)-2:
                self.cap.set(1, 0)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            if self.keep_ratio:
                img = img.scaled(self.window_size[0], self.window_size[1], Qt.KeepAspectRatio)
            else:
                img = img.scaled(self.window_size[0], self.window_size[1])
            self.pix = QPixmap.fromImage(img)
            self.videowidget.setPixmap(self.pix)
    
    def update_text(self):
        self.text_timer_counter += 1
        self.textwidget.setText(self.vis_text_list[self.text_timer_counter % 4])
    
    def closeEvent(self, event):
        self.video_timer.stop()
        self.text_timer.stop()
        self.cap.set(1, 0)

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        offset = QPoint (event.globalPos() - self.old_pos)
        self.move(self.x() + offset.x(), self.y() + offset.y())
        self.old_pos = event.globalPos()
    
    def to_center(self):
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(QtWidgets.QDesktopWidget().availableGeometry().center())
        self.move(frame_geometry.topLeft())

    
    def text_init(self):
        self.text_timer_counter = 0
        self.vis_text_list = ["Preparing", "Preparing.", "Preparing..", "Preparing..."]

