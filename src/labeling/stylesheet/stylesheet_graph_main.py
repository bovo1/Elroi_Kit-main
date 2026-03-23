stylesheet = """
QPushButton{
    background-color: transparent;
}

QPushButton:hover {
    background-color: rgb(16, 97, 150);
}

QPushButton:pressed {
    background-color: rgb(16, 97, 150);
}

QListWidget{
    border-color:transparent;
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

QComboBox{
	font: 13px;
}
"""