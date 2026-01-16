stylesheet = """
QMainWindow{
    background-color: rgb(83, 83, 83);
    border: 1px solid black;
    border-radius: 7px
}
QPushButton{
    background-color: transparent;
}
QLabel{
    background-color: transparent;
    color : white;
}
QLabel#pen_style_main_title{
    font: 20px;
}
QLabel#pen_style_static_size, QLineEdit#pen_style_static_size, QLabel#pen_style_static_pix{
    font: 15px;
}
QWidget#pen_style_picture_widget, QWidget#pen_style_static_widget, QWidget#pen_style_static_range_widget, QWidget#pen_style_widget{
    background-color: rgb(83, 83, 83);
}
QWidget#pen_style_main_title_widget, QWidget#pen_style_title_widget, QWidget#pen_style_2_widget{
    background-color: rgb(40, 39, 40);
}

QPushButton {
    background-color: transparent;
}

QPushButton:hover {
    background-color: rgb(16, 97, 150);
}

QPushButton:pressed {
    background-color: rgb(16, 97, 150);
}
"""