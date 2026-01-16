"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

import datetime
import os
import json
import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from time import time
from sklearn.metrics import precision_recall_curve, average_precision_score, accuracy_score, f1_score
from constants.constants import *
from ..models.Module import AutoEncoder
from ..models.DA import DSAD, CDSAD
from ..utils import ProgressManager, load_model, get_scores, get_images, get_threshold_from_log, save_model, format_confusion_matrix


"""
description: training module for anomaly detection task
author : HyeokYoon
modified by HyeokYoon (20240219)

recently works
- removed verbose option and related parameters
"""
class T_DSAD():
    def __init__(self, config):
        # Common Configuration
        self.is_train = config["is_train"]
        self.device = config["device"]
        self.num_bands = config["num_bands"]
        self.num_classes = config["num_classes"]
        self.images = config["images"]
        self.current_model_load_path = config["current_model_load_path"]
        self.current_model_save_path = config["current_model_save_path"]
        self.current_model_param_dict = config["current_model_param_dict"]
        self.hyperparameter_shared_dict = config["hyperparameter_shared_dict"]
        self.data_path_dict = config["data_path_dict"]
        self.shared_data = config["shared_data"]
        self._printer = config["_printer"]
        if self.is_train:
            self.cudaInfo = config["cudaInfo"]
            self.metaData = config["metaData"]
            self.labelData = config["labelData"]
            self.elroikitVersion = config["elroikitVersion"]
            wavelengths = [float(w) for w in self.metaData['wavelength']]
            self.cameraInfo = 'fx17' if any(float(w) > 1000 for w in wavelengths) else 'fx10'
            self.waverange = [min(wavelengths), max(wavelengths)]
            self.channelsFirst = True
            self.fx17InputHeight = 640

        self.current_model_type = config["hyperparameter_shared_dict"]["current_model_type"]
        current_model_settings_dict = config["hyperparameter_shared_dict"][self.current_model_type]

        # Model Configuration
        self.normalization = current_model_settings_dict["params_dict"]["loader"]["normalization"]["value"]
        self.batch_size = current_model_settings_dict["params_dict"]["loader"]["batch_size"]["value"]
        self.patch_size = current_model_settings_dict["params_dict"]["loader"]["patch_size"]["value"]
        self.spatial = True if self.patch_size >= 2 else False # If patch size is greater than 2, use CNN, otherwise use MLP

        self.learning_rate = current_model_settings_dict["params_dict"]["main_trainer"]["learning_rate"]["value"]
        self.weight_decay = current_model_settings_dict["params_dict"]["main_trainer"]["weight_decay"]["value"]
        self.epochs = current_model_settings_dict["params_dict"]["main_trainer"]["epochs"]["value"]
        beta = current_model_settings_dict["params_dict"]["main_trainer"]["beta"]["value"]
        self.beta_tensor = torch.tensor(beta, device=self.device, dtype=torch.float32)
        self.save_best_model_only = current_model_settings_dict["params_dict"]["main_trainer"]["save_best_model_only"]["value"]
        self.classifier = current_model_settings_dict["params_dict"]["main_trainer"]["classifier"]["value"]
        self.early_stop = current_model_settings_dict["params_dict"]["main_trainer"]["early_stop"]["value"]
        self.early_stopping_patience = current_model_settings_dict["params_dict"]["main_trainer"]["early_stopping_patience"]["value"]
        self.model_selection = current_model_settings_dict["params_dict"]["main_trainer"]["model_selection"]["value"]
        self.val_interval = current_model_settings_dict["params_dict"]["main_trainer"]["val_interval"]["value"]
        self.num_layers = current_model_settings_dict["params_dict"]["main_trainer"]["num_layers"]["value"]
        self.rep_dims = current_model_settings_dict["params_dict"]["main_trainer"]["rep_dims"]["value"]

        self.ae_epochs = current_model_settings_dict["params_dict"]["ae_trainer"]["epochs"]["value"]
        self.ae_learning_rate = current_model_settings_dict["params_dict"]["ae_trainer"]["learning_rate"]["value"]
        self.ae_weight_decay = current_model_settings_dict["params_dict"]["ae_trainer"]["weight_decay"]["value"]
        self.eps = torch.tensor(torch.finfo(torch.float32).eps, device=self.device)
        self.best_epoch = None
        self.modelMetadata = {}
        self.classScore = {}
        self.datasetScore = []

        # Loader
        self.train_loader = config["loader_dict"]["train"]
        self.val_loader = config["loader_dict"]["val"]

        self.ae_model = AutoEncoder(self.num_bands, self.num_layers, self.rep_dims, self.patch_size, CNN=self.spatial, normalization=self.normalization).to(self.device)
        if self.classifier:
            self.dsad_model = CDSAD(self.num_bands, self.num_layers, self.rep_dims, self.patch_size, CNN=self.spatial, normalization=self.normalization, num_classes=self.num_classes).to(self.device)
        else:
            self.dsad_model = DSAD(self.num_bands, self.num_layers, self.rep_dims, self.patch_size, CNN=self.spatial, normalization=self.normalization).to(self.device)

        ae_optimizer_index = current_model_settings_dict["params_dict"]["ae_trainer"]["optimizer"]["value"]
        if ae_optimizer_index == 0:
            self.ae_optimizer = torch.optim.AdamW(self.ae_model.parameters(), lr=self.ae_learning_rate, weight_decay=self.ae_weight_decay)
        elif ae_optimizer_index == 1:
            self.ae_optimizer = torch.optim.Adam(self.ae_model.parameters(), lr=self.ae_learning_rate, weight_decay=self.ae_weight_decay)
        else:
            raise Exception("Not Supported Optimizer Index")
       
        ae_scheduler_index = current_model_settings_dict["params_dict"]["ae_trainer"]["scheduler"]["value"]
        if ae_scheduler_index == 0:
            self.ae_scheduler = None
        elif ae_scheduler_index == 1:
            self.ae_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=self.ae_optimizer, T_max=self.ae_epochs)
        else:
            raise Exception("Not Supported Scheduler Index")
        
        self.ae_loss = nn.MSELoss().to(self.device)
        
        # Optimizer Selection (0: Adam)
        optimizer_index = current_model_settings_dict["params_dict"]["main_trainer"]["optimizer"]["value"]
        if optimizer_index == 0:
            self.dsad_optimizer = torch.optim.AdamW(self.dsad_model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        elif optimizer_index == 1:
            self.dsad_optimizer = torch.optim.Adam(self.dsad_model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        
        # Scheduler Selection (0: Not use, 1: Cosine)
        scheduler_index = current_model_settings_dict["params_dict"]["main_trainer"]["scheduler"]["value"]
        if scheduler_index == 0:
            self.dsad_scheduler = None
        elif scheduler_index == 1:
            self.dsad_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=self.dsad_optimizer, T_max=self.epochs)

    def train(self):
        # Progress
        self.progress_manager = ProgressManager(UPDATE_SIZE, len(self.train_loader) * self.ae_epochs + (len(self.train_loader) + len(self.val_loader)) * self.epochs, self.shared_data)
        self.progress_manager.init()

        # AE Part
        # ======================================================================================
        # AE Train
        self.ae_model.train().to(self.device)
        '''
            description: Keep fixed scalar buffers on GPU to accumulate loss statistics and avoid loss.item() calls that trigger GPU-to-CPU synchronization.
            modified by Chansik Kim 2025.12.12
        '''
        ae_loss_buf = torch.zeros((), device=self.device, dtype=torch.float32)
        ae_epoch_loss_sum = torch.zeros((), device=self.device, dtype=torch.float32)
        ae_epoch_cnt      = torch.zeros((), device=self.device, dtype=torch.float32)

        for epoch in range(1, self.ae_epochs + 1): # Epoch is starting from 1
            '''
                description: Reset epoch-level loss and count buffers at the start of each epoch to prevent cross-epoch accumulation.
                modified by Chansik Kim 2025.12.12
            '''
            ae_epoch_loss_sum.zero_()
            ae_epoch_cnt.zero_()
            for X, _, _, _ in self.train_loader:
                X = X.to(self.device)
                self.ae_optimizer.zero_grad(set_to_none=True)
                
                hypothesis = self.ae_model(X)
                loss = self.ae_loss(hypothesis, (X/4095.0))
                ae_loss_buf.copy_(loss)
                ae_epoch_loss_sum.add_(ae_loss_buf)
                ae_epoch_cnt.add_(1)
                loss.backward()
                self.ae_optimizer.step()

                # AE status printer
                self.progress_manager.step()
            mean_loss = float((ae_epoch_loss_sum / ae_epoch_cnt).item())
            if self.ae_scheduler:
                self.ae_scheduler.step()

            self._printer.print(f"(Sub {self.current_model_type}) - [Training] ", color="#33FFFF", font_weight="bold", append=True)
            self._printer.print(f"Epoch: {epoch}/{self.ae_epochs}, Loss: {mean_loss:.5f}")

        # AE Freeze
        self.ae_model.eval()
        for parameter in self.ae_model.parameters():
            parameter.requires_grad = False
        # ======================================================================================

        # DSAD Part
        # ======================================================================================
        # DSAD Train
        model_score_max = 0
        self.best_epoch = 1
        best_thr = 1.0
        early_stop_counter = 0

        # Initialize DSAD
        self.initialize_DSAD()
        self.dsad_model.train().to(self.device)
        '''
            description: Keep fixed scalar buffers on GPU to accumulate loss statistics and avoid loss.item() calls that trigger GPU-to-CPU synchronization.
            modified by Chansik Kim 2025.12.12
        '''
        self.loss_buf = torch.zeros((), device=self.device, dtype=torch.float32)
        dsad_epoch_loss_sum = torch.zeros((), device=self.device, dtype=torch.float32)
        dsad_epoch_cnt = torch.zeros((), device=self.device, dtype=torch.float32)

        for epoch in range(1, self.epochs + 1):
            is_best_model = False
            is_model_saved = False
            self.dsad_model.train()
            '''
                description: Reset epoch-level loss and count buffers at the start of each epoch to prevent cross-epoch accumulation.
                modified by Chansik Kim 2025.12.12
            '''
            dsad_epoch_loss_sum.zero_()
            dsad_epoch_cnt.zero_()
            for X, Y, abnormality, _ in self.train_loader:
                X = X.to(self.device)
                abnormality = abnormality.to(self.device)
                self.dsad_optimizer.zero_grad(set_to_none=True)

                if self.classifier:
                    Y = Y.to(self.device)
                    # abnormal_mask: mask for abnormal samples
                    abnormal_mask = (Y >= 3)
                    hypothesis, dist = self.dsad_model(X)
                    ce_per_sample = F.cross_entropy(hypothesis, Y, reduction="none")
                    # number of abnormal samples
                    ab_count = abnormal_mask.sum()  # scalar tensor
                    # safety guard for cases with no abnormal samples
                    # numerator is zero anyway, so clamp denominator to at least 1
                    ab_count_safe = torch.clamp_min(ab_count, 1.0)
                    # average CE only for abnormal samples
                    ce_loss = (ce_per_sample * abnormal_mask).sum() / ab_count_safe  # scalar
                    # ----- DSAD based dist loss -----
                    # abnormality: 1(abnormal), -1(normal)
                    dist_term = torch.where(abnormality == 1, torch.reciprocal(dist + self.eps), dist).mean()

                    loss = self.beta_tensor * ce_loss + (1 - self.beta_tensor) * dist_term
                else:
                    dist = self.dsad_model(X)
                    loss = torch.where(abnormality == 1, torch.reciprocal(dist + self.eps), dist).mean()

                self.loss_buf.copy_(loss.detach())
                dsad_epoch_loss_sum.add_(self.loss_buf)
                dsad_epoch_cnt.add_(1)
                loss.backward()
                self.dsad_optimizer.step()
                # DSAD training status printer
                self.progress_manager.step()

            '''
                description: Collect metadata information about input/output shape and type
                modified by ChanSik Kim 2025.12.12
            '''
            it = iter(self.train_loader)
            X0, _, _, _ = next(it)
            self.input_shape = list(X0.shape)
            if self.cameraInfo == "fx17":
                self.input_shape[0] = self.fx17InputHeight
            self.input_type = str(X0.dtype)
            if self.classifier:
                self.output_shape = [list(hypothesis.shape), list(dist.shape)]
                if self.cameraInfo == "fx17":
                    self.output_shape[0][0] = self.fx17InputHeight
                    self.output_shape[1][0] = self.fx17InputHeight
            else:
                self.output_shape = list(dist.shape)
                if self.cameraInfo == "fx17":
                    self.output_shape[0] = self.fx17InputHeight
            self.output_type = str(dist.dtype)
            
            mean_loss = float((dsad_epoch_loss_sum / dsad_epoch_cnt).item())    
            self.datasetScore = [0.0, 0.0]

            self._printer.print(f"(Main {self.current_model_type}) - [Training] ", color="#33FFFF", font_weight="bold", append=True)
            self._printer.print(f"Epoch: {epoch}/{self.epochs}, Loss: {mean_loss:.5f}")

            # Loss
            self.shared_data.put({"train_loss": mean_loss})
            
            if self.dsad_scheduler:
                self.dsad_scheduler.step()
                
            if epoch%self.val_interval == 0:
                test_results = self.test(True, self.val_loader, epoch, best_thr)
                best_thr = test_results["best_thr"]
                classScore = test_results["classScore"]
                '''
                    description: Weighted model selection score (AD primary, CLS secondary).
                    modified by Chansik Kim 2025.12.12
                '''
                if self.model_selection == MODEL_SELECTION_AUPR:
                    model_score = test_results["aupr"] * 0.8 + test_results["cls_macro_f1"] * 0.2 if self.classifier else test_results["aupr"]
                elif self.model_selection == MODEL_SELECTION_LOSS:
                    model_score = -test_results["loss"] * 0.8 + test_results["cls_macro_f1"] * 0.2 if self.classifier else test_results["loss"]
                if self.classifier:
                    self._printer.print(f"[Cls Model Selection] Score: {model_score:.5f}  (weights: AD=0.8, CLS=0.2)")

                if model_score > model_score_max:
                    model_score_max = model_score
                    self.best_epoch = epoch
                    is_best_model = True
                    early_stop_counter = 0
                else:
                    early_stop_counter += 1

                if self.early_stop and early_stop_counter >= self.early_stopping_patience:
                    self._printer.print(f"Training early stop, Epoch: {epoch}/{self.epochs}, Loss: {mean_loss:.5f}")
                    self.progress_manager.step(len(self.train_loader) * self.ae_epochs + (len(self.train_loader) + len(self.val_loader)) * self.epochs)
                    break

            # ============= MetaData =============
            dateTime = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
            torchVersion = torch.__version__.split('+')[0]
            binning = 1 if self.cameraInfo == 'fx10' else 0
            classInfoType = "binary" if not self.classifier else "classification"

            self.modelMetadata = {
                "inputShape" : [MI_INT_ARRAY, str(self.input_shape)], # input shape - list [512, 224]
                "inputType" : [MI_FLOAT, str(self.input_type)], # input type - torch.float32
                "outputShape" : [MI_INT_ARRAY_TUPLE if self.classifier else MI_INT_ARRAY, str(self.output_shape)], # output shape - list [512]
                "outputType" : [MI_FLOAT, str(self.output_type)], # output type - torch.float32
                "patchSize" : [MI_INT, str(self.patch_size)], # patch size - 1
                "lineShape" : [MI_INT, str(self.batch_size)], # line shape - 512
                "channelsFirst" : [MI_BOOL, str(self.channelsFirst)], # channels first - True
                "model" : {
                    "modelName" : [MI_STRING, self.current_model_type], # model name - DA
                    "modelDescription" : [MI_STRING, self.hyperparameter_shared_dict['modelDescription']],
                    "modelType" : [MI_STRING, self.dsad_model.modelType], # model type - AD or CLS
                    "bestThreshold" : [MI_FLOAT, str(best_thr)],
                    "classScore" : [MI_FLOAT_ARRAY, classScore], # mean and std score for each class
                    "datasetScore" : [MI_FLOAT_ARRAY, self.datasetScore] # mean and std score for dataset
                },
                "data" : {
                    "cameraInfo" : [MI_STRING, self.cameraInfo], # camera info - fx10 or fx17
                    "calibrationType" : [MI_STRING, "min/max"],
                    "calibrationRate" : [MI_FLOAT, str(self.current_model_param_dict["loader"]["calibration_rate"]["value"])], # calibration rate - 1.0
                    "inputChannel" : [MI_INT, str(self.num_bands)], # input channel - 224
                    "waverange" : [MI_FLOAT_ARRAY, str(self.waverange)], # waverange - [400.67, 997.99]
                    "spectralBinning" : [MI_INT, str(binning)],
                    "spatialBinning" : [MI_INT, str(binning)],
                    "classInfo" : {
                        "type" : [MI_STRING, classInfoType],
                        "Info" : [MI_STRING_ARRAY, self.labelData] # class info - '0' : {'label_name': "플라스틱_검정", 'label_color': '[61, 238, 220]'}
                    }
                },
                "metaData" : {
                    "dateTime" : [MI_STRING, dateTime],
                    "generatedBy" : [MI_STRING, "local"],
                    "trainGpu" : [MI_STRING, self.cudaInfo['deviceName']], # gpu name - NVIDIA GeForce RTX 4070 Laptop GPU
                    "useGpu" : [MI_BOOL, str(self.cudaInfo['useCuda'])], # use gpu - True
                    "gpuDeviceNum" : [MI_INT, str(self.cudaInfo['cudaDevice'])], # gpu device number - 0
                    "gpuCapability" : [MI_STRING, self.cudaInfo['cudaCapability']], # gpu capability - 8.9
                    "CUDAVersion" : [MI_STRING, self.cudaInfo['CUDAVersion']], # cuda version - 12.6
                    "torchVersion" : [MI_STRING, torchVersion], # torch version - 2.6.0
                    "elroikitVersion" : [MI_STRING, self.elroikitVersion]}, # elroikit version - 1.7.2
            }

            # Save
            # Only transmit metadata when it's the best model
            if is_best_model:
                self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}.el"), self.modelMetadata)
                is_model_saved = True

            if not self.save_best_model_only:
                self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}_{epoch}.el"), self.modelMetadata)
                is_model_saved = True

            if is_model_saved:
                self._printer.print(f"Model has been saved in {self.current_model_save_path}")

        self._printer.print(f"Best Epoch: {self.best_epoch}/{self.epochs}")

    @torch.inference_mode()
    def test(self, val=True, data_loader=None, epoch=None, best_thr=1.0) -> dict:
        indices = []
        preds_cls = []
        preds_softmax = []
        scores = []
        scores_without_ignored = []
        labels_multi = []
        labels_binary = []
        labels_without_ignored = []
        time_list = []
        results = []
        cm = []

        # Default metrics containers (avoid UnboundLocalError on edge cases)
        results_ad, cm_ad = [], []
        results_cls, cm_cls = [], []

        mean_loss = 0.0
        aupr = 0.0
        best_thr = best_thr
        trained_cls_list = None

        # GPU accumulation buffers
        all_dist_gpu = []
        all_abn_gpu  = []
        all_valid_cls_mask_gpu = []
        all_preds_cls_gpu = []
        all_preds_softmax_gpu = []
        all_labels_multi_gpu = []
        trained_cls_tensor = None
        loss_sum_gpu = torch.zeros((), device=self.device, dtype=torch.float32)
        loss_cnt_gpu = torch.zeros((), device=self.device, dtype=torch.float32)
        self.dsad_model.eval()
        def extract_trained_ids(label_dict: dict) -> list[int]:
            ids = sorted(int(k) for k in label_dict.keys())
            trained = [i for i in ids if i >= 3]
            return trained
        # Progress
        if not val:
            self.progress_manager = ProgressManager(UPDATE_SIZE, len(data_loader), self.shared_data)
            self.progress_manager.init()
            '''
                description: Extract list of trained abnormal classes from model metadata for selective loss calculation.
                modified by Chansik Kim 2025.12.16
            '''
            if len(self.modelMetadata) != 0:
                try:
                    if (self.modelMetadata["data"]["classInfo"]["type"][-1] == "classification"):
                        trained_cls_list = self.modelMetadata["data"]["classInfo"]["Info"][-1]
                        trained_cls_list = extract_trained_ids(trained_cls_list) # e.g. [3,4,24,25,26,27,28,29]
                except Exception as e:
                    trained_cls_list = []
                    self._printer.print(f"Error extracting trained classes from model metadata: {e}")
        else:
            if self.classifier:
                # During validation, always extract trained classes from labelData
                trained_cls_list = extract_trained_ids(self.labelData)

        if self.classifier and trained_cls_list is not None and len(trained_cls_list) > 0:
            trained_cls_tensor = torch.tensor(trained_cls_list, device=self.device, dtype=torch.long)

        for X, Y, abnormality, pos in data_loader:
            X = X.to(self.device)
            abnormality = abnormality.to(self.device)
            if self.classifier:
                Y = Y.to(self.device)
                b_start = time()
                hypothesis, dist = self.dsad_model(X)
                time_list.append(time() - b_start)

                '''
                    description: For classes that have not been trained, exclude them from loss calculation
                    modified by Chansik Kim 2025.12.16
                '''
                C = hypothesis.size(1) # number of classes
                # no trained classes
                if trained_cls_tensor is None:
                    valid_cls_mask = torch.zeros_like(Y, dtype=torch.bool)
                else:
                    # Valid abnormal labels that are within model output range and in trained set
                    valid_cls_mask = ((Y >= 3) & (Y < C) & torch.isin(Y, trained_cls_tensor))
                # exclude 0/1/2 + trained classes
                Y2 = Y.clone()
                Y2[~valid_cls_mask] = -100  # ignore_index
                ce_per_sample = F.cross_entropy(hypothesis, Y2, ignore_index=-100, reduction="none")

                # Number of abnormal samples
                ab_count = valid_cls_mask.sum()  # scalar tensor
                # Safety guard for when there are no abnormal samples
                # The numerator is zero anyway, so clamp the denominator to at least 1
                ab_count_safe = torch.clamp_min(ab_count, 1.0)
                # Calculate the average cross-entropy loss only for abnormal samples
                ce_loss = (ce_per_sample * valid_cls_mask).sum() / ab_count_safe  # scalar
                # ----- DSAD dist based loss -----
                # abnormality: 1(abnormal), -1(normal)
                dist_term = torch.where(abnormality == 1, torch.reciprocal(dist + self.eps), dist).mean()

                loss = self.beta_tensor * ce_loss + (1 - self.beta_tensor) * dist_term

                # Accumulate predictions/labels on GPU
                all_valid_cls_mask_gpu.append(valid_cls_mask.detach())
                all_preds_cls_gpu.append(torch.argmax(hypothesis, 1).detach())
                all_preds_softmax_gpu.append(torch.softmax(hypothesis, -1).detach())
                all_labels_multi_gpu.append(Y.detach())
            else:
                b_start = time()
                dist = self.dsad_model(X)
                time_list.append(time() - b_start)
                loss = torch.where(abnormality == 1, torch.reciprocal(dist + self.eps), dist).mean()

            # Accumulate (loss, dist, abn, indices)
            all_dist_gpu.append(dist.detach())
            all_abn_gpu.append(abnormality.detach())
            loss_sum_gpu.add_(loss.detach())
            loss_cnt_gpu.add_(1)
            pos = torch.stack(pos)
            indices.append(pos.transpose(0, 1))
            self.progress_manager.step()

        # -------------------------------
        # GPU -> CPU transfer and concatenation
        # -------------------------------
        scores = torch.cat(all_dist_gpu)
        all_abn  = torch.cat(all_abn_gpu)
        indices = torch.cat(indices)

        scores = scores.cpu().numpy()
        all_abn = all_abn.cpu().numpy()
        indices = indices.cpu().numpy()

        mean_loss = float((loss_sum_gpu / loss_cnt_gpu).item())

        # -------------------------------
        # AD evaluation mask/label composition
        # -------------------------------
        eval_mask = (all_abn != 0)                # exclude abnormality == 0 (ignored)
        scores_without_ignored = scores[eval_mask]

        if self.classifier:
            valid_cls_mask_gpu = torch.cat(all_valid_cls_mask_gpu) # exclude normal labels in addition to evaluation mask (for multi-class evaluation)
            preds_cls = torch.cat(all_preds_cls_gpu) # predicted class indices
            preds_softmax = torch.cat(all_preds_softmax_gpu) # predicted softmax probabilities
            labels_multi = torch.cat(all_labels_multi_gpu) # ground truth multi-class labels
            
            valid_cls_mask_gpu = valid_cls_mask_gpu.cpu().numpy()
            preds_cls = preds_cls.cpu().numpy()
            preds_cls_only_ab = preds_cls[valid_cls_mask_gpu]
            preds_softmax = preds_softmax.cpu().numpy()
            labels_multi = labels_multi.cpu().numpy()
            labels_multi_only_ab = labels_multi[valid_cls_mask_gpu]

        all_dist_gpu.clear()
        all_abn_gpu.clear()
        all_valid_cls_mask_gpu.clear()
        all_preds_cls_gpu.clear()
        all_preds_softmax_gpu.clear()
        all_labels_multi_gpu.clear()

        # AD ground truth labels (2: normal, 3: abnormal)
        labels_binary = np.where(all_abn == -1, 2, np.where(all_abn == 1, 3, 0))
        labels_without_ignored = labels_binary[eval_mask]

        # -------------------------------
        # Validation / Test logs
        # -------------------------------
        if val:
            self._printer.print(f"(Main {self.current_model_type}) - [Validation] ", color="#F4FA58", font_weight="bold", append=True)
            self._printer.print(f"Epoch: {epoch}/{self.epochs}, Loss: {mean_loss:.5f}")
        else:
            self._printer.print(f"(Main {self.current_model_type}) - [Testing] ", color="#CE33FF", font_weight="bold", append=False)
            self._printer.print(f"Mean Loss: {mean_loss:.5f}")

        num_labels_without_ignored = len(np.unique(labels_without_ignored))
        has_only_ignored_label = (num_labels_without_ignored == 0)

        # -------------------------------
        # AD AUPR / Best threshold calculation
        # -------------------------------
        if not has_only_ignored_label and num_labels_without_ignored > 1:
            precision, recall, thresholds = precision_recall_curve(
                labels_without_ignored - 2,   # 0: normal, 1: abnormal
                scores_without_ignored
            )
            aupr = average_precision_score(labels_without_ignored - 2, scores_without_ignored)
            f1scores = 2. * (precision * recall) / (precision + recall + self.eps.cpu().numpy())
            # precision/recall are length N+1, thresholds are length N. Use f1scores[:-1] to match thresholds.
            if thresholds.size > 0:
                best_thr = thresholds[int(np.argmax(f1scores[:-1]))]
        # -------------------------------
        # AD predictions
        # -------------------------------
        preds_ad_without_ignored = np.where(scores_without_ignored < best_thr, 2, 3)
        preds_ad_with_ignored   = np.where(scores < best_thr, 2, 3)
        # ----- Visualization label/pred separation -----
        if self.classifier:
            # Multi-class GT (0: ignore, 1/2: normal, 3+ abnormal classes)
            vis_labels = labels_multi

            # Class argmax results (already obtained as preds_cls from GPU→CPU transfer)
            vis_preds = preds_cls.copy()

            # Force positions predicted as normal by AD to 2 (normal)
            vis_preds[preds_ad_with_ignored == 2] = 2
        else:
            # AD binary result-based visualization
            vis_labels = labels_binary          # 0/2/3 structure
            vis_preds  = preds_ad_with_ignored  # 2/3 structure

        # -------------------------------
        # AD overall metrics (existing structure)
        # -------------------------------
        if num_labels_without_ignored > 0:
            results_ad, cm_ad = get_scores(preds_ad_without_ignored, labels_without_ignored, self.eps.cpu().numpy())
        else: # edge case: all labels are ignored
            results_ad, cm_ad = [], []

        # Classification overall metrics
        if self.classifier:
            # only abnormal samples
            if labels_multi_only_ab is not None and len(labels_multi_only_ab) > 0:
                results_cls, cm_cls = get_scores(preds_cls_only_ab, labels_multi_only_ab, self.eps.cpu().numpy())
            # edge case: all labels are ignored
            else:
                results_cls, cm_cls = [], []
        self._printer.print("Anomaly Detection Results")

        mean_inf_time = time_list[0] if len(time_list) == 1 else np.mean(time_list[:-1])

        # Class-wise score statistics (AD)
        for c in np.unique(labels_without_ignored):
            score = scores_without_ignored[np.where(labels_without_ignored == c)]
            self._printer.print(f"Class {str(c)}: Score N(mean={np.mean(score):.5f}, std={np.std(score):.5f})")
            self.classScore[str(c)] = [float(np.mean(score)), float(np.std(score))]
        if aupr:
            self._printer.print(f"[AD] AUPR: {aupr:.5f}")
        self._printer.print(f"[AD] Best Threshold: {best_thr:.5f}")

        # ======================================================
        #  Multi-class Classification Metrics (classifier=True)
        # ======================================================
        # Classification metrics initialization
        cls_macro_f1 = None
        cls_acc = None
        cls_metric_skip_reason = None

        if self.classifier:
            self._printer.print("Classification Results (for Abnormal Samples Only)")

            # Derive class dimension from logits
            C = int(preds_softmax.shape[1]) if isinstance(preds_softmax, np.ndarray) else 0

            # Determine whether GT labels are available (e.g., test set may be unlabeled)
            has_gt_labels = (labels_multi is not None) and (labels_multi.size > 0) and np.any(labels_multi >= 0)

            # Prepare trained eval class list (only abnormal labels, within [0, C))
            trained_eval_classes = []
            if trained_cls_list is not None:
                trained_eval_classes = sorted({int(c) for c in trained_cls_list if int(c) >= 3 and int(c) < C})

            # GT labels exist?
            if not has_gt_labels:
                cls_metric_skip_reason = "NO_GT_LABELS"
            # Model provides trained class info?
            elif trained_cls_list is None:
                cls_metric_skip_reason = "NO_MODEL_INFO"
            elif len(trained_cls_list) == 0:
                cls_metric_skip_reason = "EMPTY_TRAINED_CLASS_LIST"
            # Model provides trained class info?
            elif len(trained_eval_classes) == 0:
                cls_metric_skip_reason = "NO_EVAL_CLASSES_IN_RANGE"
            else:
                # valid_cls_mask_gpu already excludes non-trained / out-of-range labels
                cls_eval_mask = valid_cls_mask_gpu.astype(bool)
                y_true_cls = labels_multi[cls_eval_mask]

                # Gate 4: any GT samples belong to trained classes?
                if y_true_cls.size == 0:
                    cls_metric_skip_reason = "NO_VALID_GT_SAMPLES_FOR_TRAINED_CLASSES"
                else:
                    # Use trained classes only for argmax to avoid metric distortion
                    logits_valid = preds_softmax[:, trained_eval_classes]  # (N, K)
                    preds_cls_valid = np.array(trained_eval_classes, dtype=np.int64)[np.argmax(logits_valid, axis=1)]
                    y_pred_cls = preds_cls_valid[cls_eval_mask]

                    cls_acc = accuracy_score(y_true_cls, y_pred_cls)
                    cls_macro_f1 = f1_score(y_true_cls, y_pred_cls, average="macro")

                    self._printer.print(f"[CLS] #Eval Samples: {y_true_cls.size}")
                    self._printer.print(f"[CLS] Accuracy: {cls_acc:.5f}")
                    self._printer.print(f"[CLS] Macro F1: {cls_macro_f1:.5f}")

            # Log skipped metric reason if applicable
            if cls_metric_skip_reason is not None:
                # trained_cls_list (from model metadata)
                trained_abnormal_classes = None
                if trained_cls_list is not None and len(trained_cls_list) > 0:
                    trained_abnormal_classes = sorted(
                        int(c) for c in trained_cls_list if 3 <= int(c) < C
                    )

                # val or test set GT labels
                present_abnormal_labels_in_eval = None
                if has_gt_labels and labels_multi is not None and labels_multi.size > 0:
                    present_abnormal_labels_in_eval = sorted(
                        int(x)
                        for x in np.unique(labels_multi)
                        if 3 <= int(x) < C
                    )

                self._printer.print(
                    f"[CLS] Metric skipped: {cls_metric_skip_reason} | "
                    f"trained_abnormal_classes={trained_abnormal_classes} | "
                    f"present_abnormal_labels_in_eval={present_abnormal_labels_in_eval}"
                )


        self._printer.print(f"Average Batch Inference Time: {mean_inf_time*1000:.3f}ms")

        # ============= Result (existing shared_data handling) =============
        if not val:
            for result in results_ad:
                self._printer.print(result)

            if self.classifier:
                results = results_cls
                cm = cm_cls
                if results_cls:
                    self._printer.print("Confusion Matrix (only abnormal samples)")
                    cm_text = format_confusion_matrix(cm_cls, labels=np.unique(labels_multi_only_ab))
                    self._printer.print(cm_text)
                    for result in results_cls:
                        self._printer.print(result)
                
            else:
                results = results_ad
                cm = cm_ad

            origin_images, pred_images, label_images = self.visualization(indices, vis_labels, vis_preds)
            self.shared_data.put({"results": results})
            self.shared_data.put({"cm": cm})
            self.shared_data.put({"origin_images": origin_images})
            self.shared_data.put({"pred_images": pred_images})
            self.shared_data.put({"label_images": label_images})
            self.shared_data.put({"best_threshold": best_thr})
            self.shared_data.put({"abnormal_scores": scores})
            self.shared_data.put({"position_indices": indices})
            if self.classifier:
                self.shared_data.put({"is_classification": None})
            else:
                self.shared_data.put({"is_anomaly_detection": None})
            self.progress_manager.step()
        else:
            results = results_cls if self.classifier else results_ad

            self.shared_data.put({"abnormal_avg_f1score": float(results[-1].split(" ")[-1])})
            self.shared_data.put({"val_loss": mean_loss})
        # ==========================================================

        return {"aupr": aupr, "loss": mean_loss, "best_thr": best_thr, "classScore": self.classScore, "cls_macro_f1": cls_macro_f1 if self.classifier else None}


    def save(self, save_path, metaData=None):
        """
            Set dummy input shape based on patch_size for model tracing.

            Modified by Chansik Kim 2025.09.08

            History:
             - Modified by Hyunsu Kim : Transmit metadata (2025.10.16)
        """
        save_model(self.dsad_model, save_path, self.num_bands, self.patch_size, self.batch_size, self.device, metaData)

    def load(self, load_path: str) -> None:
        """
        Args:
            load_path (str): Path to the TorchScript model file.
            device (str): Device to load the model onto. Default is 'cuda:0'.

        History:
         - Modified by Chansik Kim : Loads the DSAD model directly from a TorchScript file using torch.jit.load (2025.05.21)
         - Modified by Chansik Kim : Load the TorchScript model onto the specified device (2025.09.08)
         - Modified by Hyunsu Kim : Load metadata with model loading (2025.10.16)
        """
        self.dsad_model, self.modelMetadata = load_model(load_path, self.device)

    def initialize_DSAD(self):
        self.dsad_model.encoder.load_state_dict(self.ae_model.encoder.state_dict())

        # C
        c = torch.zeros(self.dsad_model.rep_dim, device=self.device)
        c_size = 0

        self.ae_model.eval()
        with torch.no_grad():
            for X, _, abnormality, _ in self.train_loader:
                X = X[torch.where(abnormality == -1)].to(self.device)
                c_size += X.size(0)
                c += torch.sum(self.ae_model.encoder(X), dim=0).detach()
        c /= c_size

        c[(abs(c) < 0.1) & (c < 0)] = -0.1
        c[(abs(c) < 0.1) & (c > 0)] = 0.1
        self.dsad_model.c.data.copy_(c)  # Copy new_c to dsad_model.c

    def visualization(self, indices, labels, preds):
        # Use the predict image for classification task
        origin_images, pred_images, label_images = get_images(self.images, indices, labels, preds, os.path.join(self.current_model_save_path), f"{self.current_model_type.replace(' ', '_')}", list(zip(*self.data_path_dict["test"]))[0])
        return origin_images, pred_images, label_images
