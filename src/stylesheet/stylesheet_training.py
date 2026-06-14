"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from stylesheet.stylesheet_component import COLORS, IMAGES, RULES

TRAINING_STYLESHEET = {
    # Training Main
    "Train_Main QTabBar::tab": {
        "padding": RULES['tabBarPadding'],
        "margin-right": RULES['tabBarMarginRight'],
        "min-width": RULES['tabBarMinWidthForTrainingAdvanced'],
    },
    "Train_Main QLineEdit": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
        "border": RULES['whiteLineEditBorder'],
    },
    "Train_Main QComboBox": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Train_Main QComboBox QAbstractItemView": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Train_Main QTextEdit": {
        "background-color": COLORS['terminalColor'],
        "color": COLORS['textColor'],
        "border": RULES['terminalBorder'],
    },
    "Train_Main QScrollBar:horizontal" :{
        "border": "none",
        "background-color": COLORS['backgroundSubColor'],
        "height": RULES['smallScrollBarHeight'],
        "margin": RULES['scrollBarMarginHorizontal'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "Train_Main QScrollBar::handle:horizontal":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-width": RULES['scrollBarHandleMinWidth'],
    },
    "Train_Main QScrollBar::add-page:horizontal, Train_Main QScrollBar::sub-page:horizontal":{
        "background": "none",
    },
    "Train_Main QScrollBar::add-line:horizontal, Train_Main QScrollBar::sub-line:horizontal":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "width": "0px",
    },
    "Train_Main QScrollBar::handle:horizontal:hover":{
        "background-color": COLORS['accentColor'],
    },
    "Train_Main QScrollBar::handle:horizontal:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "Train_Main QScrollBar:left-arrow:horizontal, Train_Main QScrollBar::right-arrow:horizontal": {
        "background": "none",
    },
    "Train_Main QScrollBar:vertical" :{
        "border": "none",
        "background-color": COLORS['backgroundSubColor'],
        "margin": RULES['scrollBarMarginVertical'],
        "width": RULES['smallScrollBarWidth'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    "Train_Main QScrollBar::handle:vertical":{
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-height": RULES['scrollBarHandleMinHeight'],
    },
    "Train_Main QScrollBar::add-page:vertical, Train_Main QScrollBar::sub-page:vertical":{
        "background": "none", 
    },
    "Train_Main QScrollBar::add-line:vertical, Train_Main QScrollBar::sub-line:vertical":{
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
        "height": "0px",
    },
    "Train_Main QScrollBar::handle:vertical:hover":{
        "background-color": COLORS['accentColor'],
    },
    "Train_Main QScrollBar::handle:vertical:pressed":{
        "background-color": COLORS['accentColor'],
    },
    "Train_Main QScrollBar::up-arrow:vertical, Train_Main QScrollBar::down-arrow:vertical": {
        "background": "none",
    },
    "Train_Main QAbstractScrollArea::corner": {
        "background-color": COLORS['backgroundDarkColor'],
    },

    # Dataset
    "Dataset_Form QScrollArea QWidget#TrainingWidget": {
        "background-color" : COLORS['backgroundSubColor'],
        "border": RULES['datasetFrameBorder'],
    },
    "Dataset_Form QScrollArea QWidget#ValidationWidget": {
        "background-color" : COLORS['backgroundSubColor'],
        "border": RULES['datasetFrameBorder'],
    },
    "Dataset_Form QScrollArea QWidget#TestWidget": {
        "background-color" : COLORS['backgroundSubColor'],
        "border": RULES['datasetFrameBorder'],
    },
    "Dataset_Form QLineEdit": {
        "font-size": RULES['smallFontSize'],
    },
    "Dataset_Form QPushButton": {
        "background-color": "transparent",
    },
    "Dataset_Form QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "Dataset_Form QPushButton#LoadConfigButton": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Dataset_Form QPushButton#LoadConfigButton:hover": {
        "background-color": COLORS['accentColor'],
    },

    # Hyperparameter
    "Hyperparameter_Form QWidget#ParameterSettingsMainWidget": {
        "background-color" : COLORS['backgroundMainColor'],
    },
    "Hyperparameter_Form QScrollArea": {
        "border": "none",
    },
    "Hyperparameter_Form QFrame#vline": {
        "border": "none",
        "border-left": RULES['verticalLineBorder'],
        "border-right": RULES['verticalLineLightBorder'],
    },
    "Hyperparameter_Form QFrame#hline": {
        "border": "none",
        "border-top": RULES['horizonLineBorder'],
        "border-bottom": RULES['horizonLineLightBorder'],
    },

    "Hyperparameter_Form QPushButton#ParameterLoadPushButton, "
    "Hyperparameter_Form QPushButton#ParameterResetPushButton": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Hyperparameter_Form QPushButton#ParameterLoadPushButton:hover, "
    "Hyperparameter_Form QPushButton#ParameterResetPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },

    "Hyperparameter_Form QPushButton#CommonSettingsSavePathPushButton, "
    "Hyperparameter_Form QPushButton#CommonSettingsLoadPathPushButton, "
    "Hyperparameter_Form QPushButton#CommonSettingsLoadRefPathPushButton": {
        "background-color": "transparent",
    },
    "Hyperparameter_Form QPushButton#CommonSettingsSavePathPushButton:hover, "
    "Hyperparameter_Form QPushButton#CommonSettingsLoadPathPushButton:hover, "
    "Hyperparameter_Form QPushButton#CommonSettingsLoadRefPathPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },

    # Run
    "Run_Form QPushButton#StartButton, "
    "Run_Form QPushButton#StopButton": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Run_Form QPushButton#StartButton:hover, "
    "Run_Form QPushButton#StopButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "Run_Form QPushButton#StartButton:hover, "
    "Run_Form QPushButton#StopButton:hover": {
        "background-color": COLORS['accentColor'],
    },

    # Result
    "Result_Form QFrame#ResultControlVerticalLine1": {
        "border": "none",
        "border-left": RULES['verticalLineBorder'],
        "border-right": RULES['verticalLineLightBorder'],
    },
    "Result_Form QFrame#ResultControlVerticalLineErr": {
        "border": "none",
        "border-left": RULES['verticalLineBorder'],
        "border-right": RULES['verticalLineLightBorder'],
    },
    "Result_Form QFrame#ResultControlVerticalLine2": {
        "border": "none",
        "border-left": RULES['verticalLineBorder'],
        "border-right": RULES['verticalLineLightBorder'],
    },
    "Result_Form QFrame#OutputImageGroupBoxHorizontalLine1": {
        "border": "none",
        "border-top": RULES['horizonLineBorder'],
        "border-bottom": RULES['horizonLineLightBorder'],
    },
    "Result_Form QComboBox": {
        "width": RULES['resultImageViewComboBoxWidth'],
    },
    "Result_Form QPushButton#ThresholdButton": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "Result_Form QPushButton#ThresholdButton:hover": {
        "background-color": COLORS['accentColor'],
    },
}