"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from stylesheet.stylesheet_component import COLORS, IMAGES, RULES

ADVANCED_STYLESHEET = {
    # Advanced Main
    "Advanced_Main QTabBar::tab": {
        "padding": RULES['tabBarPadding'],
        "margin-right": RULES['tabBarMarginRight'],
        "min-width": RULES['tabBarMinWidthForTrainingAdvanced'],
    },
    "Advanced_Main QTableWidget": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "Advanced_Main QHeaderView::section": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "Advanced_Main QLineEdit": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "border": RULES['whiteLineEditBorder'],
    },
    "Advanced_Main QSpinBox": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Advanced_Main QDoubleSpinBox": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Advanced_Main QComboBox": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Advanced_Main QComboBox QAbstractItemView": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Advanced_Main QPlainTextEdit": {
        "background-color": COLORS['terminalColor'],
        "color": COLORS['textColor'],
        "border": RULES['terminalBorder'],
    },
    "Advanced_Main QScrollBar:horizontal" :{
        "border": "none",
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['smallScrollBarHeight'],
        "margin": RULES['scrollBarMarginHorizontal'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "Advanced_Main QScrollBar::handle:horizontal":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-width": RULES['scrollBarHandleMinWidth'],
    },
    "Advanced_Main QScrollBar::add-page:horizontal, Advanced_Main QScrollBar::sub-page:horizontal":{
        "background": "none",
    },
    "Advanced_Main QScrollBar::add-line:horizontal, Advanced_Main QScrollBar::sub-line:horizontal":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "width": "0px",
    },
    "Advanced_Main QScrollBar::handle:horizontal:hover":{
        "background-color": COLORS['accentColor'],
    },
    "Advanced_Main QScrollBar::handle:horizontal:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "Advanced_Main QScrollBar:left-arrow:horizontal, Advanced_Main QScrollBar::right-arrow:horizontal": {
        "background": "none",
    },
    "Advanced_Main QScrollBar:vertical" :{
        "border": "none",
        "background-color": COLORS['backgroundSubColor'],
        "margin": RULES['scrollBarMarginVertical'],
        "width": RULES['smallScrollBarWidth'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "Advanced_Main QScrollBar::handle:vertical":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-height": RULES['scrollBarHandleMinHeight'],
    },
    "Advanced_Main QScrollBar::add-page:vertical, Advanced_Main QScrollBar::sub-page:vertical":{
        "background": "none", 
    },
    "Advanced_Main QScrollBar::add-line:vertical, Advanced_Main QScrollBar::sub-line:vertical":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "height": "0px",
    },
    "Advanced_Main QScrollBar::handle:vertical:hover":{
        "background-color": COLORS['accentColor'],
    },
    "Advanced_Main QScrollBar::handle:vertical:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "Advanced_Main QScrollBar::up-arrow:vertical, Advanced_Main QScrollBar::down-arrow:vertical": {
        "background": "none",
    },
    "Advanced_Main QAbstractScrollArea::corner": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "Advanced_Main QPushButton": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Advanced_Main QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },

    # Predict Label
    "advanced_predictlabel_Form QFrame#advanced_predictlabel_image_groupbox_HorizontalLine": {
        "border": "none",
        "border-top": RULES['horizonLineBorder'],
        "border-bottom": RULES['horizonLineLightBorder'],
    },
    "advanced_predictlabel_Form QFrame#ResultControlVerticalLine1": {
        "border": "none",
        "border-left": RULES['verticalLineBorder'],
        "border-right": RULES['verticalLineLightBorder'],
    },

    # Label Correction
    "advanced_label_correction_Form QSplitter#outputSplitter": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "advanced_label_correction_Form QSplitter#outputSplitter::handle:horizontal": {
        "background-image": "none",
    },
    "advanced_label_correction_Form QSplitter#outputSplitter::handle:vertical": {
        "background-image": "none",
    },
    "advanced_label_correction_Form QDockWidget": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "advanced_label_correction_Form QFrame#advanced_label_correction_image_groupbox_HorizontalLine": {
        "border": "none",
        "border-top": RULES['horizonLineBorder'],
        "border-bottom": RULES['horizonLineLightBorder'],
    },
    "advanced_label_correction_Form QFrame#resultControlVerticalLine1": {
        "border": "none",
        "border-left": RULES['verticalLineBorder'],
        "border-right": RULES['verticalLineLightBorder'],
    },

    # Label Aggregation
    "advanced_label_aggregation_Form QLineEdit:disabled": {
        "color": COLORS['disabledColor'],
    },
}