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

QWidget#label_list_title_widget{
    border-color: rgb(39, 38, 39);
    border-style: solid;
    border-width:1px;
} 
QDialog{ 
	background-color: rgb(83, 83, 83);
}
QLineEdit, QDialog>QLineEdit{
    background-color: rgb(39, 38, 39);
    font: 15px;
    color : white;
    border: 2px solid gray;
}

QLabel{
    font: 15px;
    color : white;
}
QPushButton#label_list_color{
	border-color: rgb(39, 38, 39);
    border-style: solid;
    border-width:1px;
}


QComboBox{
	background-color: rgb(65, 65, 65);
	color: rgb(255, 255, 255);
	border: 1px solid gray;
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

/* horizon */
QScrollBar:horizontal{
	border: none;
	background-color: rgb(65, 65, 65);
	height: 10px;
    margin: 0 3px 0 3px ;
	border-radius: 5px;
}

QScrollBar::handle:horizontal{
	background-color: rgb(105, 105, 105);
	min-width: 20px;
	border-radius: 5px;
}
QScrollBar::handle:horizontal:hover{
	background-color: rgb(16, 97, 150);
	
}
QScrollBar::handle:horizontal:pressed{
	background-color: rgb(16, 97, 150);
}
/*left arrow button */
QScrollBar::sub-line::horizontal{
	border: none;
	background-color: rgb(65, 65, 65);
	width: 0px;
	border-left-radius: 7px;
	border-right-radius: 7px;
	subcontrol-position: left;
	subcontrol-origin: margin;
}
/*right arrow button */
QScrollBar::add-line::horizontal{
	border: none;
	background-color: rgb(65, 65, 65);
	width: 0px;
	border-left-radius: 7px;
	border-right-radius: 7px;
	subcontrol-position: right;
	subcontrol-origin: margin;
}
QScrollBar::add-line::horizontal:hover, QScrollBar::sub-line::horizontal:hover{
	background-color: rgb(66, 66, 66);
}
QScrollBar::add-line::horizontal:pressed, QScrollBar::sub-line::horizontal:pressed{
	background-color: rgb(16, 97, 150);
}
/* reset arrorw */
QScrollBar:left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
    background: none;
}
QScrollBar:add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

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