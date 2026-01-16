stylesheet = """
/* Widget */
QWidget{
	background-color: rgb(83, 83, 83);
	color: white;
	font: 15px;
}

/* LineEdit */
QLineEdit{
	font: 12px;
}

/* ComboBox */
#CommonSettingsModelComboBox{
	width: 70px;
	height: 22px;
}
#GPUSettingsDeviceComboBox{
	width: 150px;
	height: 22px;
}

/* ScrollArea */
QScrollArea{
	border: none;
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

QScrollBar:horizontal{
	border: none;
	background-color: rgb(65, 65, 65);
	height: 12px;
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
QScrollBar::sub-line::horizontal{
	border: none;
	background-color: rgb(65, 65, 65);
	width: 0px;
	subcontrol-position: left;
	subcontrol-origin: margin;
}
QScrollBar::add-line::horizontal{
	border: none;
	background-color: rgb(65, 65, 65);
	width: 0px;
	subcontrol-position: right;
	subcontrol-origin: margin;
}
QScrollBar::add-line::horizontal:hover, QScrollBar::sub-line::horizontal:hover{
	background-color: rgb(66, 66, 66);
}
QScrollBar::add-line::horizontal:pressed, QScrollBar::sub-line::horizontal:pressed{
	background-color: rgb(16, 97, 150);
}
QScrollBar:left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
    background: none;
}

QScrollBar:add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
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

#ParameterResetPushButton{
    background-color: rgb(83, 83, 83);
}
#ParameterResetPushButton:hover{
    background-color: rgb(16, 97, 150);
}
#ParameterResetPushButton:pressed{
    background-color: rgb(16, 97, 150);
}

#ParameterLoadPushButton{
    background-color: rgb(83, 83, 83);
}
#ParameterLoadPushButton:hover{
    background-color: rgb(16, 97, 150);
}
#ParameterLoadPushButton:pressed{
    background-color: rgb(16, 97, 150);
}

"""