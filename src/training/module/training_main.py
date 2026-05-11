import os
import sys
import datetime
import traceback
import datetime
import random
import torch
import numpy as np
from shutil import copyfile
from torch.utils.data import DataLoader
from .utils import PrinterManager, AesEncryption
from utils.shared import shared_root_path, config_path
from .Dataset import HSIDataset, get_data, load_metaData, load_labelData
from .trainer.PD import T_PLSDA
from .trainer.CLS import T_CLS
from .trainer.DA import T_DSAD
from .trainer.PE import T_PA2E_DSAD
# To import the parent module
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
import version

# def script_method(fn, _rcb=None):
#     return fn
# torch.jit.script_method = script_method

def start(is_train, dataset_shared_dict, hyperparameter_shared_dict, shared_data):
    # unpack hyperparameter shared dictionary
    current_model_type = hyperparameter_shared_dict["current_model_type"]
    current_model_settings_dict = hyperparameter_shared_dict[current_model_type]
    current_model_name = current_model_settings_dict["model_name"]
    current_model_params_dict = current_model_settings_dict["params_dict"]
    current_model_use_cuda = current_model_settings_dict["use_cuda"]
    current_model_cuda_supported = current_model_settings_dict["cuda_supported"]
    current_model_cuda_device = current_model_settings_dict["cuda_device"]
    current_model_cuda_device_name = hyperparameter_shared_dict["deviceName"]
    current_model_save_path = current_model_settings_dict["save_path"]
    current_model_load_path = current_model_settings_dict["load_path"]
    current_model_load_ref_path = current_model_settings_dict["load_ref_path"]
    current_model_use_load_ref_path = current_model_settings_dict["use_load_ref"]

    # Save path
    current_model_save_path = os.path.join(current_model_save_path, f"{current_model_type.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}")
    temp_save_path = current_model_save_path
    path_num = 1
    while os.path.exists(temp_save_path):
        temp_save_path = f"{current_model_save_path}({path_num})" # if has same name at same time
        path_num += 1
    current_model_save_path = temp_save_path
    os.mkdir(current_model_save_path)
    copyfile(config_path, os.path.join(current_model_save_path, "config.json")) # copy config file to workspace
    shared_data.put({"save_path": current_model_save_path})

    # Logger
    _printer = PrinterManager(current_model_save_path, shared_data)

    # Seed
    seed = current_model_params_dict["loader"]["seed"]["value"]
    if seed != -1:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        # Set random seed for reproducibility
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
    else:
        torch.backends.cudnn.deterministic = False
    torch.backends.cuda.matmul.allow_tf32 = True   # allow TF32 acceleration while keeping FP32 tensors
    
    # Workers
    # fixed num workers to 0 until reorganized
    num_workers = 0# current_model_params_dict["loader"]["num_workers"]["value"]
    # if num_workers != 0:
    #     torch.multiprocessing.set_sharing_strategy("file_system")
    
    # Device
    if current_model_use_cuda and current_model_cuda_supported:
        device = torch.device(f"cuda:{current_model_cuda_device}" if torch.cuda.is_available() else torch.device("cpu"))
        deviceComputeCapability = torch.cuda.get_device_capability(device)
    else:
        device = torch.device("cpu")

    cudaInfo = {"useCuda": current_model_use_cuda, "deviceName": current_model_cuda_device_name, "cudaDevice": current_model_cuda_device, "cudaCapability": f"{deviceComputeCapability[0]}.{deviceComputeCapability[1]}" if current_model_use_cuda and current_model_cuda_supported and torch.cuda.is_available() else (0.0), "CUDAVersion" : torch.version.cuda if torch.cuda.is_available() else "N/A"}
    try:
        # dataset
        # training - verbose 1,2 > (train, val, test)
        #          - verbose 0 > (train)
        # test - verbose 1,2 > (test)
        #      - verbose 0 > (train)
        # path dict
        data_path_dict = {}    
        num_classes = 2
        num_bands = 0
        dataInputHeight = 0
        dataType = None
        # verbose = current_model_params_dict["loader"]["verbose"]["value"]
        if is_train:
            # Train
            data_path_dict["train"] = []
            _printer.print("[Training Data Path]", color="#39FF33", font_weight="bold")
            for path in dataset_shared_dict["train"].keys():
                prop = dataset_shared_dict["train"][path][1]
                if dataset_shared_dict["train"][path][0] and prop > 0: # is use? and is greater than 0?
                    data_path_dict["train"].append([path, prop])
                    _printer.print(f"{len(data_path_dict['train'])}. {path} > {prop*100:.2f}%")
            # Val
            if current_model_name != "PLSDA": # PLSDA does not use validation dataset
                data_path_dict["val"] = []
                _printer.print("[Validation Data Path]", color="#39FF33", font_weight="bold")
                for path in dataset_shared_dict["val"].keys():
                    prop = dataset_shared_dict["val"][path][1]
                    if dataset_shared_dict["val"][path][0] and prop > 0: # is use? and is greater than 0?
                        data_path_dict["val"].append([path, prop])
                        _printer.print(f"{len(data_path_dict['val'])}. {path} > {prop*100:.2f}%")

        if current_model_use_load_ref_path:
            calibration_path = current_model_load_ref_path
        else:
            calibration_path = None

        # Data
        datas, labels, images = get_data(data_path_dict, current_model_params_dict, calibration_path)

        # Load metadata and label data
        metaData = None
        labelData = None
        if is_train:
            pathSample = list(dataset_shared_dict["train"].keys())[0]
            metaData = load_metaData(pathSample)

            labelData = load_labelData(data_path_dict)

        # PLSDA has no patch_size and batch_size parameters, these parameters will be used implictly
        patch_size = current_model_params_dict["loader"]["patch_size"]["value"]
        batch_size = current_model_params_dict["loader"]["batch_size"]["value"]
        ignored = current_model_params_dict["loader"]["ignored"]["value"]
        binary = current_model_params_dict["loader"]["binary"]["value"]

        # for DSAD Joint Classifier
        if "classifier" in current_model_settings_dict["params_dict"]["main_trainer"]:
            binary = not current_model_settings_dict["params_dict"]["main_trainer"]["classifier"]["value"]
        if "train" in datas:
            dataInputHeight = np.shape(datas["train"][0])[1]
            dataType = datas["train"][0].dtype
            num_bands = np.shape(datas["train"][0])[-1]
        if not binary and "train" in labels:
            num_classes = int(np.max([np.max(label) for label in labels["train"]]) + 1)

        # Data Loaders
        loader_dict = {"train": None, "val": None}
        for k in data_path_dict.keys():
            # dataset
            dataset = HSIDataset(datas=datas[k], labels=labels[k], patch_size=patch_size, binary=binary, ignored=ignored, dataset_type=k)
            
            # loader
            loader_dict[k] = DataLoader(
                dataset=dataset, batch_size=batch_size, shuffle=True if k == "train" else False, drop_last=True if k == "train" else False, num_workers=num_workers)
            
            # Display number of datas
            if k == "train":
                _printer.print(f"Train samples: {len(dataset)}")
            elif k == "val":
                _printer.print(f"Validation samples: {len(dataset)}")
        
        # Display Hyperparameters
        for k in current_model_params_dict.keys():
            current_model_param_name = current_model_params_dict[k]['name']
            # Skip displaying training-related parameters when in test mode
            if (not is_train and "train" in current_model_param_name):
                continue
            _printer.print(f"[{current_model_param_name}]", color="#FFA500", font_weight="bold")
            for _k in current_model_params_dict[k].keys():
                if "value" in current_model_params_dict[k][_k]:
                    _printer.print(f" - {current_model_params_dict[k][_k]['name']}: {current_model_params_dict[k][_k]['value']}")

        # train
        config = {
        "is_train": is_train,
        "device": device,
        "num_bands": num_bands,
        "num_classes": num_classes,
        "binary": binary,
        "images": images,
        "loader_dict": loader_dict,
        "current_model_save_path": current_model_save_path,
        "current_model_load_path": current_model_load_path,
        "current_model_param_dict": current_model_params_dict,
        "data_path_dict": data_path_dict,
        "hyperparameter_shared_dict": hyperparameter_shared_dict,
        "shared_data": shared_data,
        "_printer": _printer,
        "cudaInfo": cudaInfo,
        "metaData": metaData,
        "labelData": labelData,
        "dataInputHeight": dataInputHeight,
        "dataType": dataType,
        "elroikitVersion": f"{version.major}.{version.minor}.{version.patch}"
        }

        if is_train:
            # Trainer
            trainer = get_trainer(config, current_model_name)
            trainer.train()

        if not dataset_shared_dict["test"]: return

        # Test
        data_path_dict = {}
        data_path_dict["test"] = []
        _printer.print("[Test Data Path]", color="#39FF33", font_weight="bold")
        for path in dataset_shared_dict["test"].keys():
            prop = dataset_shared_dict["test"][path][1]
            if dataset_shared_dict["test"][path][0] and prop > 0: # is use? and is greater than 0?
                data_path_dict["test"].append([path, prop])
                _printer.print(f"{len(data_path_dict['test'])}. {path} > {prop*100:.2f}%")

        config["data_path_dict"] = data_path_dict
        datas, labels, images = get_data(data_path_dict, current_model_params_dict, calibration_path)
        config["images"] = images
        dataset = HSIDataset(datas=datas["test"], labels=labels["test"], patch_size=patch_size, binary=binary, ignored=ignored, dataset_type="test")
        test_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False, drop_last=False, num_workers=num_workers)
        # Set test loader and is_train variable
        config["loader_dict"]["test"] = test_loader
        config["is_train"] = False
        _printer.print(f"Test samples: {len(dataset)}")

        if num_bands == 0 and "test" in datas:
            config["num_bands"] = np.shape(datas["test"][0])[-1]
        if not binary and "test" in labels:
            config["num_classes"] = int(np.max([np.max(label) for label in labels["test"]]) + 1)
        trainer = get_trainer(config, current_model_name)
        if is_train:
            trainer.load(os.path.join(trainer.current_model_save_path, f"{trainer.current_model_type.replace(' ', '_')}.el"))
        else:
            trainer.load(config["current_model_load_path"])
        trainer.test(val=False, data_loader=test_loader)

    except Exception as e:
        _printer.print(f"{type(e).__name__}: {e}\n{''.join(traceback.TracebackException.from_exception(e).format())}", color="#ff0000")
        AesEncryption().make_fire(f"{type(e).__name__}: {e}\n{''.join(traceback.TracebackException.from_exception(e).format())}", f"{shared_root_path}\\{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.log", "Elroilab")
        # shared_data.put({"runtime_error": True})
        shared_data.put({"runtime_error": str(e)})
        _printer.print(f"{type(e).__name__}: at line {e.__traceback__.tb_frame} of {__file__}: {e}", color="#ff0000")


def get_trainer(config:dict, current_model_name:str):
    if current_model_name == "PLSDA":
        trainer = T_PLSDA(config)
    elif current_model_name == "DDCNN" or current_model_name == "SSGCA":
        trainer = T_CLS(config)
    elif current_model_name == "DSAD":
        trainer = T_DSAD(config)
    elif current_model_name == "PA2Ev2":
        trainer = T_PA2E_DSAD(config)
    else:
        raise Exception('Invalid model name.')
    return trainer
