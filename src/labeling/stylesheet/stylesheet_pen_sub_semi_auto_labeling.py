stylesheet = """
QWidget#PenSemiAutoLabelingForm{
    background-color: rgb(83, 83, 83);
}
QPushButton {
    background-color: transparent;
    font: 15px;
    color: white;
}
QPushButton:hover,
QPushButton:pressed {
    background-color: rgb(16, 97, 150);
}

QPushButton#penEndmemberBuildBtn,
QPushButton#penEndmemberSaveBtn {
    font: bold 15px;
    color: white;
    border: 2px solid gray;
}
QLineEdit,
QSpinBox{
    background-color: rgb(39,38,39);
    font: 13px;
    color: white;
    border: 2px solid gray;
}
QLabel {
    background-color: transparent;
    color: white;
    font: 15px;
}
QWidget#penEndmemberTitleWidget,
QWidget#penSemiAutoLabelingTitleWidget,
QWidget#penEndmemberSaveTitleWidget {
    background-color:  rgb(40, 39, 40);
}

QLabel#penEndmemberTitleLabel,
QLabel#penSemiAutoLabelingTitleLabel,
QLabel#penEndmemberSaveTitleLabel {
    font: 18px;
    qproperty-alignment: 'AlignCenter';
}

"""