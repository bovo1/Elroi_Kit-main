"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

import os
import torch
import numpy as np
import spectral
import json

from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split

from utils.tools import HSI
from constants.constants import AGGREGATION_DATA

class HSIDataset(Dataset):
    """
        HSI dataset. This is used in data loader.
        Attributes
            - datas(list): merged data that is used for train, valid, and test
            - labels(list): ground truth
            - patch_size(int): the size of patched HSI
            - binary(bool): the bool for binarized label(0: ignored, 1: normal, 2: abnormal)
            - ignored(list): the list of ignored label
            - p(int): the half of patch size
            - indices_list(list): list of the indices of ground truth
            - length(int): the length of pixels in ground truth to predict
            - dataset_type(str): the type of dataset(train, val, test)
    """
    def __init__(self, datas, labels, patch_size, binary:bool=False, ignored:list=[0], dataset_type:str="train"):
        super(Dataset, self).__init__()
        assert patch_size > 0
        # Convert numpy arrays to tensors without copying data using from_numpy method
        # Modified by Chansik Kim (2025.03.21)
        self.datas = [torch.from_numpy(data) for data in datas]
        self.labels = labels
        self.patch_size = patch_size

        self.p = self.patch_size // 2
        self.indices_list = []
        self.length = 0
        self.dataset_type = dataset_type

        #Make ignored label 
        if any(num != 0 for num in ignored) and self.dataset_type in ["train", "val"]:
            for i in range(len(self.labels)):
                self.labels[i] = np.where(np.isin(self.labels[i], ignored), 0, self.labels[i])

        #AD option make [1,2] class to 2 and others(w/o 0) to 3
        if binary:
            for i in range(len(self.labels)):
                self.labels[i] = np.where(self.labels[i] == 1, 2, np.where(self.labels[i] >= 3, 3, self.labels[i]))

        #Make pixel indices list
        for i, label in enumerate(self.labels):
            h, w, _ = datas[i].shape
            # Generate all pixel coordinates to perform inference on the entire image data during model testing.

            if self.dataset_type == "test":
                if self.p == 0:
                    indices = np.indices(label.shape)
                    x_pos, y_pos = indices[0].ravel(), indices[1].ravel()
                else:
                    x_pos = np.arange(self.p, h - self.p)
                    y_pos = np.arange(self.p, w - self.p)
                    x_pos, y_pos = np.meshgrid(x_pos, y_pos, indexing='ij')
                    x_pos, y_pos = x_pos.ravel(), y_pos.ravel()
            else:
                x_pos, y_pos = np.nonzero(label)
                if self.p != 0:
                    valid_indices = (self.p <= x_pos) & (x_pos < h - self.p) & (self.p <= y_pos) & (y_pos < w - self.p)
                    x_pos, y_pos = x_pos[valid_indices], y_pos[valid_indices]
            indices = np.column_stack((x_pos, y_pos))
            self.indices_list.append(indices)
            self.length += len(indices)

        # Convert to int64 type for binary cross entropy loss function input
        # Modified by Chansik Kim (2025.03.21)
        self.labels = [torch.from_numpy(label).type(torch.LongTensor) for label in labels]

    def __len__(self):
        """
            return length attributes
            Returns
                - length(int): the length of pixels in ground truth to predict
        """
        return self.length 

    def __getitem__(self, index):
        """
            return patch, label of center pixel, abnormality, indices
            Parameters
                - index(int): the index ranged from 0 to length
            Returns
                - data(torch): the patch image indexed by input
                - label(torch): the label of index
                - abnormality(int): if the label is abnormal, abnormality is -1, otherwise it is 0.
                - indices(tuple): the index of the image in data list, and position of pixel.
        """
        for i in range(len(self.indices_list)):
            length = len(self.indices_list[i])
            if index >= length: 
                index -= length 
                continue

            c_x, c_y = self.indices_list[i][index]

            if self.patch_size == 1:
                # Only accept input within the range set in the TensorRT engine
                data = self.datas[i][c_x, c_y]
            else:
                ul_x, ul_y = c_x - self.p, c_y - self.p # Upper left x, y 
                br_x, br_y = ul_x + self.patch_size, ul_y + self.patch_size # Bottom right x, y
                data = self.datas[i][ul_x:br_x, ul_y:br_y,:]
                data = data.permute(2, 0, 1)
            
            # Make label
            label = self.labels[i][c_x, c_y]

            # Make abnormality
            if label >= 3:
                abnormality = 1
            elif label == 0:
                abnormality = 0
            else: # label in [1, 2]
                abnormality = -1

            return data, label, abnormality, (i, c_x, c_y)

def load_data(data_path, name, calibration=False, calibration_rate=1.0, calibration_path=None) -> np.ndarray:
    """
        @description: load data from data_path with name
        @history:
            1. GaEun Hwang(26.01.26): 
                - add branch for data generated by label aggregation
            2. Hyunsu Kim (2026.03.03):
                - add if condition to check if data.json file exists to avoid error when data.json file is missing in some data paths
    """
    file_name, ext = os.path.splitext(name)
    if ext == ".npy": # label data
        data = np.load(os.path.join(data_path, name))
    elif ext == ".raw": # HSI data
        full_path = os.path.join(data_path, file_name)
        data = np.array(spectral.io.envi.open(full_path + ".hdr", full_path + ".raw").load())
        hdrData = spectral.io.envi.read_envi_header(full_path + ".hdr")
        if calibration:
            _calibration_path = calibration_path if calibration_path else data_path
            dark_data = np.array(spectral.io.envi.open(os.path.join(_calibration_path, "DARKREF.hdr"), os.path.join(_calibration_path, "DARKREF.raw")).load())
            darkDataHdr = spectral.io.envi.read_envi_header(os.path.join(_calibration_path, "DARKREF.hdr"))
            white_data = np.array(spectral.io.envi.open(os.path.join(_calibration_path, "WHITEREF.hdr"), os.path.join(_calibration_path, "WHITEREF.raw")).load())
            whiteDataHdr = spectral.io.envi.read_envi_header(os.path.join(_calibration_path, "WHITEREF.hdr"))
            # Add branch for data generated by label aggregation
            if hdrData.get("information") != AGGREGATION_DATA:
                if darkDataHdr.get("information") != AGGREGATION_DATA and whiteDataHdr.get("information") != AGGREGATION_DATA:
                    dark_data = dark_data.mean(0)
                    white_data = white_data.mean(0)
                else:
                    print("Reference data is aggregation data.")
            # Min-max scaling
            data = (((data-dark_data)/(white_data-dark_data))*4095.0)*calibration_rate
            data = np.array(np.clip(data, 0, 4095), dtype=np.float32)
    elif ext == ".json": # label info data
        if os.path.isfile(os.path.join(data_path, name)):
            with open(os.path.join(data_path, name), "r", encoding="UTF-8") as f:
                data = json.load(f)
                data = data['label_info']
        else:
            data = {}
    else:
        raise ValueError(f"Unkown file format: {ext}")
    return data

def load_labelData(data_path_dict):
    """
    description: load label data from data_path_dict
    author : Hyunsu Kim (2025.10.16)
    History :
        1. Hyunsu Kim (2026.03.03):
            - add if condition to check if data.json file exists to avoid error when data.json file is missing in some data paths
    """
    labelData = {}
    for k in data_path_dict.keys():
        for full_path, _ in data_path_dict[k]:
            temp = load_data(full_path, "data.json")
            if temp:
                for key, item in temp.items():
                    item["label_color"] = str(item["label_color"])
                    labelData.setdefault(key, item)
    return labelData

def load_metaData(data_path):
    """
    description: load metadata from data_path
    author : Hyunsu Kim (2025.10.16)
    """
    metaData = spectral.io.envi.read_envi_header(os.path.join(data_path, "data.hdr"))
    return metaData

"""
description: split datas each by task of proportion
author : HyeokYoon

@History
    1. modified by HyeokYoon (20240220)
    2. Modified to perform train/val split on the background (label 1) as well. Chansik Kim (2025.03.21)

recently works
- add normal checking for utilizing abnormal labels in hyperspectral images
"""
def get_data(data_path_dict, current_params_dict, calibration_path):    
    """
    @History
        1. Modified to avoid duplicated loading of data, label files. Hyunsu Kim (2025.09.10)
    """
    datas={}; labels={}; images={}
    for k in data_path_dict.keys():
        datas[k] = []
        labels[k] = []
        images[k] = []

    dataCache = {}
    labelCache = {}
    
    # TODO
    # select files name in settings
    for k in data_path_dict.keys():
        has_normal_total = False # check for normal inclusion in overall label
        has_abnormal_total = False # check for abnormal inclusion in overall label
        for full_path, prop in data_path_dict[k]:
            has_normal_label = False # check for normal inclusion in label
            prop = float(prop)
            assert 0 < prop <= 1
            # Load data with caching to avoid duplicated loading
            if full_path in dataCache:
                datas[k].append(dataCache.pop(full_path))
            else:
                dataCache[full_path] = load_data(full_path, "data.raw", calibration=current_params_dict["loader"]["calibration"]["value"], calibration_rate=current_params_dict["loader"]["calibration_rate"]["value"], calibration_path=calibration_path)
                datas[k].append(dataCache[full_path])
            # Enable model testing without requiring a label file
            is_label_file = os.path.isfile(os.path.join(full_path, "label.npy"))
            if is_label_file:
                # Load label with caching to avoid duplicated loading
                if full_path in labelCache:
                    label = labelCache.pop(full_path)
                else:
                    label = load_data(full_path, "label.npy")
                    labelCache[full_path] = label
                has_normal_label = np.any(np.isin(label, np.array([1, 2])))
                has_abnormal_label = np.any(label > 2) # check for abnormal label presence
                if prop < 1 and has_normal_label:
                    normal_label = np.where(label > 2, 0, label)
                    normal_label, _ = split_label(normal_label, ratio=prop)
                    abnormal_label = np.where(label <= 2, 0, label)
                    label = normal_label + abnormal_label
                has_normal_total = has_normal_total or has_normal_label
                has_abnormal_total = has_abnormal_total or has_abnormal_label # check for abnormal label presence
            else:
                label = np.zeros(dataCache[full_path].shape[:2])
            labels[k].append(label)
            # Store images only for test set to save memory during training
            if k == "test":
                image = HSI(full_path).get_image(rgb=True, calibration=True)
                images[k].append(image)
        # raise exception when label not include normal
        if k != "test":
            if not has_normal_total:
                raise ValueError(f"Normal label not included")
            if not has_abnormal_total:
                raise ValueError(f"Abnormal label not included")

    return datas, labels, images

def split_label(label, ratio=0.15):
    """
        Split the input ground truth with respect to the ratio by sklearn.model_selection module.
        Parameters
            - ground truth(numpy): a ground truth(numpy).
            - ratio(float): the ratio of train(first) and test(second) ground truth.
        Returns
            - train_gt(numpy): train(first) ground truth. Some components in the input ground truth are superseded by the 1-ratio.
            - test_gt(numpy): test(second) ground truth. Some components in the input ground truth are superseded by the ratio.
    """
    indices = np.nonzero(label)
    X = np.array(indices).T
    Y = label[indices].ravel()

    train_label = np.zeros_like(label)
    test_label = np.zeros_like(label)

    train_indices, test_indices = train_test_split(X, train_size=ratio, stratify=Y) 
    train_indices = tuple(train_indices.T)
    test_indices = tuple(test_indices.T)

    train_label[train_indices] = label[train_indices]
    test_label[test_indices] = label[test_indices]

    return train_label, test_label
