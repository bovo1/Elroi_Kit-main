stylesheet = """
/* Widget */
QWidget{
	background-color: rgb(83, 83, 83);
	color: white;
	font: 15px;
}

QComboBox{
	width: 100px;
}

/* PushButton */
QPushButton{
	background-color: transparent;
}
QPushButton:hover{
	background-color: rgb(16, 97, 150);
}
QPushButton:pressed{
	background-color: rgb(16, 97, 150);
}

/* splitter */
QSplitter::handle {
    background-color: rgb(83, 83, 83);
    padding : 2px;
}

QSplitter::handle:horizontal {
    image: url(ico/splitter/splitter_bar_horizontal_white.png);
    width: 10px;
}

QSplitter::handle:vertical {
    image: url(ico/splitter/splitter_bar_vertical_white.png);
    height: 10px;
}

QSplitter::handle:horizontal:hover, QSplitter::handle:horizontal:pressed {
    image: url(ico/splitter/splitter_bar_horizontal_yellow.png);
}

QSplitter::handle:vertical:hover, QSplitter::handle:vertical:pressed {
    image: url(ico/splitter/splitter_bar_vertical_yellow.png);
}

#ReportButton{
    background-color: rgb(83, 83, 83);
}
#ReportButton:hover{
    background-color: rgb(16, 97, 150);
}
#ReportButton:pressed{
    background-color: rgb(16, 97, 150);
}

#LoadButton{
    background-color: rgb(83, 83, 83);
}
#LoadButton:hover{
    background-color: rgb(16, 97, 150);
}
#LoadButton:pressed{
    background-color: rgb(16, 97, 150);
}

#ThresholdButton{
    background-color: rgb(83, 83, 83);
}
#ThresholdButton:hover{
    background-color: rgb(16, 97, 150);
}
#ThresholdButton:pressed{
    background-color: rgb(16, 97, 150);
}
"""