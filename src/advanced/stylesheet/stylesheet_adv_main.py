""" Ensure all tabs have equal spacing and consistent padding for uniform appearance"""
stylesheet = """
QTabBar{
	font: 15px;
	color: white;
}

QTabBar::tab{
	padding: 5px;
	padding-left: 10px;
	padding-right: 10px;
    min-width: 140px;
    width: 140px;
    margin-right: 5px;
}

QTabBar::tab::selected{
	background-color: rgb(83, 83, 83);
}

QTabBar::tab::!selected{
	background-color: rgb(66, 66, 66);
}

QWidget::pane{}

QTabWidget > QWidget{
	background-color: rgb(83, 83, 83);
}
"""