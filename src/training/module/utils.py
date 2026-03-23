import io
import os
import torch
import json
import numpy as np
import distinctipy
from dataclasses import dataclass, asdict
from constants.constants import *
# distinctipy library - https://distinctipy.readthedocs.io/en/latest/about.html

from time import time
from typing import Union
from collections import Counter
from sklearn.metrics import confusion_matrix
from datetime import datetime

from utils.encrypt import AesEncryption

from spectral import spy_colors

import warnings
warnings.filterwarnings('ignore')

class PrinterManager(object):
    def __init__(self, save_path, shared_data):
        self.save_path = save_path
        self.shared_data = shared_data
        self.message_buffer = [] # for display
        self.message_buffer_ = [] # for log
        self.writer = open(os.path.join(save_path, "training.log"), "a", encoding="utf-8")

    def print(self, message, color="#ffffff", font_size="10pt", font_weight="normal", append=False, save_only=False, overwrite_current_line=False):
        time = datetime.now().strftime('%Y-%m-%d-%H:%M')
        
        if not save_only:
            self.message_buffer.append(f"<span style='color:{color}; font-size:{font_size}; font-weight:{font_weight}'>{message}</span>")
            if not append:
                self.shared_data.put(
                    {"status_text":
                        f"<pre>" \
                            f"{time} > " \
                            f"{''.join(self.message_buffer)}" \
                        "</pre>",
                        "overwrite_current_line": overwrite_current_line
                    }
                )
                self.message_buffer = []
        
        self.message_buffer_.append(message)
        if not append and self.save_path:
            self.writer.write(f"{time} > {''.join(self.message_buffer_)}" + "\n")
            # with open(os.path.join(self.save_path, "training.log"), "a", encoding="utf-8") as f:
                # f.write(f"{time} > {''.join(self.message_buffer_)}" + "\n")
            self.message_buffer_ = []
    
    def __del__(self):
        self.writer.close()

class ProgressManager(object):
    def __init__(self, update_size, total_iter_size, shared_data):
        self.current_iter = 0
        self.total_iter_size = total_iter_size
        self.update_size = update_size
        self.shared_data = shared_data
    
    def init(self):
        # first entree point
        self.global_time = time()

    def step(self, overwrite=None):
        # count iteration
        if overwrite:
            self.current_iter = overwrite
        else:
            self.current_iter += 1 # first value
        
        # start from 1 to last iteration        
        if self.current_iter % self.update_size == 0:
            ticK_time = time() - self.global_time
            self.shared_data.put({"status_time": int(ticK_time * ((self.total_iter_size - self.current_iter) / self.update_size))})
            # self.run_signal.emit()
            self.global_time = time()
        self.shared_data.put({"status_progress": int((self.current_iter / self.total_iter_size) * 100)})
        # self.run_signal.emit()

@torch.jit._script_if_tracing
def save_model(model, save_path, num_bands, patch_size, batch_size, device="cpu", metaData=None) -> bool:
    model.eval()
    with torch.no_grad():
        """
            Set dummy input shape based on patch_size for model tracing.

            Modified by Chansik Kim 2025.09.08
            
            History:
             - Modified by Hyunsu Kim : Add metadata with model saving (2025.10.16)
        """
        # dummy tensor
        dummy_shape = (batch_size, num_bands, patch_size, patch_size) if patch_size >= 2 else (batch_size, num_bands) 
        dummy = [torch.rand(dummy_shape).to(device)]

        # binarization & metaData 저장 (extra_files)
        buffer = io.BytesIO()
        scriptModel = torch.jit.trace(model, dummy)
        extra_files = {}
        if metaData is not None:
            extra_files['metaData.json'] = json.dumps(metaData, ensure_ascii=False)
        torch.jit.save(scriptModel, buffer, _extra_files=extra_files)

        # encrypt & save
        AesEncryption().make_fire(buffer.getvalue(), save_path, _type="model")
        
@torch.jit._script_if_tracing
def load_model(load_path, device="cuda:0"):
    # decrypt & load
    """
        Load the TorchScript model onto the specified device.

        Args:
            load_path (str): Path to the TorchScript model file.
            device (str): Device to load the model onto. Default is 'cuda:0'.

        Modified by Chansik Kim 2025.09.08

        History:
         - Modified by Hyunsu Kim : Load metadata with model loading (2025.10.16)
    """
    extra_files = {'metaData.json': ''}
    model = torch.jit.load(AesEncryption().make_water(load_path, _type="model"), map_location=device, _extra_files=extra_files)
    metaData = None
    if extra_files['metaData.json']:
        metaData = json.loads(extra_files['metaData.json'])
        return model, metaData
    else:
        return model

def load_config():
    pass

def get_threshold_from_log(model_path) -> Union[float, None]:
    log_path = os.path.join(model_path, "training.log")
    if not os.path.exists(log_path):
        return None

    with open(log_path, 'r', encoding="utf-8") as f:
        lines = f.readlines()

    for line in reversed(lines):
        if 'Best Threshold' in line:
            threshold_value = float(line.split('Best Threshold:')[-1].strip())
            return threshold_value
    return None

def cat_tensor(array_tensor):
    return torch.cat(array_tensor, dim=0).numpy() if array_tensor else np.array([])

def get_scores(preds, labels, eps=1e-9) -> list:
    results = []
    preds = preds.reshape([-1])
    labels = labels.reshape([-1])
    unique_labels = np.unique(labels)

    cm = confusion_matrix(labels, preds, labels=unique_labels)
    recall = {label: recall for label, recall in zip(unique_labels, np.diag(cm)/(np.sum(cm, axis=1)+eps))}
    precision = {label: precision for label, precision in zip(unique_labels, np.diag(cm)/(np.sum(cm, axis=0)+eps))}
    F1scores = {label: f1score for label, f1score in zip(unique_labels, 2.0*np.diag(cm)/(np.sum(cm, axis=0)+np.sum(cm, axis=1)+eps))}

    n_data = Counter(labels)
    if len(unique_labels) == 2:
        results.append(f"Confusion Matrix\n{cm}")
    results.append(f"{'Label':>10}{'Num_data':>10}{'Precision':>10}{'Recall':>10}{'F1-Score':>10}")
    results.append("{0:->50}".format(""))
    [results.append(f"{i:>10}{n_data[i]:>10}{precision[i]:10.3f}{recall[i]:10.3f}{F1scores[i]:10.3f}") for i in unique_labels]

    abnormal_cm = cm[1:, :]
    if len(unique_labels) < 3 and len(abnormal_cm) != 0:
        total = np.sum(abnormal_cm)
        oa = np.trace(abnormal_cm, offset=1)/total * 100
        aa = np.mean((np.diag(abnormal_cm, k=1)/(np.sum(abnormal_cm, 1)+eps))) * 100

        results.append(f"Abnormal OA(%): {oa:.3f}")
        results.append(f"Abnormal AA(%): {aa:.3f}")
    
    # Handle edge case for single-class test data during metric calculation.
    abnormal_F1scores = []
    
    for label in unique_labels:
        if label < 3:
            continue
        abnormal_F1scores.append(F1scores[label])
    
    if abnormal_F1scores:
        mean_abnormal_F1scores = np.mean(abnormal_F1scores)
        results.append(f"Average Abnormal F1-Score: {mean_abnormal_F1scores:.3f}")

    return results, cm

def get_images(images, indices, labels, preds, save_path, model_type, test_data_path_list) -> np.ndarray:
    None if os.path.exists(save_path) else os.mkdir(save_path) # check save path

    origin_images = []
    pred_images = []
    label_images = []

    indices, x, y = np.array(indices).T
    for i in range(len(images['test'])):
        image = images["test"][i]
        _indices = np.where(indices == i)

        _preds = preds[_indices]
        _labels = labels[_indices]
        _x = x[_indices]
        _y = y[_indices]

        h, w, _ = np.shape(image)
        mask_preds = np.zeros((h, w))
        mask_labels = np.zeros((h, w))

        for j in range(len(_x)):
            x_pos = _x[j]
            y_pos = _y[j]
            mask_preds[x_pos, y_pos] = _preds[j]
            mask_labels[x_pos, y_pos] = _labels[j]
        
        origin_image = np.array(image).copy()
        pred_image = np.array(image).copy()
        label_image = np.array(image).copy()

        spyFloat = [(r/255, g/255, b/255) for (r,g,b) in spy_colors]

        for p in np.unique(_preds):
            # 0: ignored, 1: background, 2: normal
            if p not in [0, 1, 2]:
                """
                description : Generate a random color if p is larger than spy_colors size
                modified by HyunSu Kim 2025.08.26
                """
                if p >= len(spy_colors):
                    # Generate colors that do not overlap with existing spy_colors colors using the distinctipy library.
                    # It is not a refined palette like spy_colors, but it is created by optimizing the distance between colors based on visual considerations.
                    # Setting pastel_factor to 0.3 creates colors similar to the feel of spy_colors.
                    randomColors = distinctipy.get_colors(1, exclude_colors=spyFloat, pastel_factor=0.3)
                    spyFloat.append(randomColors[0])
                    color = [int(tupleIndex * 255) for tupleIndex in randomColors[0]]
                    pred_image[np.where(mask_preds == p)] = color
                    label_image[np.where(mask_labels == p)] = color           
                else:
                    colorIndex = p - 2
                    pred_image[np.where(mask_preds == p)] = spy_colors[colorIndex]
                    label_image[np.where(mask_labels == p)] = spy_colors[colorIndex]
                
        origin_images.append(origin_image)
        pred_images.append(pred_image)
        label_images.append(label_image)

    return origin_images, pred_images, label_images


def format_confusion_matrix(cm: np.ndarray, labels=None, col_width=7):
    """
    cm: numpy confusion matrix (K x K)
    labels: list or array of class ids (row/col order)
    col_width: spacing for alignment
    """
    labels = list(labels)
    K = len(labels)

    # 1) Pred header
    pred_header = " " * 7 + "Pred →"
    col_header  = " " * 7 + "".join(f"{lbl:>{col_width}}" for lbl in labels)

    # 2) separator line
    sep = "GT ↓  |" + "-" * (col_width * K + 2)

    # 3) rows
    rows = []
    for i, lbl in enumerate(labels):
        row_vals = "".join(f"{cm[i, j]:{col_width}d}" for j in range(K))
        rows.append(f"{lbl:>6}| {row_vals}")

    return "\n" + pred_header + "\n" + col_header + "\n" + sep + "\n" + "\n".join(rows)

def makeMetadata(config, num_bands, classifier, batch_size, patch_size, num_classes, current_model_type, hyperparameter_shared_dict, current_model_param_dict, modelType):
    """
        @description : Collect and save model metadata for model training.
        @author : Hyunsu Kim(2026.03.10)
        @parameter :
            config : dict (configuration information for model training)
            num_bands : int (number of input bands)
            classifier : bool (whether the model is a classifier)
            batch_size : int (batch size for model training)
            patch_size : int (patch size for model training)
            num_classes : int (number of classes for classification model)
            current_model_type : str (current model type - DN, SC, PD, DA, PE)
            hyperparameter_shared_dict : dict (shared hyperparameters for model training)
            current_model_param_dict : dict (current model parameters for model training)
            modelType : str (model type - AD or CLS or AD_CLS)
    """
    metadatas = {}
    metadatas["config"] = config
    wavelengths = [float(w) for w in metadatas["config"]["metaData"]['wavelength']]
    metadatas["cameraInfo"] = 'fx17' if any(w > 1000 for w in wavelengths) else 'fx10'
    metadatas["num_bands"] = num_bands
    metadatas["classifier"] = classifier
    metadatas["batch_size"] = batch_size
    metadatas["patch_size"] = patch_size
    metadatas["num_classes"] = num_classes
    metadatas["current_model_type"] = current_model_type
    metadatas["hyperparameter_shared_dict"] = hyperparameter_shared_dict
    metadatas["current_model_param_dict"] = current_model_param_dict
    metadatas["modelType"] = modelType
    metadatas["datasetScore"] = [0.0, 0.0]
    metadatas["classScore"] = {}
    return metadatas

@dataclass
class modelMetadata:
    """
        @description : Set metadata for train model using dataclass.
        @author : Hyunsu Kim (2026.03.03)
        @parameter :
            inputShape : list (height, channel)
            inputType : str (data type of input - float32)
            outputShape : list (height, ) or (height, num_classes)
            outputType : str (data type of output - float32)
            patchSize : int (DA/PE: 1, DN/SC/PD: patch size)
            lineShape : int (batch size - 512)
            channelsFirst : bool (True)
            model : dict
            data : dict
            metaData : dict

    """

    @dataclass
    class modelInfo:
        """
            @description : Set model information for metadata.
            @author : Hyunsu Kim (2026.03.03)
            @parameter :
                modelName : list (DN, SC, PD, DA, PE)
                modelDescription : list (model description for user reference)
                modelType : list (AD or CLS or AD_CLS)
        """
        modelName: str
        modelDescription: str
        modelType: str

    @dataclass
    class classInfo:
        """
            @description : Set class information for metadata.
            @author : Hyunsu Kim (2026.03.03)
            @parameter :
                    type : str (binary or classification)
                    Info : list (class labels for classification model)
        """
        type: str
        Info: dict

    @dataclass
    class dataInfo:
        """
            @description : Set data information for metadata.
            @author : Hyunsu Kim (2026.03.03)
            @parameter :
                    cameraInfo : str (camera information - fx10 or fx17)
                    calibrationType : str (calibration type - min/max)
                    calibrationRate : float (calibration rate for data normalization)
                    inputChannel : int (number of input channels - 224)
                    waverange : list (min and max wavelength of the data)
                    spectralBinning : int (spectral binning factor - 1)
                    spatialBinning : int (spatial binning factor - 1)
                    classInfo : dict
        """
        cameraInfo: str
        calibrationType: str
        calibrationRate: float
        inputChannel: int
        waverange: list
        spectralBinning: int
        spatialBinning: int
        classInfo: "modelMetadata.classInfo"

    @dataclass
    class runtimeMeta:
        """
            @description : Set gpu, CUDA, version, and other information for metadata.
            @author : Hyunsu Kim (2026.03.03)
            @parameter :
                dateTime : str (training date and time)
                generatedBy : str (training environment - local or server)
                trainGpu : str (GPU used for training)
                useGpu : bool (whether GPU was used for training)
                gpuDeviceNum : int (GPU device number used for training)
                gpuCapability : str (GPU capability)
                CUDAVersion : str (CUDA version used for training)
                torchVersion : str (PyTorch version used for training)
                elroikitVersion : str (ElroiKit version used for training)
        """
        dateTime: str
        generatedBy: str
        trainGpu: str
        useGpu: bool
        gpuDeviceNum: int
        gpuCapability: str
        CUDAVersion: str
        torchVersion: str
        elroikitVersion: str

    inputShape: list
    inputType: list
    outputShape: list
    outputType: list
    patchSize: int
    lineShape: int
    channelsFirst: bool
    model: modelInfo
    data: dataInfo
    metaData: runtimeMeta

    @classmethod
    def setMetadata(self, metaData):
        """
            @description : Set metadata for model training.
            @author : Hyunsu Kim (2026.03.03)
            @parameter :
                metaData : dict (metadata information for model training)
                    - config : dict (configuration information for model training)
                return : modelMetadata instance with all metadata information
            @history :
                - Modified by Hyunsu Kim (2026.03.10): Add metadata collection and setting for model training
        """
        wavelengths = [float(w) for w in metaData["config"]["metaData"]['wavelength']]
        waverange = [min(wavelengths), max(wavelengths)]
        channelsFirst = True
        dateTime = datetime.now().strftime('%Y-%m-%d-%H-%M')
        torchVersion = torch.__version__.split('+')[0]
        binning = 1 if metaData["cameraInfo"] == 'fx10' else 0
        classInfoType = "binary" if not metaData["classifier"] else "classification"

        if metaData["patch_size"] >= 2:
            inputShape = [metaData["config"]["dataInputHeight"], metaData["num_bands"], metaData["patch_size"], metaData["patch_size"]]
        else:
            inputShape = [metaData["config"]["dataInputHeight"], metaData["num_bands"]]
        
        inputType = "torch." + str(metaData["config"]["dataType"])
        outputShape = [metaData["config"]["dataInputHeight"]]
        if metaData["classifier"]:
            outputShape = [[metaData["config"]["dataInputHeight"], metaData["num_classes"]], [metaData["config"]["dataInputHeight"]]]
        outputType = "torch." + str(metaData["config"]["dataType"])
        lineShape = metaData["config"]["dataInputHeight"]

        modelInfo = self.modelInfo(
            modelName=[MI_STRING, metaData["current_model_type"]],
            modelDescription=[MI_STRING, metaData["hyperparameter_shared_dict"]['modelDescription']],
            modelType=[MI_STRING, metaData["modelType"]]
        )
        
        classInfo = self.classInfo(
            type=[MI_STRING, classInfoType],
            Info=[MI_STRING_ARRAY, metaData["config"]["labelData"]],
        )

        dataInfo = self.dataInfo(
            cameraInfo=[MI_STRING, metaData["cameraInfo"]],
            calibrationType=[MI_STRING, "min/max"],
            calibrationRate=[MI_FLOAT, str(metaData["current_model_param_dict"]["loader"]["calibration_rate"]["value"])],
            inputChannel=[MI_INT, str(metaData["num_bands"])],
            waverange=[MI_FLOAT_ARRAY, str(waverange)],
            spectralBinning=[MI_INT, str(binning)],
            spatialBinning=[MI_INT, str(binning)],
            classInfo=classInfo,
        )

        runtimeMeta = self.runtimeMeta(
            dateTime=[MI_STRING, dateTime],
            generatedBy=[MI_STRING, "local"],
            trainGpu=[MI_STRING, metaData["config"]["cudaInfo"]['deviceName']],
            useGpu=[MI_BOOL, str(metaData["config"]["cudaInfo"]['useCuda'])],
            gpuDeviceNum=[MI_INT, str(metaData["config"]["cudaInfo"]['cudaDevice'])],
            gpuCapability=[MI_STRING, metaData["config"]["cudaInfo"]['cudaCapability']],
            CUDAVersion=[MI_STRING, metaData["config"]["cudaInfo"]['CUDAVersion']],
            torchVersion=[MI_STRING, torchVersion],
            elroikitVersion=[MI_STRING, metaData["config"]["elroikitVersion"]],
        )

        return self(
            inputShape=[MI_INT_ARRAY, str(inputShape)],
            inputType=[MI_FLOAT, inputType],
            outputShape=[
                MI_INT_ARRAY_TUPLE if metaData["classifier"] else MI_INT_ARRAY,
                str(outputShape),
            ],
            outputType=[MI_FLOAT, outputType],
            patchSize=[MI_INT, str(metaData["patch_size"])],
            lineShape=[MI_INT, str(lineShape)],
            channelsFirst=[MI_BOOL, str(channelsFirst)],
            model=modelInfo,
            data=dataInfo,
            metaData=runtimeMeta,
        )

    # -------------------------
    # Export Method
    # -------------------------

    def to_dict(self):
        """
            @description : Convert modelMetadata instance to dictionary for JSON serialization.
            @author : Hyunsu Kim (2026.03.03)
        """
        return asdict(self)

@torch.inference_mode()
def makeFeatureDistanceHist(model, dataLoader, bestThreshold, device, bins = 80):
    """
        @description : Compute feature distance histograms for normal and abnormal samples based on the model's output distances to the center C
        @author : Hyunsu Kim (2026.03.10)
        @parameter:
                model: The trained model used for inference
                dataLoader: DataLoader for the train, test dataset
                bestThreshold: The threshold value is used to determine how the model divides the boundaries between normal and abnormal.
                device: The device to perform inference on (e.g., "cuda:0" or "cpu")
                bins: The number of bins to use for the histogram (default is 80)
    """
    model.eval()

    allDist = []
    allAbnormality = []

    # Iterate through the dataLoader and compute distances to center C for each sample, along with their corresponding abnormality labels
    for dataInput, _, abnormality, _ in dataLoader:
        dataInput = dataInput.to(device)
        abnormality = abnormality.to(device)

        # distance to center C
        dist = model(dataInput)
        if type(dist) == tuple: # PE model case
            dist = torch.sum((dist[0] - model.c) ** 2, dim=1)

        allDist.append(dist.detach().cpu().numpy())
        allAbnormality.append(abnormality.detach().cpu().numpy())

    allScores = np.concatenate(allDist)
    allAbn = np.concatenate(allAbnormality)

    allEvalMask = (allAbn != DATA_IGNORED)

    allLabelBinary = np.where(allAbn == -1, DATA_NORMAL, np.where(allAbn == 1, DATA_ABNORMAL, DATA_IGNORED))
    allLabelsWithoutIgnored = allLabelBinary[allEvalMask]

    def _make_hist(normalVals, abnormalVals, bins):
        """
            @description : Make Histograms using normal and abnormal data
            @author : Hyunsu Kim
            @parameter:
                - normalVals: The distance values for normal samples
                - abnormalVals: The distance values for abnormal samples
            @history:
                - Modified by Hyunsu Kim (2026.03.19) : 
                    - Modified to generate histograms and set bin sizes based on normalVals only when values ​​exist in normalVals and abnormalVals.
        """
        normalVals = np.asarray(normalVals, dtype=np.float32)
        abnormalVals = np.asarray(abnormalVals, dtype=np.float32)

        if normalVals.size:
            normalVals = normalVals[np.isfinite(normalVals)]
        if abnormalVals.size:
            abnormalVals = abnormalVals[np.isfinite(abnormalVals)]

        vMin = float(np.min(normalVals)) if normalVals.size else float(np.min(abnormalVals))
        vMax = float(np.max(abnormalVals)) if abnormalVals.size else float(np.max(normalVals))

        edges = np.linspace(vMin, vMax, bins + 1, dtype=np.float32)

        normalHist = None
        abnormalHist = None
        if normalVals.size:
            normalHist, _ = np.histogram(normalVals, bins=edges, density=False)
        if abnormalVals.size:
            abnormalHist, _ = np.histogram(abnormalVals, bins=edges, density=False)
        
        return {"edges": edges, "normal": normalHist, "abnormal": abnormalHist, "normalCount": normalVals.size, "abnormalCount": abnormalVals.size}

    # Filter out ignored samples and compute Scores for making histogram and getting fp/fn pixels based on the best threshold
    allScoresWithoutIgnored = allScores[allEvalMask]

    allNormalScores = allScoresWithoutIgnored[allLabelsWithoutIgnored == DATA_NORMAL]
    allAbnormalScores = allScoresWithoutIgnored[allLabelsWithoutIgnored == DATA_ABNORMAL]

    featureHist = _make_hist(allNormalScores, allAbnormalScores, bins)
    if isinstance(featureHist, dict):
        featureHist["best_thr"] = float(bestThreshold)
        featureHist["normalMean"] = np.mean(allNormalScores)
        featureHist["normalStd"] = np.std(allNormalScores)
        featureHist["abnormalMean"] = np.mean(allAbnormalScores)
        featureHist["abnormalStd"] = np.std(allAbnormalScores)

    return featureHist