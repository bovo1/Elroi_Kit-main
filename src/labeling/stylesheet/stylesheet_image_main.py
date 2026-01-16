stylesheet = """
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

QLabel{
    font: 15px;
    color : white;
}

QLineEdit{
    background-color: rgb(39, 38, 39);
    font: 15px;
    color : white;
    border: 2px solid gray;
}

/* scroll vertical */
QScrollBar:vertical{
	border-color:transparent; 
    border-style: solid;
    border-width:1px;
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

/*top arrow button */
QScrollBar::sub-line::vertical{
	border: none;
	background-color: rgb(65, 65, 65);
	height: 0px;
	border-top-left-radius: 7px;
	border-top-right-radius: 7px;
	subcontrol-position: top;
	subcontrol-origin: margin;
}
/*bottom arrow button */
QScrollBar::add-line::vertical{
	border: none;
	background-color: rgb(65, 65, 65);
	height: 0px;
	border-bottom-left-radius: 7px;
	border-bottom-right-radius: 7px;
	subcontrol-position: bottom;
	subcontrol-origin: margin;
}
QScrollBar::sub-line::vertical:hover, QScrollBar::add-line::vertical:hover{
	background-color: rgb(66, 66, 66);
}
QScrollBar::sub-line::vertical:pressed, QScrollBar::add-line::vertical:pressed{
	background-color: rgb(16, 97, 150);
}
/* reset arrorw */
QScrollBar:up-arrow:vertical, QScrollBar::down-arrow:vertical {
    background: none;
}
QScrollBar:add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* QTableView */
QTableView {
    background-color: rgb(65, 65, 65);
}
QTableWidget::item { 
    background-color: rgb(83, 83, 83);
    color: white;
}

QHeaderView::section {
    background-color: rgb(83, 83, 83);
    color: white;
}
"""
