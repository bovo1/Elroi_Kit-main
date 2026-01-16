"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

hyperparameter_dict = {
    "loader": {
        "name": "loader",
        "calibration": {
            "name": "Calibration",
            "value": True,
            "type": bool,
            "disabled": False,
            "visible": False
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
        "batch_size": {
            "name": "Batch Size",
            "value": 512,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": True
        },
        "normalization":{
            "name": "Normalization",
            "value": False,
            "type": bool,
            "disabled": False,
            "visible": False
        },
        "binary": {
            "name": "Binary",
            "value": True,
            "type": bool,
            "disabled": False,
            "visible": False
        },
        "ignored": {
            "name": "Ignored Label",
            "value": [0],
            "type": list,
            "regex": "\d{1,2}([,]\d{1,2})*",
            "editable": True,
            "disabled": False,
            "visible": False
        },
        "patch_size": {
            "name": "Patch Size",
            "value": 1,
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
            "value": 50,
            "type": int,
            "regex": "[1-9][0-9][0-9]",
            "disabled": False,
            "visible": True
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
        "save_best_model_only": {
            "name": "Save Best Model Only",
            "value": False,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "val_interval": {
            "name": "Validation Interval",
            "value": 1,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": False
        },
        "early_stop": {
            "name": "Early Stopping",
            "value": True,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "early_stopping_patience": {
            "name": "Early Stopping Patience(epochs)",
            "value": 40,
            "type": int,
            "regex": "[0-9]+",
            "disabled": False,
            "visible": True
        },
        "model_selection": {
            "name": "Model Selection Metric",
            "data": ["AUPR", "Val Loss"],
            "value": 0,
            "type": list,
            "editable": False,
            "disabled": False,
            "visible": False
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
        "scheduler": {
            "name": "Scheduler",
            "data": ["Not use", "Cosine"],
            "value": 1,
            "type": list,
            "editable": False,
            "disabled": False,
            "visible": False
        },
        "classifier": {
            "name": "Classifier",
            "value": False,
            "type": bool,
            "disabled": False,
            "visible": True
        },
        "beta": {
            "name": "Beta(AD/Classification Loss Balance)",
            "value": 0.05,
            "type": float,
            "regex": "([0-9]*[.])?[0-9]+([eE][-+]?\d+)?",
            "scientific_notation": False,
            "disabled": False,
            "visible": True,
            "none_zero": True,
            "none_zero_value": 0.05
        },
        "num_layers": {
            "name": "Number of Layers",
            "value": 5,
            "type": int,
            "regex": "[1-9]",
            "disabled": False,
            "visible": False
        },
        "rep_dims": {
            "name": "Representation Dimensions",
            "value": 64,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": False
        }
    },
    "ae_trainer": {
        "name": "sub_da_trainer",
        "epochs": {
            "name": "Epochs",
            "value": 50,
            "type": int,
            "regex": "[0-9][0-9][0-9]",
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
            "visible": False
        }
    }
}