stylesheet = """
QWidget{
	background-color: rgb(83, 83, 83);
	color: white;
	font: 15px;
}

QPlainTextEdit {
	border: 1px solid grey;
	background-color: black;
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


/* PushButton */

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

QTableView {
	background-color: rgb(83, 83, 83);
}

QHeaderView::section {
    background-color: rgb(83, 83, 83);
}
"""