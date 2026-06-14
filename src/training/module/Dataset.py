"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
            - dataList(list): merged data that is used for train, valid, and test
            - labelList(list): ground truth
            - patch_size(int): the size of patched HSI
            - binary(bool): the bool for binarized label(0: ignored, 1: normal, 2: abnormal)
            - ignored(list): the list of ignored label
            - p(int): the half of patch size
            - indices_list(list): list of the indices of ground truth
            - length(int): the length of pixels in ground truth to predict
            - dataset_type(str): the type of dataset(train, val, test)
    """
    def __init__(self, dataList, labelList, patch_size, binary:bool=False, ignored:list=[0], dataset_type:str="train"):
        super(Dataset, self).__init__()
        assert patch_size > 0
        # Convert numpy arrays to tensors without copying data using from_numpy method
        # Modified by Chansik Kim (2025.03.21)
        self.dataList = [torch.from_numpy(data) for data in dataList]
        self.labelList = labelList
        self.patch_size = patch_size

        self.p = self.patch_size // 2
        self.indices_list = []
        self.length = 0
        self.dataset_type = dataset_type

        #Make ignored label 
        if any(num != 0 for num in ignored) and self.dataset_type in ["train", "val"]:
            for i in range(len(self.labelList)):
                self.labelList[i] = np.where(np.isin(self.labelList[i], ignored), 0, self.labelList[i])

        #AD option make [1,2] class to 2 and others(w/o 0) to 3
        if binary:
            for i in range(len(self.labelList)):
                self.labelList[i] = np.where(self.labelList[i] == 1, 2, np.where(self.labelList[i] >= 3, 3, self.labelList[i]))

        #Make pixel indices list
        for i, label in enumerate(self.labelList):
            h, w, _ = dataList[i].shape
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
        self.labelList = [torch.from_numpy(label).type(torch.LongTensor) for label in labelList]

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
                data = self.dataList[i][c_x, c_y]
            else:
                ul_x, ul_y = c_x - self.p, c_y - self.p # Upper left x, y 
                br_x, br_y = ul_x + self.patch_size, ul_y + self.patch_size # Bottom right x, y
                data = self.dataList[i][ul_x:br_x, ul_y:br_y,:]
                data = data.permute(2, 0, 1)
            
            # Make label
            label = self.labelList[i][c_x, c_y]

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
            3. Hyunsu Kim (2026.04.17):
                - add exception handling for data loading failure and return None when loading fails to allow graceful error handling in the calling function
    """
    file_name, ext = os.path.splitext(name)
    if ext == ".npy": # label data
        data = np.load(os.path.join(data_path, name))
        if np.unique(data).size == 1 and np.unique(data)[0] == 0:
            raise ValueError(f"Warning: Loaded label data from {os.path.join(data_path, name)} contains only ignored labels (0). Please check if the label file is correctly placed and formatted.")
    elif ext == ".raw": # HSI data
        try:
            fullPath = os.path.join(data_path, file_name)
            data = np.array(spectral.io.envi.open(fullPath + ".hdr", fullPath + ".raw").load())
            hdrData = spectral.io.envi.read_envi_header(fullPath + ".hdr")
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
        except:
            print("Error loading HSI data. Please check if the data files are in ENVI format and the calibration files are correctly placed if calibration is enabled.")
            data = None
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

def load_labelData(dataPathDict):
    """
    description: load label data from dataPathDict
    author : Hyunsu Kim (2025.10.16)
    History :
        1. Hyunsu Kim (2026.03.03):
            - add if condition to check if data.json file exists to avoid error when data.json file is missing in some data paths
    """
    labelData = {}
    for k in dataPathDict.keys():
        for fullPath, _ in dataPathDict[k]:
            temp = load_data(fullPath, "data.json")
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


def loadDataset(fullPath, calibration, calibrationRate, calibrationPath, loadTestImage):
    """
    description: load dataset from fullPath
    author : Hyunsu Kim (2026.04.07)
    """
    data = load_data(
        fullPath,
        "data.raw",
        calibration=calibration,
        calibration_rate=calibrationRate,
        calibration_path=calibrationPath,
    )
    label = load_data(fullPath, "label.npy") if os.path.isfile(os.path.join(fullPath, "label.npy")) else None
    image = HSI(fullPath).get_image(rgb=True, calibration=True) if loadTestImage else {}
    return fullPath, data, label, image

"""
description: split dataList each by task of proportion
author : HyeokYoon

@History
    1. modified by HyeokYoon (20240220)
    2. Modified to perform train/val split on the background (label 1) as well. Chansik Kim (2025.03.21)

recently works
- add normal checking for utilizing abnormal labels in hyperspectral images
"""
def get_data(dataPathDict, currentParamsDict, calibrationPath, workers):    
    """
    @History
        1. Modified to avoid duplicated loading of data, label files. Hyunsu Kim (2025.09.10)
        2. Modified to add thread-based parallel loading of data and label files to speed up the loading process. Hyunsu Kim (2026.04.07)
        3. Modified to stop loading immediately when any loaded result is an None. Hyunsu Kim (2026.04.17)
    """
    dataList = {}
    labelList = {}
    imageList = {}
    for k in dataPathDict.keys():
        dataList[k] = []
        labelList[k] = []
        imageList[k] = []

    uniquePaths = {}
    for k in dataPathDict.keys():
        for fullPath, _ in dataPathDict[k]:
            if k == "val" and fullPath in uniquePaths.keys():
                continue
            else:
                uniquePaths.setdefault(fullPath, False)
                uniquePaths[fullPath] = uniquePaths[fullPath] or (k == "test")

    calibration = currentParamsDict["loader"]["calibration"]["value"]
    calibrationRate = currentParamsDict["loader"]["calibration_rate"]["value"]
    loadedDataList = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                loadDataset,
                fullPath,
                calibration,
                calibrationRate,
                calibrationPath,
                loadTestImage,
            ): fullPath
            for fullPath, loadTestImage in uniquePaths.items()
        }
        for future in as_completed(futures):
            fullPath, data, label, image = future.result()
            if any(item is None for item in (data, label, image)):
                raise ValueError(f"Failed to load dataset from {fullPath}")
            
            loadedDataList[fullPath] = {"data": data, "label": label, "image": image}
    
    # TODO
    # select files name in settings
    for k in dataPathDict.keys():
        has_normal_total = False # check for normal inclusion in overall label
        has_abnormal_total = False # check for abnormal inclusion in overall label
        for fullPath, prop in dataPathDict[k]:
            has_normal_label = False # check for normal inclusion in label
            prop = float(prop)
            assert 0 < prop <= 1
            data = loadedDataList[fullPath]["data"]
            dataList[k].append(data)
            # Enable model testing without requiring a label file
            label = loadedDataList[fullPath]["label"]
            if label is not None:
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
                label = np.zeros(data.shape[:2])
            labelList[k].append(label)
            # Store images only for test set to save memory during training
            if k == "test":
                image = loadedDataList[fullPath]["image"]
                imageList[k].append(image)
        # raise exception when label not include normal
        if k != "test":
            if not has_normal_total:
                raise ValueError(f"Normal label not included")
            if not has_abnormal_total:
                raise ValueError(f"Abnormal label not included")

    return dataList, labelList, imageList

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
