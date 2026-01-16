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
            "value": 1,
            "type": int,
            "regex": "[0-9]+",
            "disabled": False,
            "visible": False
        },
        "batch_size": {
            "name": "Batch Size",
            "value": 512,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": False
        },
    },
    "main_trainer": {
        "name": "main_trainer",
        "max_iter": {
            "name": "Max Iteration",
            "value": 1000,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": True
        },
        "num_lv": {
            "name": "Number of Latent Vectors",
            "value": 40,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": True
        },
        "thr": {
            "name": "Threshold",
            "value": 1e-6,
            "type": float,
            "regex": "([0-9]*[.])?[0-9]+([eE][-+]?\d+)?",
            "scientific_notation": True,
            "disabled": False,
            "visible": True,
            "none_zero": False,
            "none_zero_value": 0.0
        }
    }
}