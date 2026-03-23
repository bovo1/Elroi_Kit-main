""" Ensure all tabs have equal spacing and consistent padding for uniform appearance"""
stylesheet = """
QWidget#scrollAreaWidgetContents{
    background-color: rgb(65, 65, 65);
    border: 0px;
}
QDockWidget{
    background-color: rgb(39, 38, 39);
}

QMessageBox{
    background-color: rgb(83, 83, 83);
}
QLabel{
    font: 15px;
    color : white;
}
QPushButton{
    background-color: transparent;
    font: 15px;
    color : white;
}

QPushButton:hover {
    background-color: rgb(16, 97, 150);
}

QPushButton:pressed {
    background-color: rgb(16, 97, 150);
}

QHeaderView{
    font: 14px;
}

QTabBar{
    font: 15px;
    color : white;
}

QTabWidget>QWidget, QTabWidget::pane, QWidget#Label_widget, Widget#Image_widget, QWidget::pane, QListWidget{
    background-color: rgb(83, 83, 83);
}

QTabBar::tab{
	padding : 5px;
    padding-left: 10px;
	padding-right:10px;
    min-width: 60px;
    max-width: 100px;
    margin-right: 5px;
}


QTabBar::tab::selected{
    background-color: rgb(83, 83, 83);
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab::!selected {
    background-color: rgb(66, 66, 66);
}
QTabBar::tab::disabled{
    background-color: rgb(66, 66, 66);
}


/* splitter */
QSplitter::handle {
    background-color: rgb(39, 38, 39);
    padding : 2px;
}

QSplitter::handle:horizontal {
    image: url(ico/labeling/splitter/splitter_bar_horizontal_white.png);
    width: 10px;
}

QSplitter::handle:vertical {
    image: url(ico/labeling/splitter/splitter_bar_vertical_white.png);
    height: 10px;
}

QSplitter::handle:horizontal:hover, QSplitter::handle:horizontal:pressed {
    image: url(ico/labeling/splitter/splitter_bar_horizontal_yellow.png);
}

QSplitter::handle:vertical:hover, QSplitter::handle:vertical:pressed {
    image: url(ico/labeling/splitter/splitter_bar_vertical_yellow.png);
}
"""