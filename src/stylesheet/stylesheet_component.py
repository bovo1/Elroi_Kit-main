"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

"""
    ElroiKit contains a mix of widgets that follow PyQt's default styles and those that follow custom styles.
    Additionally, there are widgets that follow PyQt’s default style but apply different styles depending on the UI page (labeling, training, advanced).
    For example, widgets such as QLineEdit and QPushButton fall into this category. 
    Applying a style to a widget that follows PyQt’s default style will override PyQt’s default style.
    For the above reasons, widgets that follow PyQt's default style should apply a specific style rather than a Common Style.
    So, to efficiently manage and apply PyQt’s default styles and custom styles, style sheets are managed separately as Common Styles and Specific Styles.

    [Common style and Specific Style]
    1. Common Style:
        - Common style is a style that applies the style that you want to apply to a particular widget to all of the same type widgets in the UI.
          For example, if you specify the color of QPushButton with a common style, all QPushButtons in the UI appear in the same color.
        - example) "QPushButton" : {"color": "red", "background-color": "blue"}
    
    2. Specific Style:
        - Specific style is a style that applies only to selected UI widgets.
          For example, if you specify the color of QPushButton with a specific style, only the QPushButton with the specified identifier appears in that color.
        - example) "Label_Main QLineEdit", "Train_Main QPushButton", "Dataset_Form QPushButton#LoadConfigButton"
    
    [Style Precedence]
    - style precedence is determined by the specificity of the selector. The more specific the selector (e.g., using identifiers like # or .), the higher its precedence.
    - For example, a style defined for "QPushButton#myButton" will take precedence over a style defined for "QPushButton" because it is more specific.
    - If specificity is equal, the later rule in the stylesheet will take precedence.

    [Qt Style Syntax Reference]
    https://doc.qt.io/archives/qt-5.15/stylesheet-reference.html
"""

def buildStylesheet(globalStyle: dict = None, specificStyle: list = None) -> str:
    """
        @description : Build the complete stylesheet by combining global styles and specific styles for different components.
        @author : GaEun Hwang (2026.05.06)
    """
    # input globalStyle and specificStyle in styles dictionary
    styles = {**globalStyle, **{k: v for style in specificStyle for k, v in style.items()}}

    styleBlocks = []
    for selector, properties in styles.items():
        if properties:
            # Convert the properties dictionary into a CSS block string
            block = "\n".join(f"{k}: {v};" for k, v in properties.items())
            styleBlocks.append(f"{selector}{{\n{block}\n}}")

    return "\n\n".join(styleBlocks)


COLORS = {
    # COLORS is a dictionary that defines the colors used in the stylesheet
    # When adding a new color, you must clearly state what purpose the color will be used for and the RGB values ​​of that color
    # Example) "colorForWhat" : "rgb(255, 255, 255)"

    "backgroundMainColor": "rgb(83, 83, 83)",
    "backgroundSubColor": "rgb(65, 65, 65)",
    "backgroundDarkColor": "rgb(39, 38, 39)",
    "backgroundLightColor": "rgb(105, 105, 105)",
    "accentColor": "rgb(16, 97, 150)",
    "scrollHandleColor": "rgb(105, 105, 105)",
    "terminalColor": "rgb(0, 0, 0)",
    "progressBarColor": "rgb(119, 136, 153)",
    "disabledColor": "gray",
    "textColor": "rgb(255, 255, 255)",
    "labelTitleColor": "rgb(40, 39, 40)",
}

IMAGES = {
    # IMAGES is a dictionary that defines the common images used in the stylesheet
    # Do not add images that are used as icons for specific widgets, such as buttons
    # Example) "imageForWhat" : "url(image path)"

    "elroilabLogoImage": "url('ico/labeling/logo/logo.png')",
    "labelingSplitterHorizontalImage": "url(ico/labeling/splitter/splitter_bar_horizontal_white.png)",
    "labelingSplitterVerticalImage": "url(ico/labeling/splitter/splitter_bar_vertical_white.png)",
    "labelingSplitterHorizontalActiveImage": "url(ico/labeling/splitter/splitter_bar_horizontal_yellow.png)",
    "labelingSplitterVerticalActiveImage": "url(ico/labeling/splitter/splitter_bar_vertical_yellow.png)",
}

RULES = {
    # RULES is a dictionary that defines the common rules (size, margin, border, etc.) used in the stylesheet
    # When adding a rule, you must clearly write which rule applies to which part of the widget
    # Example) "ruleForWhat" : "5px / 1px solid black / etc..."
    # For example, if the color of the border is one of the colors defined in the COLORS Dictionary, write it as below using f-string
    # "ruleForWhat": f"1px solid {COLORS['colorForWhat']}"

    # Font size
    "smallFontSize": "13px",
    "bigFontSize": "20px",
    "titleFontSize": "14px",

    # ScrollBar
    "scrollBarWidth": "15px",
    "scrollBarHeight": "15px",
    "smallScrollBarWidth": "12px",
    "smallScrollBarHeight": "12px",
    "scrollBarHandleMinWidth": "20px",
    "scrollBarHandleMinHeight": "20px",
    "scrollBarMarginVertical": "3px 0 3px 0",
    "scrollBarMarginHorizontal": "0 3px 0 3px",
    "scrollBarBorderRadius": "5px",
    "displayScrollBarHandleBorder": "1px solid transparent",

    # ProgressBar
    "progressBarBorderRadius": "5px",
    "progressBarBorder": "1px solid grey",

    # QWidget
    "whiteWidgetBorder": "1px solid white",

    # LineEdit
    "whiteLineEditBorder": "2px solid white",
    "greyLineEditBorder": "2px solid grey",
    "subColorLineEditBorder": f"1px solid {COLORS['backgroundSubColor']}",
    "darkColorLineEditBorder": f"1px solid {COLORS['backgroundDarkColor']}",

    # ComboBox
    "comboBoxBorder": "1px solid white",
    "resultImageViewComboBoxWidth": "100px",

    # QDoubleSpinBox
    "doubleSpinBoxPadding": "2px 6px",

    # QCheckBox
    "checkBoxSpacing": "8px",
    "checkBoxIndicatorSize": "16px",

    # QPushButton
    "buttonFont": "bold 14px",
    "buttonBorder": "1px solid white",
    "buttonPadding": "6px",
    "buttonMargin": "6px",

    # Terminal
    "terminalBorder": "1px solid grey",

    # Frame Line
    "datasetFrameBorder": "1px solid",
    "horizonLineBorder": f"1px solid {COLORS['backgroundSubColor']}",
    "horizonLineLightBorder": f"1px solid {COLORS['backgroundLightColor']}",
    "verticalLineBorder": f"1px solid {COLORS['backgroundSubColor']}",
    "verticalLineLightBorder": f"1px solid {COLORS['backgroundLightColor']}",

    # TabBar
    "tabBarPadding": "5px 10px 5px 10px",
    "tabBarMarginRight": "5px",
    "tabBarMinWidthForLabeling": "60px",
    "tabBarMaxWidthForLabeling": "100px",
    "tabBarMinWidthForTrainingAdvanced": "140px",
    "tabPadding": "5px",
    "tabPaddingLeft": "10px",
    "tabPaddingRight": "10px",
    "selectedBorderRadius": "4px",

    # ToolBar
    "midToolBarPadding": "5px",
    "midToolBarSpacing": "10px",

    # Slider
    "horizonSliderHeight": "5px",
    "sliderBorderRadius": "2px",
    "sliderHandleWidth": "10px",
    "sliderHandleMargin": "-5px 0",

}