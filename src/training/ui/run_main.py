import os

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QThread, QTimer, pyqtSignal

import multiprocessing
from multiprocessing import Queue

from training.module import training_main
from .video_window import Video_Form

from training.stylesheet.stylesheet_run_main import stylesheet
from constants.constants import MESSAGE_BOX_WARNING, MESSAGE_BOX_CONFIRMATION
from utils.custom_ui import messageBox

class ProgressBar(QtWidgets.QProgressBar):
    def text(self):
        if self.value() == 0:
            return "Process Ready"
        elif self.value() == 100:
            return "Process Finished"
        return f"{self.value()}%"

class OutputText(QtWidgets.QTextEdit):
    def mousePressEvent(self, event):
        self.setDisabled(True)
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setEnabled(True)
        return super().mouseReleaseEvent(event)

class Training_Thread(QThread):
    run_signal = pyqtSignal(dict)
    def __init__(self, is_train, dataset_shared_dict, hyperparameter_shared_dict, result_signal):
        super().__init__()        
        self.shared_data = Queue()
        self.training_process = multiprocessing.get_context("spawn").Process(name="Training Process", target=training_main.start, args=(
            is_train, dataset_shared_dict, hyperparameter_shared_dict, self.shared_data
        ))
        self._stop = False
        self.dataset_shared_dict = dataset_shared_dict
        self.hyperparameter_shared_dict = hyperparameter_shared_dict
        self.result_signal = result_signal
    
    def emit_result_signal(self, shared_data:dict) -> None:
        list_result_signal = ["train_loss", "val_loss", "test_loss", "abnormal_avg_f1score", "origin_images", "pred_images", "label_images", "abnormal_scores", "abnormal_scores_without_ignored", "labels", "labels_without_ignored", "bestThreshold", "position_indices", "position_indices_without_ignored", "trainFeatureDistHist", "testFeatureDistHist","save_path", "results", "cm", "is_classification", "is_anomaly_detection"]
        for data in list_result_signal:
            if data in shared_data:
                self.result_signal.emit({data: shared_data[data]})
                break
        
    def run(self):
        self.training_process.start()
        while self.training_process.is_alive():
            # get shared data
            try:
                shared_data = self.shared_data.get_nowait()
            except:
                shared_data = {}
            # data process (pooling)
            # run signal
            if "status_text" in shared_data:
                self.run_signal.emit({"status_text": shared_data["status_text"], "overwrite_current_line": shared_data["overwrite_current_line"]})
            elif "status_progress" in shared_data:
                self.run_signal.emit({"status_progress": shared_data["status_progress"]})
            elif "status_time" in shared_data:
                self.run_signal.emit({"status_time": shared_data["status_time"]})
            
            # result signal
            self.emit_result_signal(shared_data)

            # terminate
            if "runtime_error" in shared_data:
                self.run_signal.emit({"runtime_error": None}); break

            if self._stop:
                self.run_signal.emit({"stop": None}); break

        self.training_process.terminate()
        self.training_process.join()

        if not self._stop and not "runtime_error" in shared_data:
            self.run_signal.emit({"end": None})

    def stop(self):
        self._stop = True

class Run_Form(QtWidgets.QWidget):
    def __init__(self, Sync, lang):
        super().__init__()
        self.lang = lang
        self.init(Sync=Sync)
        self.init_ui(self)
        self.setup_ui()
        self.init_function()

        self.lang.set("training", "run_main", "update_run_text", self.update_run_text)

    def init(self, Sync=None):
        self.status = 0 # 0: init, 1: running, 2: end, 3: stopping, 4: error
        self.is_train = True
        self.auto_scroll = True

        # Sync
        self.Sync = Sync
        self.dataset_signal = Sync.dataset_signal
        self.hyperparameter_signal = Sync.hyperparameter_signal
        self.result_signal = Sync.result_signal

        self.dataset_shared_dict = Sync.dataset_shared_dict
        self.hyperparameter_shared_dict = Sync.hyperparameter_shared_dict

        # init thread
        self.training_thread = Training_Thread(self.is_train, self.dataset_shared_dict, self.hyperparameter_shared_dict, self.result_signal)

        # Timer for Remain Time text Animation
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_remain_time)
        self.remain_time_waiting_text_list = ["", ".", "..", "..."]
        self.waiting_counter = 0
        self.remain_time = -1

    def init_ui(self, Form):
        Form.setObjectName("Run_Form")
        Form.setWindowTitle("Run_Form")
        Form.setStyleSheet(stylesheet)
        self.FormLayout = QtWidgets.QVBoxLayout(Form)
        self.FormLayout.setObjectName("FormLayout")

        # =============== Icon Area ===============
        # TODO

        # =============== Output Form Area ===============
        # self.OutputWidget = QtWidgets.QPlainTextEdit(Form)
        self.OutputWidget = QtWidgets.QTextEdit(Form)
        # self.OutputWidget = OutputText(Form)
        self.OutputWidget.setObjectName("OutputWidget")

        # =============== Progress Form Area ===============
        self.ProgressLayout = QtWidgets.QHBoxLayout()
        self.ProgressLayout.setObjectName("ProgressLayout")

        self.RemainTimeLabel = QtWidgets.QLabel()
        self.RemainTimeLabel.setObjectName("RemainTimeLabel")

        # self.ProgressBar = QtWidgets.QProgressBar(Form)
        self.ProgressBar = ProgressBar(Form)
        self.ProgressBar.setObjectName("ProgressBar")

        self.RunTypeComboBox = QtWidgets.QComboBox()
        self.RunTypeComboBox.setObjectName("RunTypeComboBox")

        self.StartButton = QtWidgets.QPushButton()
        self.StartButton.setObjectName("StartButton")

        self.StopButton = QtWidgets.QPushButton()
        self.StopButton.setObjectName("StopButton")

        self.VideoForm = Video_Form()

        QtCore.QMetaObject.connectSlotsByName(Form)


    def setup_ui(self):
        # =============== Output Settings ===============
        self.OutputWidget.setUndoRedoEnabled(False)
        # self.OutputWidget.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.OutputWidget.setReadOnly(True)
        # self.OutputWidget.setDisabled(True)
        # self.OutputWidget.setOverwriteMode(False)

        # =============== Progress Settings ===============
        self.RemainTimeLabel.setFixedWidth(200)
        self.RunTypeComboBox.addItems(["", ""])
        self.lang.set("training", "run_main", "RunTypeComboBox", self.RunTypeComboBox) # change the separated combobox parsing type to one list (Hyeok Yoon 2025.10.31)
        self.ProgressBar.setProperty("value", 0)

        # =============== Add Widgets or Layout ===============
        self.ProgressLayout.addWidget(self.RunTypeComboBox)
        self.ProgressLayout.addWidget(self.StartButton)
        self.ProgressLayout.addWidget(self.StopButton)
        self.ProgressLayout.addWidget(self.ProgressBar)
        self.ProgressLayout.addWidget(self.RemainTimeLabel)

        self.FormLayout.addWidget(self.OutputWidget)
        self.FormLayout.addLayout(self.ProgressLayout)

        self.lang.set("training", "run_main", "StartButton", self.StartButton)
        self.lang.set("training", "run_main", "StopButton", self.StopButton)

    def init_function(self):
        self.StartButton.clicked.connect(lambda: self.start())
        self.StopButton.clicked.connect(lambda: self.stop())
        self.RunTypeComboBox.currentIndexChanged.connect(lambda: self.set_is_train(self.RunTypeComboBox.currentIndex()))
        # self.OutputWidget.verticalScrollBar().sliderPressed.connect(lambda: self.scrollable(True))
        # self.OutputWidget.verticalScrollBar().sliderReleased.connect(lambda: self.scrollable(False))

    def update_run_text(self):
        """
        Convert remaining time from mm:ss to hh:mm:ss format.

        Args:
            seconds (int): The remaining time in seconds.

        Returns:
            str: Formatted time string in hh:mm:ss format.

        Description:
            Previously, the time format was limited to mm:ss, which lacked clarity for long durations. 
            This function converts the remaining time from seconds into hh:mm:ss format, improving readability 
            for extended processes such as model training.

        modified by Chansik KIM 2024.12.17
        """
        if self.status == 0:
            self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_hour')} 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_minute')} 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_second')}")
        elif self.status == 1:
            if self.remain_time == -1:
                self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: {self.lang.get('training', 'run_main', 'RemainTimeLabel_calculating')}" + self.remain_time_waiting_text_list[self.waiting_counter % 4])
            else:
                self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: {self.remain_time // 3600}{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_hour')}{(self.remain_time // 60)%60}{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_minute')}{self.remain_time % 60}{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_second')}")
        elif self.status == 2:
            self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_hour')}0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_minute')}  0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_second')}")
        elif self.status == 3:
            self.RemainTimeLabel.setText(self.lang.get("training", "run_main", "RemainTimeLabel_stop"))
        elif self.status == 4:
            self.RemainTimeLabel.setText(self.lang.get("training", "run_main", "RemainTimeLabel_runtime_error"))

    def enable_ui(self):
        self.dataset_signal.emit({"disabled": False}) # enable dataset tab
        self.hyperparameter_signal.emit({"disabled": False}) # enable hyperparameter tab

        self.StartButton.setDisabled(False)
        self.StartButton.setStyleSheet("""
            QPushButton{
                background-color: rgb(83, 83, 83);
            }
            QPushButton:hover{
                background-color: rgb(16, 97, 150);
            }
            QPushButton:pressed{
                background-color: rgb(16, 97, 150);
            }
        """)
        self.RunTypeComboBox.setDisabled(False)
        self.RunTypeComboBox.setStyleSheet("background-color: rgb(83, 83, 83)")

    def disable_ui(self):
        self.dataset_signal.emit({"disabled": True}) # disable dataset tab
        self.hyperparameter_signal.emit({"disabled": True}) # disable hyperparameter tab

        self.StartButton.setDisabled(True)
        self.StartButton.setStyleSheet("background-color: grey")
        self.RunTypeComboBox.setDisabled(True)
        self.RunTypeComboBox.setStyleSheet("background-color: grey")

    def start(self):
        if self.path_validator():
            self.status = 1
            self.disable_ui()
            self.Sync.core_obj_dict["status_training_status"].setText("Initializing")

            # ============== init part ==============
            self.OutputWidget.clear() # Clear StatusText
            self.ProgressBar.setValue(0) # Clear ProgressBar
            self.result_signal.emit({"init": None}) # Results

            # send current model type
            self.result_signal.emit({"current_model_type": self.hyperparameter_shared_dict["current_model_type"]})

            # init timer
            self.remain_time = -1
            # ============== init part ==============

            # new thread
            self.training_thread = Training_Thread(self.is_train, self.dataset_shared_dict, self.hyperparameter_shared_dict, self.result_signal)
            self.training_thread.run_signal.connect(self.run_signal_receiver)

            # start timer
            self.timer.start()

            # start new thread
            self.training_thread.start()

            # play video
            if self.hyperparameter_shared_dict["show_video"]:
                self.VideoForm.show()
                self.VideoForm.play(self.is_train)

    def stop(self):
        response = messageBox(mode=MESSAGE_BOX_CONFIRMATION, 
                             title=self.lang.get("training", "run_main", "Stop_info_title"),
                             text=self.lang.get("training", "run_main", "Stop_info_msg"),
                             buttons={self.lang.get("main", "messageBox", "msgYes"): "accept", self.lang.get("main", "messageBox", "msgNo"): "reject"})
        if self.training_thread.isRunning() and response == "accept":
            self.status = 3
            # stop timer
            self.timer.stop()

            # stop thread
            self.training_thread.stop()
            self.training_thread.wait()

            # close video
            self.VideoForm.close()

            self.enable_ui()
            self.RemainTimeLabel.setText(self.lang.get("training", "run_main", "RemainTimeLabel_stop"))
            return True
        return False
    
    def scrollable(self, enabled):
        # if enabled:
        #     self.OutputWidget.setDisabled(False)
        # else:
        #     self.OutputWidget.setDisabled(True)
        self.auto_scroll = not enabled
    
    def runtime_error(self, msg="Runtime Error Occurred"):
        self.status = 4
        # stop timer
        self.timer.stop()

        # wait to stop
        self.training_thread.wait()
        
        # close video
        self.VideoForm.close()
        
        self.enable_ui()
        self.RemainTimeLabel.setText(self.lang.get("training", "run_main", "RemainTimeLabel_runtime_error"))
        self.Sync.core_obj_dict["status_training_status"].setText(self.lang.get("training", "run_main", "RemainTimeLabel_runtime_error"))

        messageBox(mode=MESSAGE_BOX_WARNING,
                   title=self.lang.get("training", "run_main", "RemainTimeLabel_runtime_error"),
                   text=self.lang.get("training", "run_main", "RuntimeErrorMsg"),
                   buttons={self.lang.get("main", "messageBox", "msgOk"):"accept"})
    def end(self):
        self.status = 2
        # stop timer
        self.remain_time = 0

        # wait to stop
        self.training_thread.wait()
        
        # close video
        self.VideoForm.close()
        self.enable_ui()
        self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: 0{self.lang.get('training','run_main', 'RemainTimeLabel_time_hour')} 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_minute')} 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_second')}")
        self.Sync.core_obj_dict["status_training_status"].setText("")

    def set_is_train(self, current_index):
        if current_index == 0:
            self.is_train = True
        else:
            self.is_train = False
    
    def path_validator(self):
        message_list = []

        train_dict = self.dataset_shared_dict["train"]
        if self.is_train and sum([train_dict[data_path][0] for data_path in train_dict.keys()]) == 0:
            message_list.append("There is no useable training datas")
        
        val_dict = self.dataset_shared_dict["val"]
        if self.is_train and sum([val_dict[data_path][0] for data_path in val_dict.keys()]) == 0:
            if self.hyperparameter_shared_dict["current_model_type"] != "PD":
                message_list.append("There is no useable validation datas")

        test_dict = self.dataset_shared_dict["test"]
        if not self.is_train and sum([test_dict[data_path][0] for data_path in test_dict.keys()]) == 0:
            message_list.append("There is no useable test datas")

        save_path = self.hyperparameter_shared_dict[self.hyperparameter_shared_dict["current_model_type"]]["save_path"]
        if not os.path.exists(save_path):
            message_list.append("Save path is invalid")
        
        load_path = self.hyperparameter_shared_dict[self.hyperparameter_shared_dict["current_model_type"]]["load_path"]
        if not self.is_train and not os.path.exists(load_path):
            message_list.append("Load path is invalid")

        if message_list != []:
            messageBox(mode=MESSAGE_BOX_WARNING,
                       title= self.lang.get("main", "run_main", "PathInvalidErrorMsg"),
                       text="\n".join(message_list),
                       buttons={self.lang.get("main", "messageBox", "msgOk"):"accept"})
            return False
        return True

    def run_signal_receiver(self, _dict):
        if "status_text" in _dict:
            textcursor = self.OutputWidget.textCursor()
            if _dict["overwrite_current_line"]:
                textcursor.select(QtGui.QTextCursor.LineUnderCursor)
                textcursor.removeSelectedText()
                self.OutputWidget.insertHtml(_dict["status_text"])

            else:
                self.OutputWidget.append(_dict["status_text"])

            # if self.auto_scroll:
            #     self.OutputWidget.moveCursor(QtGui.QTextCursor.End)
        elif "status_time" in _dict:
            self.remain_time = _dict["status_time"]
            if not self.timer.isActive():
                self.timer.start()
        elif "runtime_error" in _dict:
            self.runtime_error()
        elif "end" in _dict:
            self.end()
        elif "status_progress" in _dict:
            self.Sync.core_obj_dict['status_training_status'].setText(f"{_dict['status_progress']}%")
            self.ProgressBar.setValue(_dict["status_progress"])

    def update_remain_time(self):
        # waiting info display
        if self.remain_time == -1:
            self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: {self.lang.get('training', 'run_main', 'RemainTimeLabel_calculating')}" + self.remain_time_waiting_text_list[self.waiting_counter % 4])
            self.waiting_counter += 1            
        # end
        elif self.remain_time == 0:
            self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_hour')} 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_minute')} 0{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_second')}")
            self.ProgressBar.setValue(100)
            self.remain_time = -1
            self.timer.stop()
        # during training
        else:
            self.RemainTimeLabel.setText(f"{self.lang.get('training', 'run_main', 'RemainTimeLabel')}: {self.remain_time // 3600}{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_hour')} {(self.remain_time // 60)%60}{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_minute')} {self.remain_time % 60}{self.lang.get('training', 'run_main', 'RemainTimeLabel_time_second')}")
            self.remain_time -= 1
            if self.remain_time <= 0:
                self.remain_time = 0

    def close(self):
        if self.training_thread.isRunning():
            if self.stop():
                return True
            else:
                return False
        else:
            return True