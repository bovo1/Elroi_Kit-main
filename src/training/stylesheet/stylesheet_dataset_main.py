stylesheet = """
QWidget{
	background-color: rgb(83, 83, 83);
	color: white;
	font: 15px;
}

/* LineEdit */
QLineEdit{
	font: 12px;
}

/* ScrollBar */
QScrollBar:vertical{
	border: none;
	background-color: rgb(65, 65, 65);
	width: 12px;
	margin: 3px 0 3px 0;
	border-radius: 5px;
}
QScrollBar::handle:vertical{
	background-color: rgb(105, 105, 105);
	min-height: 20px;
	border-radius: 5px;
}
QScrollBar::handle:vertical:hover{
	background-color: rgb(16, 97, 150);
}
QScrollBar::handle:vertical:pressed{
	background-color: rgb(16, 97, 150);
}
QScrollBar::sub-line::vertical{
	border: none;
	background-color: rgb(65, 65, 65);
	height: 0px;
	border-top-left-radius: 7px;
	border-top-right-radius: 7px;
	subcontrol-position: top;
	subcontrol-origin: margin;
}
QScrollBar::add-line::vertical{
	border: none;
	background-color: rgb(65, 65, 65);
	height: 0px;
	border-bottom-left-radius: 7px;
	border-bottom-right-radius: 7px;
	subcontrol-position: bottom;
	subcontrol-origin: margin;
}
QScrollBar:up-arrow:vertical, QScrollBar::down-arrow:vertical {
    background: none;
}
QScrollBar:add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Inner Widget Background */
QScrollArea .QWidget, QScrollArea .QFrame{
	background-color: rgb(65, 65, 65);
}

/* Inner Widget Border */
#TrainingWidget{
	border: 1px solid;
}

#TrainingSubLabelWidget{
	border-top: 1px solid;
	border-left: 1px solid;
	border-right: 1px solid;
}

#TrainingSubInputWidget{
	border-left: 1px solid;
	border-right: 1px solid;
	border-bottom: 1px solid;
}

#ValidationWidget{
	border: 1px solid;
}

#ValidationSubLabelWidget{
	border-top: 1px solid;
	border-left: 1px solid;
	border-right: 1px solid;
}

#ValidationSubInputWidget{
	border-left: 1px solid;
	border-right: 1px solid;
	border-bottom: 1px solid;
}

#TestWidget{
	border: 1px solid;
}

#TestSubLabelWidget{
	border-top: 1px solid;
	border-left: 1px solid;
	border-right: 1px solid;
}

#TestSubInputWidget{
	border-left: 1px solid;
	border-right: 1px solid;
	border-bottom: 1px solid;
}

/* Inner Frame */
.DatasetFrame .QFrame{
	border-left: 1px solid;
	border-right: 1px solid;
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

/* QLabel */
QLabel{
	background-color: transparent;
}

#LoadAllButton{
	background-color: transparent;
}

#LoadAllButton:hover{
	background-color: rgb(16, 97, 150);
}

#LoadAllButton:pressed{
	background-color: rgb(16, 97, 150);
}

#ClearAllButton{
	background-color: transparent;
}

#ClearAllButton:hover{
	background-color: rgb(16, 97, 150);
}

#ClearAllButton:pressed{
	background-color: rgb(16, 97, 150);
}

#LoadConfigButton{
    background-color: rgb(83, 83, 83);
}
#LoadConfigButton:hover{
    background-color: rgb(16, 97, 150);
}
#LoadConfigButton:pressed{
    background-color: rgb(16, 97, 150);
}
"""