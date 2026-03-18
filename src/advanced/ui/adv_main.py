"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""
from PyQt5 import QtCore, QtWidgets
import sys

if __name__ == "__main__" :
    from adv_predictlabel_mode import advanced_predictlabel_Form
    from adv_SAL_mode import advanced_sal_Form
    from advanced.ui.adv_pixel_based_labeling_mode import advanced_pixel_based_labeling_Form
    from adv_label_correction_mode import advanced_label_correction_Form
    from adv_label_aggregation_mode import advanced_label_aggregation_Form
else:
    from .adv_predictlabel_mode import advanced_predictlabel_Form
    from .adv_SAL_mode import advanced_sal_Form
    from .adv_pixel_based_labeling_mode import advanced_pixel_based_labeling_Form
    from .adv_label_correction_mode import advanced_label_correction_Form
    from .adv_label_aggregation_mode import advanced_label_aggregation_Form

from advanced.stylesheet.stylesheet_adv_main import stylesheet


class Advanced_Main(QtWidgets.QWidget):
    """라벨링 모드 상위 메인 클래스이다. 라벨링을 위한 이미지, 라벨, 디스플레이, 펜, 그래프 UI들이 하위 클래스에서 선언된다.
    """
    def __init__(self, Sync=None, lang=None, ) -> None:
        super().__init__()
        self.init(Sync=Sync, lang=lang)
        self.init_Ui_Advanced_Main(self)
        self.setup_Ui_Advanced_Main(self)
        
        if __name__ == "__main__" :
            self.show()

    def init(self, Sync, lang):
        """
            @description : 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
            @author : MyoungHwan
            @parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.parent = None
        """
            description
            modified by MyoungHwan(20240603): 신기능관련 UI Form 추가
        """
        self.advanced_predictlabel_Form = advanced_predictlabel_Form(Sync=self.Sync, lang=self.lang)
        self.advanced_sal_Form = advanced_sal_Form(Sync=self.Sync, lang=self.lang)
        self.advanced_pixel_based_labeling_Form = advanced_pixel_based_labeling_Form(Sync=self.Sync, lang=self.lang)
        self.advanced_label_correction_Form = advanced_label_correction_Form(Sync=self.Sync, lang=self.lang)
        self.advanced_label_aggregation_Form = advanced_label_aggregation_Form(Sync=self.Sync, lang=self.lang)


    def init_Ui_Advanced_Main(self, MainWindow):
        """라벨링 모드 UI 생성을 위한 초기 선언문이다.
                Parameters
                1.   MainWindow(object): PyQt widget object
        """
        MainWindow.setObjectName("Advanced_MainWindow")
        MainWindow.setWindowTitle("Advanced Menu")
        MainWindow.resize(800,640)
        MainWindow.setMinimumWidth(800)
        MainWindow.setMinimumHeight(640)
        MainWindow.setStyleSheet(stylesheet)
        
        self.Advanced_main_vertical = QtWidgets.QVBoxLayout(MainWindow)
        self.Advanced_main_vertical.setObjectName("Advanced_main_vertical")

        self.Advanced_tab_widget = QtWidgets.QTabWidget()
        self.Advanced_tab_widget.setObjectName("Advanced_tab_widget")
        """
            description
            modified by MyoungHwan(20240603): 신기능관련 UI Form 추가
            modified by Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        self.Advanced_tab_widget.addTab(self.advanced_predictlabel_Form, "")
        self.Advanced_tab_widget.addTab(self.advanced_sal_Form, "")
        self.Advanced_tab_widget.addTab(self.advanced_pixel_based_labeling_Form, "")
        self.Advanced_tab_widget.addTab(self.advanced_label_correction_Form, "")
        self.Advanced_tab_widget.addTab(self.advanced_label_aggregation_Form, "")

        self.lang.set("advanced", "advanced_main", "advanced_predictlabel_Form", self.Advanced_tab_widget)
        self.lang.set("advanced", "advanced_main", "advanced_sal_Form", self.Advanced_tab_widget)
        self.lang.set("advanced", "advanced_main", "advanced_pixel_based_labeling_Form", self.Advanced_tab_widget)
        self.lang.set("advanced", "advanced_main", "advanced_label_correction_Form", self.Advanced_tab_widget)
        self.lang.set("advanced", "advanced_main", "advanced_label_aggregation_Form", self.Advanced_tab_widget)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setup_Ui_Advanced_Main(self, MainWindow):
        """초기화된 ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
                Parameters
                1.   MainWindow(object): PyQt widget object
        """
        self.Advanced_main_vertical.addWidget(self.Advanced_tab_widget)

    def closeEvent(self, e):
        if self.parent is not None:
            self.parent.setChecked(False)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Advanced_Main()
    # ui.init_Ui_main(MainWindow)
    # MainWindow.show()
    sys.exit(app.exec_())
