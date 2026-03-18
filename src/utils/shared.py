import os
import sys

if hasattr(sys, '_MEIPASS'):
    resource_path = os.path.join(sys._MEIPASS, 'rsrc')
    icon_path = os.path.join(sys._MEIPASS, 'ico')
    font_path = os.path.join(sys._MEIPASS, 'font')
else:
    resource_path = os.path.join(os.path.abspath("."), 'rsrc')
    icon_path = os.path.join(os.path.abspath("."), 'ico')
    font_path = os.path.join(os.path.abspath("."), 'font')
main_key = "elroilab" # main key for encryption
shared_root_path = "C:\\ProgramData\\ElroiKit" # shared path (workspace)
license_path = "C:\\ProgramData\\ElroiKit\\license" # license path
license_txt_path = os.path.join(resource_path, "license.txt")
temp_path = f"C:\\Users\\{os.getlogin()}\\Documents\\ElroiKit" # temp path (labeling, training)
config_path = f"{os.path.join(shared_root_path)}\\config.json" # config path
settings_path = f"{os.path.join(shared_root_path)}\\settings.json" # settings path
background_image_path = os.path.join(icon_path, "labeling\\logo\\background.jpg")
video_path = os.path.join(resource_path, f"videos\\training.gif") # video path
