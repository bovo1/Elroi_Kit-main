"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

hyperparameter_dict = {
    "loader": {
        "name": "loader",
        "seed": {
            "name": "Sampling Seed",
            "value": -1,
            "type": int,
            "regex": "([-][1])|[0-9]+",
            "disabled": False,
            "visible": True
        },
        "num_workers": {
            "name": "Number of Workers",
            "value": 0,
            "type": int,
            "regex": "[0-9]+",
            "disabled": True,
            "visible": False
        },
        "calibration": {
            "name": "Calibration",
            "value": True,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "calibration_rate": {
            "name": "Calibration Rate",
            "value": 1.0,
            "type": float,
            "regex": "([0]*[.])?([0-9])?",
            "scientific_notation": True,
            "disabled": False,
            "visible": True,
            "none_zero": True,
            "none_zero_value": 0.1
        },
        "normalization":{
            "name": "Normalization",
            "value": False,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "binary": {
            "name": "Binary",
            "value": False,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "ignored": {
            "name": "Ignored Label",
            "value": [0],
            "type": list,
            "regex": "\d{1,2}([,]\d{1,2})*",
            "editable": True,
            "disabled": False,
            "visible": True
        },
        "patch_size": {
            "name": "Patch Size",
            "value": 5,
            "type": int,
            "regex": "[5-9][0-9]+",
            "disabled": False,
            "visible": True
        },
        "batch_size": {
            "name": "Batch Size",
            "value": 512,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": True
        },
    },
    "main_trainer": {
        "name": "main_trainer",
        "epochs": {
            "name": "Epochs",
            "value": 200,
            "type": int,
            "regex": "[1-9][0-9][0-9]",
            "disabled": False,
            "visible": True
        },
        "dropout": {
            "name": "Dropout",
            "value": 0.1,
            "type": float,
            "regex": "([0-9]*[.])?[0-9]+([eE][-+]?\d+)?",
            "disabled": False,
            "visible": True,
            "none_zero": False,
            "none_zero_value": 0.0
        },
        "val_interval": {
            "name": "Validation Interval",
            "value": 1,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": True
        },
        "save_best_model_only": {
            "name": "Save Best Model Only",
            "value": False,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "early_stop": {
            "name": "Early Stop",
            "value": True,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "early_stopping_patience": {
            "name": "Early Stopping Patience",
            "value": 40,
            "type": int,
            "regex": "[0-9]+",
            "disabled": False,
            "visible": True
        },
        "optimizer": {
            "name": "Optimizer",
            "data": ["AdamW", "Adam"],
            "value": 0,
            "type": list,
            "editable": False,
            "disabled": False,
            "visible": True
        },
        "loss_function": {
            "name": "Loss Function",
            "data": ["Cross Entropy"],
            "value": 0,
            "type": list,
            "editable": False,
            "disabled": False,
            "visible": True
        },
        "weight_decay": {
            "name": "Weight Decay",
            "value": 0.0,
            "type": float,
            "regex": "([0-9]*[.])?[0-9]+([eE][-+]?\d+)?",
            "scientific_notation": True,
            "disabled": False,
            "visible": True,
            "none_zero": False,
            "none_zero_value": 0.0
        },
        "learning_rate": {
            "name": "Learning Rate",
            "value": 0.001,
            "type": float,
            "regex": "([0-9]*[.])?[0-9]+([eE][-+]?\d+)?",
            "scientific_notation": True,
            "disabled": False,
            "visible": True,
            "none_zero": False,
            "none_zero_value": 0.0
        },
        "scheduler": {
            "name": "Scheduler",
            "data": ["Not use", "Cosine"],
            "value": 1,
            "type": list,
            "editable": False,
            "disabled": False,
            "visible": True
        }
    }
}