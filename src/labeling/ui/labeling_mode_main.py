import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSlot
from utils.custom_ui import ReDockOnCloseDockWidget, customTabBar

from constants.constants import QT_MAX_SIZE
if __name__ == "__main__" :
    from pen_main import Pen_Form
    from label_main import Labellist_Form
    from graph_main import Graph_Form
    from display_main import Display_Form
    from image_main import Image_Form
else:
    from .pen_main import Pen_Form
    from .label_main import Labellist_Form
    from .graph_main import Graph_Form
    from .graph_group_main import graphGroupForm
    from .display_main import Display_Form
    from .image_main import Image_Form


class Label_Main(QtWidgets.QMainWindow):
    """라벨링 모드 상위 메인 클래스이다. 라벨링을 위한 이미지, 라벨, 디스플레이, 펜, 그래프 UI들이 하위 클래스에서 선언된다.
    """
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.init(Sync=Sync, lang=lang)
        self.init_Ui_label_main(self)
        self.setup_Ui_label_main(self)
        
        if __name__ == "__main__" :
            self.show()

    def init(self, Sync, lang):
        """초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.core_to_labeling_mode_main_signal = self.Sync.core_to_labeling_mode_main_signal
        self.core_to_labeling_mode_main_signal.connect(self.recv_from_core)


    def init_Ui_label_main(self, MainWindow):
        """라벨링 모드 UI 생성을 위한 초기 선언문이다.
                Parameters
                1.   MainWindow(object): PyQt widget object

                @history: 
                    1. Add function to clear LDA Graph modified by GaEun Hwang
                    2. Imporve graph view using DockWidget modified by GaEun Hwang(2026.03.09)

        """
        MainWindow.setObjectName("Label_MainWindow")
        MainWindow.setWindowTitle("Label Main Window")
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.grid_main_window = QtWidgets.QGridLayout(self.centralwidget)
        self.grid_main_window.setObjectName("grid_main_window")
        
        self.grid_sub_window = QtWidgets.QGridLayout()
        self.grid_sub_window.setObjectName("grid_sub_window")
        
        self.image_scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.image_scrollArea.setObjectName("image_scrollArea")
        self.image_scrollArea.setWidgetResizable(True)
        
        self.image_scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff )
        

        self.grid_right_window_widget = QtWidgets.QWidget()
        self.grid_right_window_widget.setObjectName("grid_right_window_widget")

        self.grid_right_window = QtWidgets.QGridLayout(self.grid_right_window_widget)
        self.grid_right_window.setObjectName("grid_right_window")
                
        self.Label_widget = Labellist_Form(Sync=self.Sync, lang=self.lang)
        self.Label_widget.setObjectName("Label_widget")

        self.graphGroupWidget = graphGroupForm(Sync=self.Sync, lang=self.lang)
        self.graphGroupWidget.setObjectName("graphGroupWidget")

        self.Image_widget = Image_Form(Sync=self.Sync, lang=self.lang)
        self.Image_widget.setObjectName("Image_widget")

        self.pen_widget = Pen_Form(Sync=self.Sync, lang=self.lang)
        self.pen_widget.setObjectName("pen_widget")
        
        self.imagelabel_tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.imagelabel_tab_widget.setObjectName("imagelabel_tab_widget")
        self.imagelabel_tab_widget.addTab(self.Label_widget, "")
        self.imagelabel_tab_widget.addTab(self.graphGroupWidget, "")
        self.imagelabel_tab_widget.addTab(self.Image_widget, "")
        self.imagelabel_tab_widget.setCurrentIndex(2)
        self.lang.set("labeling", "labeling_mode_main", "imagelabel_tab_label", self.imagelabel_tab_widget)
        self.lang.set("labeling", "labeling_mode_main", "imagelabel_tab_graph", self.imagelabel_tab_widget)
        self.lang.set("labeling", "labeling_mode_main", "imagelabel_tab_image", self.imagelabel_tab_widget)
        
        self.Graph_widget = Graph_Form(Sync=self.Sync, lang=self.lang)
        self.Graph_widget.setObjectName("Graph_widget")
        self.clear_graph_list = self.Graph_widget.clear_graph_list
        # Add function to clear LDA Graph for global initialization
        self.clearLDAGraph = self.Graph_widget.clearLDAGraph
        self.update_graph_preview = self.Graph_widget.update_graph_preview


        self.function_list = []
        self.function_list.append(self.clear_graph_list)
        self.function_list.append(self.clearLDAGraph)
        self.function_list.append(self.update_graph_preview)
        
        self.Graph_tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        # apply customTabBar for graph tab widget to implement detachable tab
        self.graphTabBar = customTabBar(self.Graph_tab_widget)
        self.Graph_tab_widget.setTabBar(self.graphTabBar)
        self.Graph_tab_widget.setObjectName("Graph_tab_widget")
        self.graphTabBar.setObjectName("graphTabBar")
        self.Graph_tab_widget.addTab(self.Graph_widget, "")
        self.lang.set("labeling", "labeling_mode_main", "Graph_tab_widget", self.Graph_tab_widget)
        self.Graph_tab_widget.setCurrentIndex(0)

        self.graphDockingWindow = QtWidgets.QMainWindow()
        self.graphDockingWindow.setObjectName("graphDockingWindow")
        self.graphDock = ReDockOnCloseDockWidget(self.lang.get("labeling", "labeling_mode_main", "graphTitle"), self.graphDockingWindow, hideTitleBarWhenDocked=True, hideTitleBarWhenFloating=False)
        self.lang.set("labeling", "labeling_mode_main", "graphTitle", self.graphDock)
        self.graphDockingWindow.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.graphDock)
        self.graphDock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.graphDockingWindow.setDockOptions(QtWidgets.QMainWindow.DockOption.AnimatedDocks)
        self.graphDock.setWidget(self.Graph_tab_widget)

        # Connect signals from customTabBar to functions for floating and moving the graph dock
        self.graphTabBar.requestDetachSignal.connect(self.floatGraphDock)
        self.graphTabBar.moveSignal.connect(self.moveFloatingGraphDock)

        self.scrollAreaWidgetContents = Display_Form(Sync=self.Sync, function_list=self.function_list, lang=self.lang)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.image_tabwidget_horizon = QHBoxLayout()
        self.image_tabwidget_horizon.setObjectName("horizon")

        self.tab_widget_vertical = QVBoxLayout()
        self.tab_widget_vertical.setObjectName("tab_widget_vertical")

        self.hsplitter = QSplitter(QtCore.Qt.Horizontal)
        self.hsplitter.setObjectName("hsplitter")

        self.vsplitter = QSplitter(QtCore.Qt.Vertical)
        self.vsplitter.setObjectName("vsplitter")
        self.vsplitter.splitterMoved.connect(self.setDockingArea)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.pen_widget.setEnabled(False)
        self.Graph_widget.setEnabled(False)
        # self.Graph_widget.graph_plot_widget.setBackground(QtGui.QColor(0, 0, 0))
        self.imagelabel_tab_widget.setTabEnabled(0, False)
        self.imagelabel_tab_widget.setTabEnabled(1, False)
        self.imagelabel_tab_widget.setTabEnabled(2, True)


    def setup_Ui_label_main(self, MainWindow):
        """
            초기화된 ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
                Parameters
                1.   MainWindow(object): PyQt widget object
                @history:
                    1. remove graph tab widget minimum size through dragging becomes stable even when the mainwindow is small modified by GaEun Hwang(2026.03.18)
                       if graph tab widget's minimum size is bigger than docking area size, docking is not stable when dragging the graph tab widget
        """
        # MainWindow.resize(1085, 705)
        MainWindow.setCentralWidget(self.centralwidget)

        self.grid_main_window.addLayout(self.grid_sub_window, 0, 0, 1, 1)
        
        self.hsplitter.addWidget(self.image_scrollArea)
        self.hsplitter.addWidget(self.grid_right_window_widget)

        self.hsplitter.setStretchFactor(0,3)
        # self.hsplitter.setStretchFactor(1,1)
        self.hsplitter.setSizes([int(self.hsplitter.size().width() * 0.9), 
                        int(self.hsplitter.size().width() * 0.1)])

        self.image_tabwidget_horizon.addWidget(self.hsplitter)

        self.vsplitter.addWidget(self.imagelabel_tab_widget)
        self.vsplitter.addWidget(self.graphDockingWindow)
        self.tab_widget_vertical.addWidget(self.vsplitter)

        self.grid_sub_window.addWidget(self.pen_widget, 0, 0, 1, 1)
        self.grid_sub_window.addLayout(self.image_tabwidget_horizon, 0, 1, 1, 1)
        self.grid_right_window.addLayout(self.tab_widget_vertical, 0, 0, 1, 1)

        self.grid_main_window.setContentsMargins(0, 6, 0, 6)
        self.grid_right_window.setContentsMargins(0, 0, 0, 0)
        self.grid_sub_window.setContentsMargins(0, 0, 0, 0)
        self.tab_widget_vertical.setContentsMargins(0,0,0,0)
        self.image_tabwidget_horizon.setContentsMargins(0,0,0,0)
        self.pen_widget.setContentsMargins(0,0,0,0)


        self.pen_widget.setMinimumSize(QtCore.QSize(45, 0))
        self.pen_widget.setMaximumSize(QtCore.QSize(45, QT_MAX_SIZE))
        
        self.Graph_tab_widget.setMaximumSize(QtCore.QSize(QT_MAX_SIZE, QT_MAX_SIZE))
        
        self.imagelabel_tab_widget.setMinimumSize(QtCore.QSize(350, 300))
        self.imagelabel_tab_widget.setMaximumSize(QtCore.QSize(QT_MAX_SIZE, QT_MAX_SIZE))

        self.image_scrollArea.resize(int(MainWindow.width()*0.9), int(MainWindow.height()*0.9))   
        
        self.image_scrollArea.setWidget(self.scrollAreaWidgetContents)

    def floatGraphDock(self, globalPos, startPos):
        """
            @description: float graphDock when received requestDetachSignal from graphTabBar
            @author: GaEun Hwang(2026.03.09)
        """
        if not self.graphDock.isFloating():
            # hide dockwidget before floating to prevent it showing another place temporarily
            self.graphDock.hide()
            self.graphDock.setFloating(True)
            self.moveFloatingGraphDock(globalPos, startPos)

        self.graphDock.show()
        self.graphDock.raise_() 

    def moveFloatingGraphDock(self, globalPos, startPos):
        """
            @description: move floating graphDock when received move signal from graphTabBar
            @author: GaEun Hwang(2026.03.09)
        """
        # calculate the position to move the floating dock to the cursor position
        movedPos = self.graphDock.pos() + (globalPos - self.graphTabBar.mapToGlobal(startPos))
        self.graphDock.move(movedPos)

    def setDockingArea(self):
        """
            @description: set docking area of graphDock according to the height of docking area when splitter is moved
            @author: GaEun Hwang(2026.03.24)
        """
        dockingWidgetIndex = self.vsplitter.indexOf(self.graphDockingWindow)
        vsplitterHeight = self.vsplitter.widget(dockingWidgetIndex).height()
        
        if vsplitterHeight <= self.graphDock.minimumSizeHint().height():
            self.graphDock.setAllowedAreas(Qt.DockWidgetArea.NoDockWidgetArea)
        else:
            self.graphDock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

    @pyqtSlot(dict)
    def recv_from_core(self, output):
        # print("test : recv labeling mode main from display")
        # print(output)
        in_from = output['from']
        if in_from == "display":
            mode = output['mode']
            if mode == 0:
                self.pen_widget.setEnabled(False)
                self.Graph_widget.setEnabled(False)
                # self.Graph_widget.graph_plot_widget.setBackground(QtGui.QColor(0, 0, 0))
                self.imagelabel_tab_widget.setTabEnabled(0, False)
                self.imagelabel_tab_widget.setTabEnabled(1, False)
                self.imagelabel_tab_widget.setTabEnabled(2, False)
            elif mode == 1:
                type_detail = output['type_detail']
                if type_detail == 0:
                    self.pen_widget.setEnabled(True)
                    self.Graph_widget.setEnabled(True)
                    self.Graph_widget.graph_plot_widget.setBackground(QtGui.QColor(83, 83, 83))
                    self.imagelabel_tab_widget.setTabEnabled(0, True)
                    self.imagelabel_tab_widget.setTabEnabled(1, True)
                elif type_detail == 1:
                    self.pen_widget.setEnabled(True)
                    self.imagelabel_tab_widget.setTabEnabled(0, True)
                    self.imagelabel_tab_widget.setTabEnabled(1, True)

        elif in_from == "image":
            mode = output['mode']
            if mode == 0:
                self.pen_widget.setEnabled(False)
                self.Graph_widget.setEnabled(False)
                # self.Graph_widget.graph_plot_widget.setBackground(QtGui.QColor(0, 0, 0))
                self.imagelabel_tab_widget.setTabEnabled(0, False)
                self.imagelabel_tab_widget.setTabEnabled(1, False)

            elif mode == 1:
                type_detail = output['type_detail']
                if type_detail == 0:
                    self.pen_widget.setEnabled(True)
                    self.Graph_widget.setEnabled(True)
                    self.Graph_widget.graph_plot_widget.setBackground(QtGui.QColor(83, 83, 83))
                    self.imagelabel_tab_widget.setTabEnabled(0, True)
                    self.imagelabel_tab_widget.setTabEnabled(1, True)

                elif type_detail == 1:
                    self.pen_widget.setEnabled(True)
                    self.imagelabel_tab_widget.setTabEnabled(0, True)
                    self.imagelabel_tab_widget.setTabEnabled(1, True)

        elif in_from == "image_sub":
            mode = output['mode']
            if mode == 0:# hsi update
                self.Graph_widget.setEnabled(True)
                self.Graph_widget.graph_plot_widget.setBackground(QtGui.QColor(83, 83, 83))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Label_Main()
    # ui.init_Ui_main(MainWindow)
    # MainWindow.show()
    sys.exit(app.exec_())
