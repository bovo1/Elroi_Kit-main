stylesheet = """
QTableView {
    background-color: rgb(65, 65, 65);
}
QTableWidget::item { 
    background-color: rgb(83, 83, 83);
    color: white;
}
QTableWidget::item:selected {
    background-color: rgb(16, 97, 150);
}
QHeaderView::section {
    background-color: rgb(83, 83, 83);
    color: white;
}

QWidget{
    background-color: rgb(83, 83, 83);
}

QLabel{
    background-color: transparent;
    color : white;
    font: 12px;
}

QPushButton{
    background-color: transparent;
}
QPushButton:disabled{
    background-color: rgb(65, 65, 65);
}
QPushButton:hover {
    background-color: rgb(16, 97, 150);
}
QPushButton:pressed {
    background-color: rgb(16, 97, 150);
}

QGroupBox::title {
    color : white;
    font: 20px;
}
QGroupBox:disabled{
    background-color: rgb(65, 65, 65);
}

QLineEdit{
    background-color: rgb(40, 39, 40);
    font: 15px;
    color : white;
    border: 2px solid gray;
}
QLineEdit:disabled{
	background-color: rgb(65, 65, 65);
}

/* scroll vertical */
QScrollBar:vertical{
	border: none;
	background-color: rgb(65, 65, 65);
	width: 10px;
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
"""