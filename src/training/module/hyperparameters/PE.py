"""
    ELROILAB Kit
 
    Copyright 2025. Elroilab All rights reserved.
"""

"""
    description: hyperparameter UI Widget for PA2Ev2
    author : Chansik Kim 2025.02.26
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
            "visible": False
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
        "model_selection": {
            "name": "Model Selection Metric",
            "data": ["AUPR", "LOSS"],
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
        "num_layers": {
            "name": "Number of Layers(Default: 3)",
            "value": 3,
            "type": int,
            "regex": "[1-9]",
            "disabled": False,
            "visible": True
        },
        "rep_dims": {
            "name": "Rep Dimensions(Default: 32)",
            "value": 32,
            "type": int,
            "regex": "[1-9][0-9]+",
            "disabled": False,
            "visible": True
        },
        "num_agg_layers": {
            "name": "Number of Agg layers(Default: 3)",
            "value": 3,
            "type": int,
            "regex": "[1-9]",
            "disabled": False,
            "visible": True
        },
        "window_size": {
            "name": "Window Size(Default: 56)",
            "value": 56,
            "type": int,
            "regex": "[1-9][0-9]?",
            "disabled": False,
            "visible": True
        },
        "window_stride": {
            "name": "Window Stride(Default: 14)",
            "value": 14,
            "type": int,
            "regex": "[1-9][0-9]?",
            "disabled": False,
            "visible": True
        },
        "window_rep_dims": {
            "name": "Window Rep Dims(Default: 28)",
            "value": 28,
            "type": int,
            "regex": "[1-9][0-9]?",
            "disabled": False,
            "visible": True
        },
        "factor": {
            "name": "Factor(Default: 1.0)",
            "value": 1.0,
            "type": float,
            "regex": "([0]*[.])?([0-9])?",
            "scientific_notation": True,
            "disabled": False,
            "visible": False,
            "none_zero": True,
            "none_zero_value": 0.1
        },
        "alpha": {
            "name": "Alpha(Default: 1.0)",
            "value": 1.0,
            "type": float,
            "regex": "([0]*[.])?([0-9])?",
            "scientific_notation": True,
            "disabled": False,
            "visible": False,
            "none_zero": True,
            "none_zero_value": 0.1
        },
        "layer_fusion": {
            "name": "Layer Fusion(Default: True)",
            "value": True,
            "type": bool,
            "disabled": False,
            "visible": False,
        },
        "act_verbose": {
            "name": "Activation Verbose(Default: [0, 0, 1, 1])",
            "value": [0, 0, 1, 1],
            "type": list[bool],
            "regex": "([0]*[.])?([0-9])?",
            "disabled": False,
            "visible": False,
        },
        "dropout_rate": {
            "name": "Dropout Rate(Default: 0.0)",
            "value": 0.0,
            "type": float,
            "regex": "([0]*[.])?([0-9])?",
            "disabled": False,
            "visible": False,
        },
    },
    "pa2e_trainer": {
        "name": "sub_pa2e_trainer",
        "epochs": {
            "name": "Epochs",
            "value": 20,
            "type": int,
            "regex": "[0-9][0-9][0-9]",
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
        "val_offset": {
            "name": "Validation Offset For Pretraining(Default: 20)",
            "value": 20,
            "type": int,
            "regex": "[0-9][0-9][0-9]",
            "disabled": False,
            "visible": False
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