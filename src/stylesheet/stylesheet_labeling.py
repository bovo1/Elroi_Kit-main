"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from stylesheet.stylesheet_component import COLORS, IMAGES, RULES

LABELING_STYLESHEET = {
    # Label Main
    "Label_Main QLineEdit": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['greyLineEditBorder'],    
    },
    "Label_Main QTabBar::tab": {
        "padding": RULES['tabBarPadding'],
        "min-width": RULES['tabBarMinWidthForLabeling'],
        "max-width": RULES['tabBarMaxWidthForLabeling'],
        "margin-right": RULES['tabBarMarginRight'],
    },
    "Label_Main QTableWidget": {
        "background-color": COLORS['backgroundSubColor'],
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "Label_Main QHeaderView::section": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "Label_Main QDockWidget": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "Label_Main QSplitter": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "Label_Main QSplitter::handle": {
        "background-repeat": "no-repeat",
    },
    "Label_Main QSplitter::handle:horizontal": {
        "background-image": IMAGES['labelingSplitterHorizontalImage'],
        "background-position": "center",
        "width": RULES['scrollBarWidth'],
    },
    "Label_Main QSplitter::handle:horizontal:pressed": {
        "background-image": IMAGES['labelingSplitterHorizontalActiveImage'],
    },
    "Label_Main QSplitter::handle:vertical": {
        "background-image": IMAGES['labelingSplitterVerticalImage'],
        "background-position": "center",
        "height": RULES['scrollBarHeight'],
    },
    "Label_Main QSplitter::handle:vertical:pressed": {
        "background-image": IMAGES['labelingSplitterVerticalActiveImage'],
    },
    "Label_Main QPushButton": {
        "background-color": "transparent",
    },
    "Label_Main QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "Label_Main QScrollBar:horizontal" :{
        "border": RULES['displayScrollBarHandleBorder'],
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['smallScrollBarHeight'],
        "margin": RULES['scrollBarMarginHorizontal'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "Label_Main QScrollBar::handle:horizontal":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-width": RULES['scrollBarHandleMinWidth'],
    },
    "Label_Main QScrollBar::add-page:horizontal, Label_Main QScrollBar::sub-page:horizontal":{
        "background": "none",
    },
    "Label_Main QScrollBar::add-line:horizontal, Label_Main QScrollBar::sub-line:horizontal":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "width": "0px",
    },
    "Label_Main QScrollBar::handle:horizontal:hover":{
        "background-color": COLORS['accentColor'],
    },
    "Label_Main QScrollBar::handle:horizontal:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "Label_Main QScrollBar:left-arrow:horizontal, Label_Main QScrollBar::right-arrow:horizontal": {
        "background": "none",
    },
    "Label_Main QScrollBar:vertical" :{
        "border": RULES['displayScrollBarHandleBorder'],
        "background-color": COLORS['backgroundSubColor'],
        "margin": RULES['scrollBarMarginVertical'],
        "width": RULES['smallScrollBarWidth'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "Label_Main QScrollBar::handle:vertical":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-height": RULES['scrollBarHandleMinHeight'],
    },
    "Label_Main QScrollBar::add-page:vertical, Label_Main QScrollBar::sub-page:vertical":{
        "background": "none", 
    },
    "Label_Main QScrollBar::add-line:vertical, Label_Main QScrollBar::sub-line:vertical":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "height": "0px",
    },
    "Label_Main QScrollBar::handle:vertical:hover":{
        "background-color": COLORS['accentColor'],
    },
    "Label_Main QScrollBar::handle:vertical:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "Label_Main QScrollBar::up-arrow:vertical, Label_Main QScrollBar::down-arrow:vertical": {
        "background": "none",
    },
    "Label_Main QAbstractScrollArea::corner": {
        "background-color": COLORS['backgroundDarkColor'],
    },

    # Display
    "Display_Form > QWidget" : {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "Display_Form QScrollBar:horizontal": {
        "height": RULES['scrollBarHeight'],
    },
    "Display_Form QScrollBar:vertical": {
        "width": RULES['scrollBarWidth'],
    },

    # Display Menu
    "displayMenu QSlider::groove:horizontal": {
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['horizonSliderHeight'],
        "border-radius": RULES['sliderBorderRadius'],
    },
    "displayMenu QSlider::handle:horizontal": {
        "background-color": "white",
        "width": RULES['sliderHandleWidth'],
        "margin": RULES['sliderHandleMargin'],
        "border-radius": RULES['sliderBorderRadius'],
    },
    "displayMenu QSlider::sub-page:horizontal": {
        "background-color": COLORS['accentColor'],
    },
    "displayMenu QSlider:horizontal:disabled": {
        "background-color": COLORS['disabledColor'],
    },

    # Image Detail
    "Image_detail_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Image_detail_Form QLineEdit": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['greyLineEditBorder'],
    },
    "Image_detail_Form QPushButton": {
        "background-color": "transparent",
    },
    "Image_detail_Form QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "Image_detail_Form QTableWidget": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Image_detail_Form QTableWidget::item:selected": {
        "background-color": COLORS['accentColor'],
    },
    "Image_detail_Form QHeaderView::section": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "Image_detail_Form QLabel": {
        "color": COLORS['textColor'],
    },

    # Label
    "Labellist_Form QLineEdit": {
        "background-color" : COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['greyLineEditBorder'],
    },
    "Labellist_Form QHeaderView::section": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "Labellist_Form QInputDialog": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Labellist_Form QInputDialog QPushButton": {
        "color": COLORS['textColor'],
    },

    # Label sub
    "label_sub_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "label_sub_Form QLabel": {
        "color": COLORS['textColor'],
    },

    # Label sub ess
    "label_sub_ess_option_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "label_sub_ess_option_Form QLabel": {
        "color": COLORS['textColor'],
    },
    "label_sub_ess_option_Form QCheckBox": {
        "color": COLORS['textColor'],
    },

    # Pen Main
    "Pen_Form > QWidget": {
        "background-color": COLORS['backgroundSubColor'],
    },
    "Pen_Form QMenu": {
        "background-color": COLORS['backgroundMainColor'],
    },

    # Pen Sub
    "Pen_style_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Pen_style_Form QLineEdit": {
        "background-color": "white",
        "color": "black",
    },
    "Pen_style_Form QLabel": {
        "color": COLORS['textColor'],
    },
    "Pen_style_Form QPushButton": {
        "background-color": "transparent",
    },
    "Pen_style_Form QLabel#pen_style_main_title": {
        "font": RULES['bigFontSize'],
    },
    "Pen_style_Form QWidget#pen_style_main_title_widget, Pen_style_Form QWidget#pen_style_title_widget, Pen_style_Form QWidget#pen_style_2_widget": {
        "background-color": COLORS['backgroundDarkColor'],
    },

    # Pen Semi auto labeling
    "PenSemiAutoLabelingForm": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "PenSemiAutoLabelingForm QLineEdit": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['greyLineEditBorder'],
    },
    "PenSemiAutoLabelingForm QLabel": {
        "color": COLORS['textColor'],
    },
    "PenSemiAutoLabelingForm QSpinBox": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['greyLineEditBorder'],
    },
    "PenSemiAutoLabelingForm QWidget#penEndmemberTitleWidget, PenSemiAutoLabelingForm QWidget#penSemiAutoLabelingTitleWidget": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "PenSemiAutoLabelingForm QLabel#penEndmemberTitleLabel, PenSemiAutoLabelingForm QLabel#penSemiAutoLabelingTitleLabel": {
        "font": RULES['bigFontSize'],
        "color": COLORS['textColor'],
        "qproperty-alignment": "AlignCenter",
    },
    "PenSemiAutoLabelingForm QPushButton#normalDirectoryLoadBtn, "
    "PenSemiAutoLabelingForm QPushButton#fileAddBtn": {
        "background-color": "transparent",
    },
    "PenSemiAutoLabelingForm QPushButton#normalDirectoryLoadBtn:hover, "
    "PenSemiAutoLabelingForm QPushButton#fileAddBtn:hover": {
        "background-color": COLORS['accentColor'],
    },
    "PenSemiAutoLabelingForm QPushButton#penEndmemberBuildBtn, PenSemiAutoLabelingForm QPushButton#penSemiAutoApplyBtn": {
        "font": "bold",
        "color": COLORS['textColor'],
        "border": RULES['buttonBorder'],
    },
    "PenSemiAutoLabelingForm QPushButton#penEndmemberBuildBtn:hover, PenSemiAutoLabelingForm QPushButton#penSemiAutoApplyBtn:hover": {
        "background-color": COLORS['accentColor'],
    },

    # Pen Rectangle
    "penRectangleSALForm": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "penRectangleSALForm QWidget#mainTitleWidget": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "penRectangleSALForm QLabel": {
        "color": COLORS['textColor'],
    },
    "penRectangleSALForm QLabel#mainTitleLabel": {
        "font": RULES['bigFontSize'],
    },

    # SimilarityMapWindow
    "SimilarityMapWindow": {
        "background-color": COLORS['backgroundMainColor'],
    },

    "SimilarityMapWindow QLabel": {
        "color": COLORS['textColor'],
    },

    "SimilarityMapWindow PlotWidget#similarityHistogramPlot": {
        "background-color": COLORS['backgroundMainColor'],
    },

    # Pen eraser
    "Pen_eraser_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Pen_eraser_Form QLineEdit": {
        "background-color": "white",
        "color": "black",
    },
    "Pen_eraser_Form QLabel": {
        "color": COLORS['textColor'],
    },
    "Pen_eraser_Form QLabel#pen_eraser_main_title": {
        "font": RULES['bigFontSize'],
    },
    "Pen_eraser_Form QWidget#pen_eraser_main_title_widget": {
        "background-color": COLORS['backgroundDarkColor'],
    },

    # display sub rgb change
    "Display_rgb_change_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Display_rgb_change_Form QLabel": {
        "color": COLORS['textColor'],
        "font": RULES['smallFontSize'],
    },

    # pen sub adv opacity option
    "pen_sub_adv_opacity_option_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "pen_sub_adv_opacity_option_Form QLabel": {
        "color": COLORS['textColor'],
    },

    # Graph
    "Graph_Form QListWidget": {
        "color": COLORS['textColor'],
    },

    # Graph sub
    "graph_sub_Form": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "graph_sub_Form QLabel": {
        "color": COLORS['textColor'],
    },

    # Graph Group
    "graphGroupForm QLineEdit": {
        "background-color" : COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['greyLineEditBorder'],
    },
    "graphGroupForm QHeaderView::section": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },

    # Graph Option
    "graphOptionForm QWidget": {
        "color": COLORS['textColor'],
    },
    "graphOptionForm QSlider::groove:horizontal": {
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['horizonSliderHeight'],
        "border-radius": RULES['sliderBorderRadius'],
    },
    "graphOptionForm QSlider::handle:horizontal": {
        "background-color": "white",
        "width": RULES['sliderHandleWidth'],
        "margin": RULES['sliderHandleMargin'],
        "border-radius": RULES['sliderBorderRadius'],
    },
    "graphOptionForm QSlider::sub-page:horizontal": {
        "background-color": COLORS['accentColor'],
    },

    # Graph Export
    "graphExportForm": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollArea": {
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "outline": "none",
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollArea .QWidget": {
        "background-color": COLORS['backgroundSubColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar:horizontal" :{
        "border": RULES['displayScrollBarHandleBorder'],
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['smallScrollBarHeight'],
        "margin": RULES['scrollBarMarginHorizontal'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::handle:horizontal":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-width": RULES['scrollBarHandleMinWidth'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::add-page:horizontal, QMainWindow#graphExportMatplotlibWindow QScrollBar::sub-page:horizontal":{
        "background": "none",
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::add-line:horizontal, QMainWindow#graphExportMatplotlibWindow QScrollBar::sub-line:horizontal":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "width": "0px",
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::handle:horizontal:hover":{
        "background-color": COLORS['accentColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::handle:horizontal:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar:left-arrow:horizontal, QMainWindow#graphExportMatplotlibWindow QScrollBar::right-arrow:horizontal": {
        "background": "none",
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar:vertical" :{
        "border": RULES['displayScrollBarHandleBorder'],
        "background-color": COLORS['backgroundSubColor'],
        "margin": RULES['scrollBarMarginVertical'],
        "width": RULES['smallScrollBarWidth'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::handle:vertical":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-height": RULES['scrollBarHandleMinHeight'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::add-page:vertical, QMainWindow#graphExportMatplotlibWindow QScrollBar::sub-page:vertical":{
        "background": "none", 
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::add-line:vertical, QMainWindow#graphExportMatplotlibWindow QScrollBar::sub-line:vertical":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "height": "0px",
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::handle:vertical:hover":{
        "background-color": COLORS['accentColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::handle:vertical:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QScrollBar::up-arrow:vertical, QMainWindow#graphExportMatplotlibWindow QScrollBar::down-arrow:vertical": {
        "background": "none",
    },
    "QMainWindow#graphExportMatplotlibWindow QAbstractScrollArea::corner": {
        "background-color": COLORS['backgroundSubColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow FormDialog": {
        "background-color": COLORS['backgroundSubColor'],
    },
    "SubplotToolQt": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow FormDialog QLabel, SubplotToolQt QLabel, "
    "QMainWindow#graphExportMatplotlibWindow FormDialog QGroupBox, SubplotToolQt QGroupBox": {
        "color": COLORS['textColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow FormDialog QLineEdit, QMainWindow#graphExportMatplotlibWindow FormDialog QSpinBox, QMainWindow#graphExportMatplotlibWindow FormDialog QDoubleSpinBox, QMainWindow#graphExportMatplotlibWindow FormDialog QComboBox, "
    "SubplotToolQt QDoubleSpinBox": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
        "border": RULES['subColorLineEditBorder'],
    },
    "QMainWindow#graphExportMatplotlibWindow FormDialog QPushButton, SubplotToolQt QPushButton": {
        "background-color": COLORS['backgroundSubColor'],
        "color": COLORS['textColor'],
        "border": RULES['darkColorLineEditBorder'],
    },
    "QMainWindow#graphExportMatplotlibWindow FormDialog QPushButton:hover, SubplotToolQt QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "QMainWindow#graphExportMatplotlibWindow QAbstractItemView": {
        "background-color": COLORS['backgroundSubColor'],
        "color": COLORS['textColor'],
        "selection-background-color": COLORS['accentColor'],
        "outline": "none",
    },
    "QMainWindow#graphExportMatplotlibWindow QToolBar": {
        "border": "none",
    },
    "graphExportForm QLabel": {
        "color": COLORS['textColor'],
    },
    "graphExportForm QLineEdit": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": RULES['subColorLineEditBorder'],
        "color": COLORS['textColor'],
    },
    "graphExportForm QTreeWidget": {
        "background-color": COLORS['backgroundSubColor'],
        "outline": "none",
        "border": "none",
        "color": COLORS['textColor'],
    },
    "graphExportForm QTreeWidget::item:selected": {
        "background-color": COLORS['accentColor'],
    },
    "graphExportForm QPushButton": {
        "background-color": COLORS['backgroundSubColor'],
        "border": RULES['darkColorLineEditBorder'],
        "color": COLORS['textColor'],
        "outline": "none",
    },
    "graphExportForm QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "graphExportForm QPushButton:disabled": {
        "color": COLORS['disabledColor'],
    },
    "graphExportForm QGroupBox": {
        "color": COLORS['textColor'],
    },
    "graphExportForm QSpinBox": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": RULES['darkColorLineEditBorder'],
        "color": COLORS['textColor'],
    },
    "graphExportForm QSpinBox:disabled": {
        "color": COLORS['disabledColor'],
    },
    "graphExportForm QToolBar": {
        "border": "none",
    },
    "graphExportForm QComboBox": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": RULES['darkColorLineEditBorder'],
        "color": COLORS['textColor'],
    },
    "graphExportForm QAbstractItemView": {
        "background-color": COLORS['backgroundSubColor'],
        "color": COLORS['textColor'],
        "selection-background-color": COLORS['accentColor'],
        "outline": "none",
    },
    "graphExportForm QSlider::groove:horizontal": {
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['horizonSliderHeight'],
        "border-radius": RULES['sliderBorderRadius'],
    },
    "graphExportForm QSlider::handle:horizontal": {
        "background-color": "white",
        "width": RULES['sliderHandleWidth'],
        "margin": RULES['sliderHandleMargin'],
        "border-radius": RULES['sliderBorderRadius'],
    },
    "graphExportForm QSlider::sub-page:horizontal": {
        "background-color": COLORS['accentColor'],
    },
}