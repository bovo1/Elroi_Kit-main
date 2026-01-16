import io
import os
import torch
import json
import types
import numpy as np
import distinctipy
# distinctipy library - https://distinctipy.readthedocs.io/en/latest/about.html

from time import time
from typing import Union
from collections import Counter
from sklearn.metrics import confusion_matrix
from datetime import datetime

from utils.encrypt import AesEncryption

from spectral import spy_colors
from PIL import Image

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
