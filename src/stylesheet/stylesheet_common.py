"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from stylesheet.stylesheet_component import COLORS, IMAGES, RULES

STYLE = {
    # Top
    "Top_MainWindow_Form": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "Top_MainWindow_Form QPushButton": {
        "background-color": "transparent",
    },
    "Top_MainWindow_Form QPushButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "Top_MainWindow_Form QLabel": {
        "font-size": RULES['titleFontSize'],
        "color": COLORS['textColor'],
    },

    # Mid
    "Mid_MainWindow_Form": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    "Mid_MainWindow_Form QToolBar": {
        "padding-left": RULES['midToolBarPadding'],
        "spacing": RULES['midToolBarSpacing'],
        "background": f"no-repeat right/ {IMAGES['elroilabLogoImage']}",
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
    },
    "Mid_MainWindow_Form QToolButton:hover": {
        "background-color": "transparent",
    },
    "Mid_MainWindow_Form QLabel": {
        "color": COLORS['textColor'],
    },

    # QMenuBar
    "QMenuBar": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
    },
    "QMenuBar::item": {
        "background-color": "transparent",
        "color": COLORS['textColor'],
    },
    "QMenuBar::item:selected": {
        "background-color": "transparent",
        "color": COLORS['accentColor'],
    },

    # QMenu
    "QMenu": {
        "background-color": COLORS['backgroundDarkColor'],
        "color": COLORS['textColor'],
    },
    "QMenu::item:selected": {
        "background-color": "transparent",
        "color": COLORS['accentColor'],
    },
    "QMenu .QLabel, QCheckBox, QRadioButton": {
        "color": COLORS['textColor'],
    },

    # QGroupBox
    "QGroupBox": {
        "color": COLORS['textColor'],
    },

    # QStatusBar
    "QStatusBar": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },
    "QStatusBar::item": {
        "border": "none",
    },

    # QTabBar
    "QTabBar": {
        "color": COLORS['textColor'],
    },
    "QTabBar::tab:selected": {
        "background-color": COLORS['backgroundMainColor'],
    },
    "QTabBar::tab:!selected": {
        "background-color": COLORS['backgroundSubColor'],
    },

    # QTabWidget
    "QTabWidget::pane": {
        "border": "none",
        "background-color": COLORS['backgroundSubColor'],
    },
    "QTabWidget > QWidget": {
        "background-color": COLORS['backgroundMainColor'],
    },

    # QTableView
    "QTableView": {
        "background-color": COLORS['backgroundSubColor'],
    },

    # QTableWidget
    "QTableWidget::item": {
        "background-color": COLORS['backgroundMainColor'],
        "color": COLORS['textColor'],
    },

    # QProgressBar
    "QProgressBar": {
        "background-color": "transparent",
        "color": COLORS['textColor'],
        "border": RULES['progressBarBorder'],
        "border-radius": RULES['progressBarBorderRadius'],
        "text-align": "center",
    },
    "QProgressBar::chunk": {
        "background-color": COLORS['progressBarColor'],
    },
}