import os
import copy
import shutil
import pyqtgraph
import numpy as np

import pickle

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer#, pyqtSlot
from qtwidgets import AnimatedToggle
from sklearn.metrics import precision_score, recall_score, f1_score
from constants.constants import MESSAGE_BOX_INFORMATION
from utils.custom_ui import messageBox
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# import matplotlib.pyplot as plt

# from functools import partial

from pyqtgraph import ImageView, exporters, GraphicsLayoutWidget#, PlotDataItem, ImageItem, HistogramLUTItem, ColorMap

from PIL import Image
from fpdf import FPDF, HTMLMixin

from datetime import datetime
from training.stylesheet.stylesheet_result_main import stylesheet

from sklearn.metrics import confusion_matrix

from utils.viewer import Display_viewer
from utils.tools import HSI

class PyFPDF(FPDF, HTMLMixin):
    pass

class Result_Form(QtWidgets.QWidget):
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.lang = lang
        self.init(Sync=Sync)
        self.init_ui(self)
        self.setup_ui()
        self.init_params()
        self.init_function()

        self.plot_updator = QTimer()
        self.plot_updator.setInterval(1000)
        self.plot_updator.timeout.connect(self.update_plot)

        self.is_anomaly_detection = False

    def init(self, Sync=None):
        # Sync
        self.dataset_shared_dict = Sync.dataset_shared_dict
        self.hyperparameter_shared_dict = Sync.hyperparameter_shared_dict
        Sync.result_signal.connect(self.result_signal_receiver)
    
    def init_params(self):
        # reset control ui
        self.is_anomaly_detection = False
        self.change_control_ui(self.is_anomaly_detection)

        self.train_loss = []
        self.val_loss = []
        self.abnormal_avg_f1score = []
        self.image_names = []
        self.origin_images = []
        self.current_pred_image = None
        self.pred_images = []
        self.pred_thresholds = 0.0
        self.label_images = []
        self.abnormal_scores = None
        self.labels = None
        self.best_threshold = 0.0
        self.current_threshold = None
        self.position_indices = None
        self.save_path = None
        # self.cm = None
        
        self.prev_train_loss_length = 0
        self.prev_val_loss_length = 0
        self.prev_abnormal_avg_f1score_length = 0

        self.TrainLossPlot.clear()
        self.ValLossPlot.clear()
        self.ValAvgF1Plot.clear()
        # self.OutputImageWidget.clear()
        self.OutputImageWidget.initPhoto(QtGui.QPixmap("./ico/labeling/logo/background.jpg"), init=True, dragmode=1)
        self.OutputImageWidget.updateDrag(mode=1)
        self.ThresholdLineEdit.setText("")
        self.ThresholdScoreLabel.setText("")
        self.init_combobox()


    def init_ui(self, Form):
        Form.setObjectName("Result_Form")
        Form.setWindowTitle("Result_Form")
        Form.setStyleSheet(stylesheet)
                
        self.FormLayout = QtWidgets.QVBoxLayout(Form)
        self.FormLayout.setObjectName("FormLayout")

        self.OutputMain = QtWidgets.QSplitter(Form)
        self.OutputMain.setObjectName("OutputMain")

        self.OutputMainLayout = QtWidgets.QHBoxLayout(self.OutputMain)
        self.OutputMainLayout.setObjectName("OutputMainLayout")
        
        self.OutputPlotMainWidget = QtWidgets.QWidget()
        self.OutputPlotMainWidget.setObjectName("OutputPlotMainWidget")

        self.OutputPlotMainWidgetLayout = QtWidgets.QVBoxLayout(self.OutputPlotMainWidget)
        self.OutputPlotMainWidgetLayout.setObjectName("OutputPlotMainWidgetLayout")

        self.OutputImageMainWidget = QtWidgets.QWidget()
        self.OutputImageMainWidget.setObjectName("OutputImageMainWidget")

        self.OutputImageMainWidgetLayout = QtWidgets.QVBoxLayout(self.OutputImageMainWidget)
        self.OutputImageMainWidgetLayout.setObjectName("OutputImageMainWidgetLayout")

        self.OutputPlotGroupBox = QtWidgets.QGroupBox(self.OutputPlotMainWidget)
        self.OutputPlotGroupBox.setObjectName("OutputPlotGroupBox")

        self.OutputPlotGroupBoxLayout = QtWidgets.QVBoxLayout(self.OutputPlotGroupBox)
        self.OutputPlotGroupBoxLayout.setObjectName("OutputPlotGroupBoxLayout")

        self.OutputImageGroupBox = QtWidgets.QGroupBox(self.OutputImageMainWidget)
        self.OutputImageGroupBox.setObjectName("OutputImageGroupBox")

        self.OutputImageGroupBoxLayout = QtWidgets.QVBoxLayout(self.OutputImageGroupBox)
        self.OutputImageGroupBoxLayout.setObjectName("OutputImageGroupBoxLayout")

        # Result controller - [Image selection controller, Threshold controller]
        self.ResultControlWidget = QtWidgets.QWidget()
        self.ResultControlWidget.setObjectName("ResultControlWidget")

        self.ResultControlLayout = QtWidgets.QHBoxLayout(self.ResultControlWidget)
        self.ResultControlLayout.setObjectName("ResultControlLayout")

        # Image selection controller
        self.ImageSelectorMainWidget = QtWidgets.QWidget()
        self.ImageSelectorMainWidget.setObjectName("ImageSelectorMainWidget")
        self.ResultControlLayout.addWidget(self.ImageSelectorMainWidget)

        self.ImageSelectorMainLayout = QtWidgets.QHBoxLayout(self.ImageSelectorMainWidget)
        self.ImageSelectorMainLayout.setObjectName("ImageSelectorMainLayout")

        self.ImageSelectorComboBox = QtWidgets.QComboBox()
        self.ImageSelectorComboBox.setObjectName("ImageSelectorComboBox")

        # Vertical line (Image selection controller <-> Pred map controller)
        self.ResultControlVerticalLine1 = QtWidgets.QFrame()
        self.ResultControlVerticalLine1.setObjectName("ResultControlVerticalLine1")
        self.ResultControlVerticalLine1.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLine1)

        # Pred map controller
        self.PredictionMapLabel = QtWidgets.QLabel()
        self.PredictionMapLabel.setObjectName("PredictionMapLabel")
        self.ResultControlLayout.addWidget(self.PredictionMapLabel)

        self.PredictionMapToggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.PredictionMapToggle.setObjectName("PredictionMapToggle")
        self.PredictionMapToggle.setChecked(True)
        self.ResultControlLayout.addWidget(self.PredictionMapToggle)

        # Vertical line (Pred map controller <-> Threshold controller)
        self.ResultControlVerticalLine2 = QtWidgets.QFrame()
        self.ResultControlVerticalLine2.setObjectName("ResultControlVerticalLine2")
        self.ResultControlVerticalLine2.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLine2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLine2)

        # Threshold controller
        self.ThresholdMainWidget = QtWidgets.QWidget()
        self.ThresholdMainWidget.setObjectName("ThresholdMainWidget")
        self.ResultControlLayout.addWidget(self.ThresholdMainWidget)

        self.ThresholdMainLayout = QtWidgets.QHBoxLayout(self.ThresholdMainWidget)
        self.ThresholdMainLayout.setObjectName("ThresholdMainLayout")
        
        self.ThresholdLabel = QtWidgets.QLabel()
        self.ThresholdLabel.setObjectName("ThresholdLabel")
        self.ThresholdMainLayout.addWidget(self.ThresholdLabel)
        
        self.ThresholdLineEdit = QtWidgets.QLineEdit()
        self.ThresholdLineEdit.setObjectName("ThresholdLineEdit")
        self.ThresholdMainLayout.addWidget(self.ThresholdLineEdit)

        self.ThresholdButton = QtWidgets.QPushButton()
        self.ThresholdButton.setObjectName("ThresholdButton")
        self.ThresholdMainLayout.addWidget(self.ThresholdButton)

        self.ThresholdScoreLabel = QtWidgets.QLabel()
        self.ThresholdScoreLabel.setObjectName("ThresholdScoreLabel")
        self.ThresholdMainLayout.addWidget(self.ThresholdScoreLabel)

        # Image View
        # self.OutputImageWidget = SelfImageView()
        self.OutputImageWidget = Display_viewer(usescrollbar=False)

        # Plot View
        self.OutputPlotWidget = GraphicsLayoutWidget()

        # Button Widgets
        self.GlobalButtonContainer = QtWidgets.QWidget()
        self.GlobalButtonContainer.setObjectName("GlobalButtonContainer")

        self.GlobalButtonContainerLayout = QtWidgets.QHBoxLayout(self.GlobalButtonContainer)
        self.GlobalButtonContainerLayout.setObjectName("GlobalButtonContainerLayout")

        self.LoadButton = QtWidgets.QPushButton()
        self.LoadButton.setObjectName("LoadButton")

        self.ReportButton = QtWidgets.QPushButton()
        self.ReportButton.setObjectName("ReportButton")

    def setup_ui(self):
        # Language Settings
        self.lang.set("training", "result_main", "OutputPlotGroupBox", self.OutputPlotGroupBox)
        self.lang.set("training", "result_main", "OutputImageGroupBox", self.OutputImageGroupBox)
        self.lang.set("training", "result_main", "update_result_text", self.update_result_text)
        self.lang.set("training", "result_main", "PredictionMapLabel", self.PredictionMapLabel)
        self.lang.set("training", "result_main", "ThresholdLabel", self.ThresholdLabel)
        self.lang.set("training", "result_main", "ThresholdButton", self.ThresholdButton)
        self.lang.set("training", "result_main", "ReportButton", self.ReportButton)
        self.lang.set("training", "result_main", "LoadButton", self.LoadButton)

        # ======================= Plot Area =======================
        # Plot View Settings
        style = {"color": "w", "font-size": "15px"}
        self.OutputPlotWidget.setBackground(pyqtgraph.mkColor(83, 83, 83))

        # Loss Plot
        self.LossPlot = self.OutputPlotWidget.addPlot(row=0, col=0)
        self.LossPlot.setLabel("left", "Loss", **style)
        self.LossPlot.getAxis("left").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.LossPlot.setLabel("bottom", "Epochs", **style)
        self.LossPlot.getAxis("bottom").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.LossPlot.showGrid(x=True, y=True)
        self.LossPlot.setMenuEnabled(False)
        self.LossPlot.setMouseEnabled(x=False, y=False)
        self.LossPlot.addLegend(labelTextColor=pyqtgraph.mkColor("w"))
        self.LossPlot.legend.setOffset(1)
        self.TrainLossPlot = self.LossPlot.plot(pen=pyqtgraph.mkPen(pyqtgraph.mkColor(255, 0, 0, 250), width=2), name="Train")
        self.ValLossPlot = self.LossPlot.plot(pen=pyqtgraph.mkPen(pyqtgraph.mkColor(0, 255, 0, 150), width=2), name="Val")

        # F1 Plot
        self.F1Plot = self.OutputPlotWidget.addPlot(row=1, col=0)
        self.F1Plot.setLabel("left", "F1-Score", **style)
        self.F1Plot.getAxis("left").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.F1Plot.setLabel("bottom", "Epochs", **style)
        self.F1Plot.getAxis("bottom").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.F1Plot.showGrid(x=True, y=True)
        self.F1Plot.setMenuEnabled(False)
        self.F1Plot.setMouseEnabled(x=False, y=False)
        self.ValAvgF1Plot = self.F1Plot.plot(pen=pyqtgraph.mkPen(pyqtgraph.mkColor(255, 255, 255, 255), width=2), name="F1-Score")

        self.OutputPlotGroupBoxLayout.addWidget(self.OutputPlotWidget)
        # ======================= Plot Area =======================
        # Image selector control settings
        self.ImageSelectorMainLayout.addWidget(self.ImageSelectorComboBox)

        # Threshold control settings
        self.ThresholdButton.setFixedWidth(70)
        self.ThresholdLineEdit.setFixedWidth(100)
        self.ThresholdLineEdit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("([0-9]*[.])?[0-9]+([eE][-+]?\d+)?")))
        self.ThresholdMainWidget.setVisible(False)
        self.ResultControlVerticalLine2.setVisible(False)
        
        # ==========================================
        # Add ResultControlWidget
        self.OutputImageGroupBoxLayout.addWidget(self.ResultControlWidget, 0, QtCore.Qt.AlignLeft)
        
        # Horizontal line (ResultControllerWidget <-> OutputImageWidget)
        self.OutputImageGroupBoxHorizontalLine1 = QtWidgets.QFrame()
        self.OutputImageGroupBoxHorizontalLine1.setObjectName("OutputImageGroupBoxHorizontalLine1")
        self.OutputImageGroupBoxHorizontalLine1.setFrameShape(QtWidgets.QFrame.HLine)
        self.OutputImageGroupBoxHorizontalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.OutputImageGroupBoxLayout.addWidget(self.OutputImageGroupBoxHorizontalLine1)
        
        # Add OutputImageWidget
        self.OutputImageGroupBoxLayout.addWidget(self.OutputImageWidget)
        # ==========================================

        self.OutputPlotMainWidgetLayout.addWidget(self.OutputPlotGroupBox)
        self.OutputPlotMainWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.OutputImageMainWidgetLayout.addWidget(self.OutputImageGroupBox)
        self.OutputImageMainWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.OutputMainLayout.addWidget(self.OutputPlotGroupBox)
        self.OutputMainLayout.addWidget(self.OutputImageGroupBox)

        self.OutputMain.setSizes([1, 2])

        self.GlobalButtonContainerLayout.addWidget(self.ReportButton, 0, QtCore.Qt.AlignRight)
        self.GlobalButtonContainerLayout.setContentsMargins(0, 0, 0, 0)
        
        self.FormLayout.addWidget(self.GlobalButtonContainer, 0, QtCore.Qt.AlignRight)
        self.FormLayout.addWidget(self.OutputMain)
    
    def init_function(self):
        self.ReportButton.clicked.connect(lambda: self.report_result())
        self.LoadButton.clicked.connect(lambda: self.load_result())
        self.PredictionMapToggle.clicked.connect(lambda: self.show_selected_image(self.ImageSelectorComboBox.currentIndex(), self.PredictionMapToggle.isChecked(), True))
        self.ThresholdButton.clicked.connect(lambda: self.show_updated_pred_image(self.ImageSelectorComboBox.currentIndex(), float(self.ThresholdLineEdit.text()), self.PredictionMapToggle.isChecked()))
        self.ThresholdLineEdit.editingFinished.connect(self.ThresholdButton.click)
        # Connect multiple callbacks to combobox index change:
        # 1. Update displayed image based on new selection
        # 2. Adjust combobox width to fit content
        self.ImageSelectorComboBox.currentIndexChanged.connect(lambda: (
            self.show_selected_image(self.ImageSelectorComboBox.currentIndex(), self.PredictionMapToggle.isChecked(), True), 
            self.adjust_combo_box_width()
        ))

    def update_result_text(self):
        style = {"color": "w", "font-size": "15px"}
        self.LossPlot.setTitle(self.lang.get("training", "result_main", "LossPlotTitle"), **style)
        self.F1Plot.setTitle(self.lang.get("training", "result_main", "F1PlotTitle"), **style)

    def update_plot(self):
        if self.train_loss != []:
            if len(self.train_loss) != self.prev_train_loss_length:
                self.prev_train_loss_length = len(self.train_loss)
                self.TrainLossPlot.setData(self.train_loss)
        if self.val_loss != []:
            if len(self.val_loss) != self.prev_val_loss_length:
                self.prev_val_loss_length = len(self.val_loss)
                self.ValLossPlot.setData(self.val_loss)
        if self.abnormal_avg_f1score != []:
            if len(self.abnormal_avg_f1score) != self.prev_abnormal_avg_f1score_length:
                self.prev_abnormal_avg_f1score_length = len(self.abnormal_avg_f1score)
                self.ValAvgF1Plot.setData(self.abnormal_avg_f1score)

    def init_combobox(self):
        self.ImageSelectorComboBox.clear()

    def init_combobox_item_list(self, is_load):
        if not is_load:
            for test_data_path in self.dataset_shared_dict["test"].keys():
                if self.dataset_shared_dict["test"][test_data_path][0] and self.dataset_shared_dict["test"][test_data_path][1] != 0:
                    self.image_names.append(test_data_path.split("\\")[-1] if os.name == "nt" else test_data_path.split("/")[-1])
            self.ImageSelectorComboBox.addItems(self.image_names)
            self.adjust_combo_box_width()

    def init_images_anomaly_detection(self, origin_images):
        for i in range(len(origin_images)):
            self.pred_images.append(self.get_pred_image(i, self.best_threshold))

    def adjust_combo_box_width(self):
        """
        description: Added dynamic width adjustment functionality to automatically resize ImageSelectorComboBox based on its content length
        modified by Chansik Kim 2024.12.16
        """
        font_metrics = self.ImageSelectorComboBox.fontMetrics()
        text_width = 100  # Default minimum width
        if self.ImageSelectorComboBox.count() > 0:
            text_width = max(font_metrics.horizontalAdvance(self.ImageSelectorComboBox.itemText(i)) 
                           for i in range(self.ImageSelectorComboBox.count()))
        
        # Add padding for dropdown arrow and margins
        self.ImageSelectorComboBox.setFixedWidth(text_width + 30)

    def change_control_ui(self, is_anomaly_detection:bool):
        if is_anomaly_detection:
            self.ThresholdMainWidget.setVisible(True)
            self.ResultControlVerticalLine2.setVisible(True)
            self.ThresholdLineEdit.setText(f"{self.pred_thresholds:.3f}")
        else:
            self.ThresholdMainWidget.setVisible(False)
            self.ResultControlVerticalLine2.setVisible(False)

    def show_selected_image(self, image_index:int, show_pred_map:bool, fitinview:bool):
        if image_index == -1: return
        image = None
        # Update inference image with new threshold only for anomaly detection task
        # Modified by Chansik Kim (2025.03.21)
        if self.is_anomaly_detection:
            threshold_txt = float(self.ThresholdLineEdit.text())
            threshold = threshold_txt if threshold_txt != 0.0 else self.best_threshold
            self.update_pred_image(image_index, threshold)
            self.ThresholdLineEdit.setText(f"{self.pred_thresholds:.3f}")

        if show_pred_map:
            if self.pred_images != []:
                image = self.pred_images[image_index]#.transpose(1, 0, 2)
        else:
            if self.origin_images != []:
                image = self.origin_images[image_index]#.transpose(1, 0, 2)
        
        if image is not None:
            self.OutputImageWidget.updatePhoto(QtGui.QPixmap(QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)), fitinview)

    def show_updated_pred_image(self, image_index:int, threshold:float, show_pred_map:bool):
        self.update_pred_image(image_index, threshold)
        self.show_selected_image(image_index, show_pred_map, True)

    def update_pred_image(self, image_index, threshold):
        self.pred_images[image_index] = self.get_pred_image(image_index, threshold)
        self.pred_thresholds = threshold

    def get_pred_image(self, image_index, threshold):
        """
        Description:
        Generate an image with abnormal regions highlighted in red.

        Args:
            image_index (int): Index of the target image.
            threshold (float): Threshold for detecting abnormal regions.

        Returns:
            np.ndarray: Original image with abnormal regions (scores >= threshold) highlighted in red ([255, 0, 0]).
        
        modified by Chansik Kim 2024.12.17
        """
        origin_image = np.copy(self.origin_images[image_index])
        w, h, _ = origin_image.shape
        indices = self.position_indices[:, 0]
        indices = np.where(np.array(indices) == image_index)
        abnormal_scores = self.abnormal_scores[indices]
        eval_mask = abnormal_scores >= threshold
        origin_image[eval_mask.reshape(w, h)] = [255, 0, 0]
        return origin_image

    def get_scores(self, preds, labels, eps=1e-9) -> str:
        preds = preds.reshape([-1])
        labels = labels.reshape([-1])
        unique_labels = np.unique(labels)

        cm = confusion_matrix(labels, preds, labels=unique_labels)
        recall = (np.diag(cm)/(np.sum(cm, axis=1)+eps))[-1]
        precision = (np.diag(cm)/(np.sum(cm, axis=0)+eps))[-1]
        F1score = (2.0*np.diag(cm)/(np.sum(cm, axis=0)+np.sum(cm, axis=1)+eps))[-1]
        
        return f"Prec: {precision:.3f}, Rec: {recall:.3f}, F1: {F1score:.3f}"

    def report_result(self):
        if (len(self.origin_images) != 0):
            # report resource directory
            temp_path = os.path.join(self.save_path, "temp")
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)
            
            # Plot Export
            plot_exporter = exporters.ImageExporter(self.OutputPlotWidget.scene())
            plot_exporter.export(os.path.join(temp_path, "OutputPlot.png"))

            pdf = PyFPDF()
            pdf.add_page()

            head = """
                <table border="0" align="center">
                        <thead>
                            <tr>
                                <th width="12%">Label</th><th width="12%">Num Data</th><th width="12%">Precision</th><th width="12%">Recall</th><th width="12%">F1-Score</th>
                            </tr>
                        </thead>
                    <tbody>
            """
            body = []
            tail = """
                    </tbody>
                </table>
            """

            for result in self.results[3:-3]:
                result = result.split()
                body.append(f"<tr align='center'><td>{result[0]}</td><td>{result[1]}</td><td>{result[2]}</td><td>{result[3]}</td><td>{result[4]}</td></tr>")
            results = head + "".join(body) + tail

            html1 = f"""
            <h1 align="center">Spectral AI Report</h1>
            <h1>{self.current_model_type}</h1>
            <h2>Date: {datetime.now().strftime('%Y/%m/%d %H:%M')}</h2>
            <h2>Score</h2>
            {results}
            <p>Abnormal OA: {self.results[-3].split()[-1]}</p>
            <br><p>Abnormal AA: {self.results[-2].split()[-1]}</p>
            <br><p>Abnormal Average F1-Score: {self.results[-1].split()[-1]}</p>
            <br>
            """
            
            pdf.write_html(html1)
            pdf.add_page()

            html3 = u"<h2>Visualization</h2>"
            
            # # Image Export
            for i in range(len(self.ImageSelectorComboBox)):
                if self.current_threshold != None:
                    Image.fromarray(self.get_pred_image(i, self.current_threshold)).save(f"{os.path.join(temp_path, 'pred_' + str({i}) + '.png')}")
                else:
                    Image.fromarray(self.pred_images[i]).save(f"{os.path.join(temp_path, 'pred_' + str({i}) + '.png')}")
                Image.fromarray(self.label_images[i]).save(f"{os.path.join(temp_path, 'label_' + str({i}) + '.png')}")
                html3 += f"""
                    <br><h3>                                           Label                                             Prediction</h3>
                    <img width="200" src="{os.path.join(temp_path, 'label_' + str({i}) + '.png')}"/>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                    <img width="200" src="{os.path.join(temp_path, 'pred_' + str({i}) + '.png')}"/>
                    <br><br><br><br><br><br><br><br><br><br><br><br>
                """
                if i % 2 == 0 and i != 0:
                    pdf.write_html(html3)
                    pdf.add_page()
                    html3 = u"<h2>Visualization</h2>"
            
            if len(self.ImageSelectorComboBox) % 3 != 0:
                pdf.write_html(html3)

            pdf.output(os.path.join(self.save_path, "report.pdf"), "F")

            shutil.rmtree(temp_path)
            message = f'{self.lang.get("training", "result_main", "ReportMessageBoxText")}{self.save_path}'
            print(message)
            messageBox(mode=MESSAGE_BOX_INFORMATION,
                       title=self.lang.get("training", "result_main", "ReportMessageBoxTitle"),
                       text=message,
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"}
                       )
        else:
            message = self.lang.get("training", "result_main", "ReportNoResultText")
            messageBox(mode=MESSAGE_BOX_INFORMATION,
                       title=self.lang.get("training", "result_main", "ReportMessageBoxTitle"),
                       text=message,
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"}
                       )

    def save_result(self, save_path):
        with open(os.path.join(save_path, "result.re"), "wb") as f:
            pickle.dump(
                {
                    "current_model_type": self.current_model_type,
                    "is_anomaly_detection": self.is_anomaly_detection,
                    "save_path": save_path,
                    "image_names": self.image_names,
                    "current_index": self.ImageSelectorComboBox.currentIndex(),
                    "position_indices": self.position_indices,
                    "abnormal_scores": self.abnormal_scores,
                    "labels": self.labels,
                    "best_threshold": self.best_threshold,
                    "origin_images": self.origin_images,
                    "pred_images": self.pred_images, # for classification
                    "pred_thresholds": self.pred_thresholds,
                    "label_images": self.label_images, # for report
                    "train_loss": self.train_loss,
                    "val_loss": self.val_loss,
                    "abnormal_avg_f1score": self.abnormal_avg_f1score,
                    "show_pred_map": self.PredictionMapToggle.isChecked(),
                    "results": self.results
                },
                file=f,
                protocol=pickle.HIGHEST_PROTOCOL
            )

    def load_result(self):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_dialog.setNameFilters(["re (*.re)"])
        if file_dialog.exec_():
            load_path = file_dialog.selectedFiles()[0]
            # PyQt file dialog return the posix path style
            if os.name == "nt":
                load_path = load_path.replace("/", "\\")

            with open(load_path, "rb") as f:
                loaded_results = pickle.load(f)

            self.init_combobox()

            if "current_model_type" in loaded_results:
                self.current_model_type = loaded_results["current_model_type"]

            if "is_anomaly_detection" in loaded_results:
                self.is_anomaly_detection = loaded_results["is_anomaly_detection"]

            if "save_path" in loaded_results:
                self.save_path = loaded_results["save_path"]
            if "train_loss" in loaded_results:
                self.train_loss = loaded_results["train_loss"]
                self.TrainLossPlot.setData(self.train_loss)
            if "val_loss" in loaded_results:
                self.val_loss = loaded_results["val_loss"]
                self.ValLossPlot.setData(self.val_loss)
            if "abnormal_avg_f1score" in loaded_results:
                self.abnormal_avg_f1score = loaded_results["abnormal_avg_f1score"]
                self.ValAvgF1Plot.setData(self.abnormal_avg_f1score)
            
            # for classification
            if "pred_images" in loaded_results:
                self.pred_images = loaded_results["pred_images"]
            if "label_images" in loaded_results:
                self.label_images = loaded_results["label_images"]
            
            # for anomaly detection
            if "origin_images" in loaded_results:
                self.origin_images = loaded_results["origin_images"]
            if "abnormal_scores" in loaded_results:
                self.abnormal_scores = loaded_results["abnormal_scores"]
            if "labels" in loaded_results:
                self.labels = loaded_results["labels"]
            if "pred_thresholds" in loaded_results:
                self.pred_thresholds = loaded_results["pred_thresholds"]
            if "position_indices" in loaded_results:
                self.position_indices = loaded_results["position_indices"]

            if "show_pred_map" in loaded_results:
                self.PredictionMapToggle.setChecked(loaded_results["show_pred_map"])
            
            image_index = 0
            if "current_index" in loaded_results:
                image_index = loaded_results["current_index"]
            
            if "image_names" in loaded_results:
                self.image_names = loaded_results["image_names"]


            if "results" in loaded_results:
                self.results = loaded_results["results"]
            
            self.change_control_ui(self.is_anomaly_detection) # set to specific type of task
            self.ImageSelectorComboBox.addItems(self.image_names)
            self.ImageSelectorComboBox.setCurrentIndex(image_index)
            self.ImageSelectorComboBox.setCurrentText(self.image_names[image_index])
            self.show_selected_image(image_index, loaded_results["show_pred_map"], True)
            self.init_combobox_item_list(True)
            self.adjust_combo_box_width()

    def result_signal_receiver(self, _dict):        
        if "current_model_type" in _dict:
            self.current_model_type = _dict["current_model_type"]
        # loss and f1 score
        if "train_loss" in _dict:
            self.train_loss.append(_dict["train_loss"])
        if "val_loss" in _dict:
            self.val_loss.append(_dict["val_loss"])
        if "abnormal_avg_f1score" in _dict:
            self.abnormal_avg_f1score.append(_dict["abnormal_avg_f1score"])
        if "train_loss" in _dict or "val_loss" in _dict or "abnormal_avg_f1score" in _dict:
            self.plot_updator.start() # plot update start
        # images, abnormal scores and labels
        if "origin_images" in _dict:
            self.origin_images = copy.deepcopy(_dict["origin_images"])
        if "pred_images" in _dict:
            self.pred_images = copy.deepcopy(_dict["pred_images"])
        if "label_images" in _dict:
            self.label_images = copy.deepcopy(_dict["label_images"])
        if "abnormal_scores" in _dict:
            self.abnormal_scores = copy.deepcopy(_dict["abnormal_scores"])
        if "labels" in _dict:
            self.labels = copy.deepcopy(_dict["labels"])
        if "best_threshold" in _dict:
            self.best_threshold = _dict["best_threshold"]
        if "position_indices" in _dict:
            self.position_indices = np.copy(_dict["position_indices"])
        if "save_path" in _dict:
            self.save_path = _dict["save_path"]
        if "results" in _dict:
            self.results = _dict["results"]
        if "init" in _dict:
            self.init_params()
        if "is_classification" in _dict:
            self.is_anomaly_detection = False
            self.change_control_ui(self.is_anomaly_detection) # set to specific type of task
            self.show_selected_image(0, self.PredictionMapToggle.isChecked(), True)
            self.init_combobox_item_list(False)
        if "is_anomaly_detection" in _dict:
            self.is_anomaly_detection = True
            self.change_control_ui(self.is_anomaly_detection) # set to specific type of task
            self.pred_thresholds = self.best_threshold
            self.init_images_anomaly_detection(self.origin_images)
            self.show_selected_image(0, self.PredictionMapToggle.isChecked(), True)
            self.init_combobox_item_list(False)
        if ("is_classification" in _dict or "is_anomaly_detection" in _dict) and self.plot_updator.isActive():
            self.plot_updator.stop()