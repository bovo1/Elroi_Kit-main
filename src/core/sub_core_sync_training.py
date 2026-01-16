import os
import json
from PyQt5 import QtCore

from utils.shared import config_path
class Sub_Core_Sync_Training(QtCore.QObject):
    # dataset_main -> run_main, result_main
    dataset_shared_dict = {}
    dataset_signal = QtCore.pyqtSignal(dict)
    metadata_shared_dict = {}

    # hyperparameter_main -> run_main, result_main
    hyperparameter_shared_dict = {}
    hyperparameter_signal = QtCore.pyqtSignal(dict)
    
    # run_main -> result_main
    # model_type(str): current trained model type (model 1, model 2...)
    # save_path(str): current save path
    # origin_img(np.ndarray): original test image
    # pred_img(np.ndarray): prediction map
    # pred_score(np.ndarray): prediction score (only for DSAD)
    # threshold_visible(bool): on/off threshold visivility (only for DSAD)
    # threhold(float): last best threshold (only for DSAD)
    # train_loss(list): training loss
    # val_loss(list): validation loss
    # test_loss(list): test loss
    # init(bool): initilize
    result_signal = QtCore.pyqtSignal(dict)
    statusbar_signal = QtCore.pyqtSignal(str)

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.loads(f.read())
        except:
            config = {"datasets": {}, "hyperparameters": {}}
    else:
        config = {"datasets": {}, "hyperparameters": {}}


    def __init__(self, core_obj_dict):
        super().__init__()
        self.core_obj_dict = core_obj_dict