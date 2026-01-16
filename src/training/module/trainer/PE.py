"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

import os
from time import time
import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from constants.constants import *
from utils.optimize_nn import Optimize

from ..models.PE import PA2Ev2, PA2E_model, PA_Encoder
from ..utils import ProgressManager, load_model, get_scores, get_images, get_threshold_from_log, cat_tensor, save_model

"""
description: training module for anomaly detection task
author : HyeokYoon
modified by HyeokYoon (20240219)

recently works
- removed verbose option and related parameters
"""
class T_PA2E_DSAD():
    def __init__(self, config):
        # Common Configuration
        self.is_train = config["is_train"]
        self.device = config["device"]
        self.num_bands = config["num_bands"]
        self.num_classes = config["num_classes"]
        self.images = config["images"]
        self.current_model_load_path = config["current_model_load_path"]
        self.current_model_save_path = config["current_model_save_path"]
        self.data_path_dict = config["data_path_dict"]
        self.shared_data = config["shared_data"]
        self._printer = config["_printer"]

        self.current_model_type = config["hyperparameter_shared_dict"]["current_model_type"]
        current_model_settings_dict = config["hyperparameter_shared_dict"][self.current_model_type]

        # Model Configuration
        self.normalization = current_model_settings_dict["params_dict"]["loader"]["normalization"]["value"]
        self.batch_size = current_model_settings_dict["params_dict"]["loader"]["batch_size"]["value"]
        self.patch_size = current_model_settings_dict["params_dict"]["loader"]["patch_size"]["value"]

        self.learning_rate = current_model_settings_dict["params_dict"]["main_trainer"]["learning_rate"]["value"]
        self.weight_decay = current_model_settings_dict["params_dict"]["main_trainer"]["weight_decay"]["value"]
        self.pae_epochs = current_model_settings_dict["params_dict"]["main_trainer"]["epochs"]["value"]
        self.save_best_model_only = current_model_settings_dict["params_dict"]["main_trainer"]["save_best_model_only"]["value"]
        self.early_stop = current_model_settings_dict["params_dict"]["main_trainer"]["early_stop"]["value"]
        self.early_stopping_patience = current_model_settings_dict["params_dict"]["main_trainer"]["early_stopping_patience"]["value"]
        self.model_selection = current_model_settings_dict["params_dict"]["main_trainer"]["model_selection"]["value"]
        self.val_interval = current_model_settings_dict["params_dict"]["main_trainer"]["val_interval"]["value"]
        self.num_layers = current_model_settings_dict["params_dict"]["main_trainer"]["num_layers"]["value"]
        self.rep_dims = current_model_settings_dict["params_dict"]["main_trainer"]["rep_dims"]["value"]
        self.num_agg_layers = current_model_settings_dict["params_dict"]["main_trainer"]["num_agg_layers"]["value"]
        self.window_size = current_model_settings_dict["params_dict"]["main_trainer"]["window_size"]["value"]
        self.window_stride = current_model_settings_dict["params_dict"]["main_trainer"]["window_stride"]["value"]
        self.window_rep_dims = current_model_settings_dict["params_dict"]["main_trainer"]["window_rep_dims"]["value"]
        self.factor = current_model_settings_dict["params_dict"]["main_trainer"]["factor"]["value"]
        self.alpha = current_model_settings_dict["params_dict"]["main_trainer"]["alpha"]["value"]
        self.layer_fusion = current_model_settings_dict["params_dict"]["main_trainer"]["layer_fusion"]["value"]
        self.act_verbose = current_model_settings_dict["params_dict"]["main_trainer"]["act_verbose"]["value"]
        self.dropout_rate = current_model_settings_dict["params_dict"]["main_trainer"]["dropout_rate"]["value"]

        self.pa2e_epochs = current_model_settings_dict["params_dict"]["pa2e_trainer"]["epochs"]["value"]
        self.val_offset = current_model_settings_dict["params_dict"]["pa2e_trainer"]["val_offset"]["value"]
        self.pa2e_learning_rate = current_model_settings_dict["params_dict"]["pa2e_trainer"]["learning_rate"]["value"]
        self.pa2e_weight_decay = current_model_settings_dict["params_dict"]["pa2e_trainer"]["weight_decay"]["value"]
        self.eps = 1e-9
        self.best_epoch = None
        self.weight = None

        # Loader
        self.train_loader = config["loader_dict"]["train"]
        self.val_loader = config["loader_dict"]["val"]

        self.num_window = int(1 + (self.num_bands - self.window_size) / self.window_stride)

        self.pa2e_model = PA2Ev2(n_band=self.num_bands, n_w = self.num_window, w_s=self.window_size, s=self.window_stride, n_layer=self.num_layers, n_aglayer=self.num_agg_layers, rep_dim=self.rep_dims, w_rep_dim=self.window_rep_dims, dropout=self.dropout_rate, act_verbose=self.act_verbose, factor=self.factor).to(self.device)
		
        self.pae_model = PA_Encoder(n_band=self.num_bands, n_w = self.num_window, w_s=self.window_size, s=self.window_stride, n_layer=self.num_layers, n_aglayer=self.num_agg_layers, rep_dim=self.rep_dims, w_rep_dim=self.window_rep_dims, dropout=self.dropout_rate, act_verbose=self.act_verbose, factor=self.factor).to(self.device)

		# Generate a matrix to perform sliding window operation on input x via matrix multiplication.
        self.set_weight(self.num_bands, self.num_window, self.window_size, self.window_stride)

        pa2e_optim_index = current_model_settings_dict["params_dict"]["pa2e_trainer"]["optimizer"]["value"]
        if pa2e_optim_index == 0:
            self.pa2e_optim = torch.optim.AdamW(self.pa2e_model.parameters(), lr=self.pa2e_learning_rate, weight_decay=self.pa2e_weight_decay)
        elif pa2e_optim_index == 1:
            self.pa2e_optim = torch.optim.Adam(self.pa2e_model.parameters(), lr=self.pa2e_learning_rate, weight_decay=self.pa2e_weight_decay)
        else:
            raise Exception("Not Supported Optimizer Index")
       
        pa2e_scheduler_index = current_model_settings_dict["params_dict"]["pa2e_trainer"]["scheduler"]["value"]
        if pa2e_scheduler_index == 0:
            self.pa2e_scheduler = None
        elif pa2e_scheduler_index == 1:
            self.pa2e_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=self.pa2e_optim, T_max=self.pa2e_epochs)
        else:
            raise Exception("Not Supported Scheduler Index")
        
        # Optimizer Selection (0: AdamW, 1: Adam)
        pae_optim_index = current_model_settings_dict["params_dict"]["main_trainer"]["optimizer"]["value"]
        if pae_optim_index == 0:
            self.pae_optimizer = torch.optim.AdamW(self.pae_model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        elif pae_optim_index == 1:
            self.pae_optimizer = torch.optim.Adam(self.pae_model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        
        # Scheduler Selection (0: Not use, 1: Cosine Scheduler)
        pae_scheduler_index = current_model_settings_dict["params_dict"]["main_trainer"]["scheduler"]["value"]
        if pae_scheduler_index == 0:
            self.pae_scheduler = None
        elif pae_scheduler_index == 1:
            self.pae_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=self.pae_optimizer, T_max=self.pae_epochs)


    def set_weight(self, n_band, n_w, w_s, s):
        """
			Set Sliding window matrix
			Parameters
				- n_band (int): the number of band
				- n_w (int): the number of window
				- w_s (int): window size
				- s (int): stride size
		"""
        self.weight = torch.zeros((n_band, n_w * w_s))
        for i in range(n_w):
            window = np.zeros((w_s,w_s))
            window[np.diag_indices(w_s)] = 1
            self.weight[i*s : i*s+w_s, i*w_s : (i+1)*w_s] = torch.as_tensor(window)
        self.weight = self.weight.to(self.device)

	
    def init_normal_center(self, loader):
        """
			Set the center point of normal data
			Parameters
				- loader (DataLoader): data loader that is used to set the center point
		"""
        c = torch.zeros(self.pae_model.rep_dim, device=self.device)

        self.pae_model.eval()
        num=0
        with torch.no_grad():
            for X, _, abnormality, _ in loader:
                X = X.to(self.device)
                abnormality = abnormality.to(self.device)
                hypothesis, _ = self.pae_model(X)
                num+=len(torch.where(abnormality==-1)[0])
                c += torch.sum(hypothesis[torch.where(abnormality==-1)], dim=0).detach()
        c/=num

        c[(abs(c) < 0.1) & (c <0)] = -0.1
        c[(abs(c) < 0.1) & (c >0)] = 0.1

        self.pae_model.c = nn.Parameter(c)


    def transfer_pretrained_weights(self):
        """
            Load weight of encoder in PA2E to weight of encoder in PAE model.
        """
        self.pa2e_model.eval()
        for parameter in self.pa2e_model.parameters():
            parameter.requires_grad = False

        model = self.pae_model.state_dict()
        model.update({k:v for k,v in self.pa2e_model.state_dict().items() if k in model})
        self.pae_model.load_state_dict(model)
        self.pae_model = self.pae_model.to(self.device)


    def train(self):
        # Progress
        self.progress_manager = ProgressManager(UPDATE_SIZE, len(self.train_loader) * self.pa2e_epochs + (len(self.train_loader) + len(self.val_loader)) * self.pae_epochs, self.shared_data)
        self.progress_manager.init()
        model_score_max = 0
        self.best_epoch = 1

        # ======================================================================================
        # PA2E Part(Pre-Training)
        # ======================================================================================
        for epoch in range(1, self.pa2e_epochs + 1): # Epoch is starting from 1
            is_best_model = False
            loss_total = []
            self.pa2e_model.train()
            for X, _, _, _ in self.train_loader:
                X = X.to(self.device)
                x_hat, xp_hat = self.pa2e_model(X)
                X/=4095.0
                X = X.squeeze()
                X = torch.matmul(X, self.weight)
                loss = torch.sum((x_hat - X) ** 2, dim = 1) # reconstruction loss(global feature)
                loss += self.alpha * torch.sum((xp_hat - X) ** 2, dim = 1) # partial reconstruction loss(local feature)

                loss = loss.mean()
                
                self.pa2e_optim.zero_grad()
                loss.backward()
                self.pa2e_optim.step()
                loss_total.append(loss.item())
                
                self.progress_manager.step()
            
            mean_loss = np.mean(loss_total)

            self._printer.print(f"(Sub {self.current_model_type}) - [Pretrain Training] ", color="#33FFFF", font_weight="bold", append=True)
            self._printer.print(f"Epoch: {epoch}/{self.pa2e_epochs}, Loss: {mean_loss:.5f}")

            if self.pa2e_scheduler != None:
                self.pa2e_scheduler.step()
            
        # ======================================================================================
        # PAE Part(Main Training)
        # ======================================================================================
        # Initialize PAE
        self.transfer_pretrained_weights()
        self.init_normal_center(self.train_loader)
        model_score_max = 0
        early_stop_counter = 0
        self.best_epoch = 1

        for epoch in range(1, self.pae_epochs + 1):
            is_best_model = False
            is_model_saved = False
            loss_total = []
            self.pae_model.train()
            for X, _, abnormality, _ in self.train_loader:
                X = X.to(self.device)
                abnormality = abnormality.to(self.device)
                hypothesis, xp_hat = self.pae_model(X)

                # Compute the L2 loss: sum of squared differences between the normal center and the latent vector from the pae_model
                loss = torch.sum((hypothesis - self.pae_model.c) ** 2, dim = 1) 
                # For normal samples, use l2_loss; for abnormal samples, use its reciprocal (with epsilon) so loss decreases with higher distance.
                loss = torch.where(abnormality == 1, (loss + self.eps)**-1, loss) # abnormality: 1(abnormal), -1(normal)
                if self.alpha != 0:
                    X/=4095.0 # Divide the model's output by 4095.0 for subsequent computation.
                    X = X.squeeze() # Squeeze the input for subsequent operations.
                    X = torch.matmul(X,self.weight) # Apply matrix multiplication with a custom matrix to create a sliding window effect on the input.
                    loss += self.alpha * torch.sum((X - xp_hat) ** 2, dim = 1)
                loss = loss.mean()

                self.pae_optimizer.zero_grad()
                loss.backward()
                self.pae_optimizer.step()

                loss_total.append(loss.item())
                self.progress_manager.step()
            
            mean_loss = np.mean(loss_total)

            self._printer.print(f"(Main {self.current_model_type}) - [Training] ", color="#33FFFF", font_weight="bold", append=True)
            self._printer.print(f"Epoch: {epoch}/{self.pae_epochs}, Loss: {mean_loss:.5f}")

            # Loss
            self.shared_data.put({"train_loss": mean_loss})
            
            if self.pae_scheduler != None:
                self.pae_scheduler.step()
                
            if epoch%self.val_interval == 0:
                if self.model_selection == MODEL_SELECTION_AUPR:
                    model_score = self.test(val=True, data_loader=self.val_loader, epoch=epoch)["aupr"]
                elif self.model_selection == MODEL_SELECTION_LOSS:
                    model_score = -self.test(val=True, data_loader=self.val_loader, epoch=epoch)["loss"]

                if model_score > model_score_max:
                    model_score_max = model_score
                    self.best_epoch = epoch
                    is_best_model = True
                    early_stop_counter = 0
                else:
                    early_stop_counter += 1

                if self.early_stop and early_stop_counter >= self.early_stopping_patience:
                    self._printer.print(f"Training early stop, Epoch: {epoch}/{self.pae_epochs}, Loss: {mean_loss:.5f}")
                    self.progress_manager.step(len(self.train_loader) * self.pae_epochs + (len(self.train_loader) + len(self.val_loader)) * self.pae_epochs)
                    break

            # Save
            if is_best_model:
                self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}.el"))
                is_model_saved = True

            if not self.save_best_model_only:
                self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}_{epoch}.el"))
                is_model_saved = True

            if is_model_saved:
                self._printer.print(f"Model has been saved in {self.current_model_save_path}")

        self._printer.print(f"Main Training Best Epoch: {self.best_epoch}/{self.pae_epochs}")


    def test(self, val=True, data_loader=None, epoch=None) -> dict:
        indices = []
        loss_total = []
        preds_cls = []
        scores = []
        scores_without_ignored = []
        labels_multi = []
        labels_binary = []
        labels_without_ignored = []
        time_list = []
        results = []
        cm = []

        best_thr = 1.0
        aupr = None
        # Progress
        if not val:
            self.progress_manager = ProgressManager(UPDATE_SIZE, len(data_loader), self.shared_data)
            self.progress_manager.init()
        with torch.no_grad():
            self.pae_model.eval()
            for X, _, abnormality, pos in data_loader:                    
                X = X.to(self.device)
                abnormality = abnormality.to(self.device)
                b_start = time()
                if val:
                    hypothesis, xp_hat = self.pae_model(X, inference=False)
                    dist = torch.sum((hypothesis-self.pae_model.c)**2,dim=1)
                    loss = torch.where(abnormality == 1, (dist + self.eps)**-1, dist)
                    if self.alpha != 0:
                        X/=4095.0
                        X = X.squeeze()
                        X = torch.matmul(X,self.weight)
                        loss += self.alpha * torch.sum((X - xp_hat) ** 2, dim = 1)
                    loss = loss.mean()
                else:
                    dist = self.pae_model(X)
                    loss = torch.where(abnormality == 1, (dist + self.eps)**-1, dist).mean() # abnormality: 1(abnormal), -1(normal)
                loss_total.append(loss.item())
                time_list.append(time()-b_start)
                
                dist = dist.to('cpu')
                eval_mask = (abnormality != 0).to('cpu')

                scores.append(dist)
                scores_without_ignored.append(dist[eval_mask])
                labels = torch.where(abnormality == -1, 2, torch.where(abnormality != 0, 3, 0)).to('cpu')
                labels_binary.append(labels)
                labels_without_ignored.append(labels[eval_mask])
                pos = torch.stack(pos) # (batch_size, 3)
                indices.append(pos.transpose(0, 1))
                
                self.progress_manager.step()

            mean_loss = np.mean(loss_total)

            if val:
                self._printer.print(f"(Main {self.current_model_type}) - [Validation] ", color="#F4FA58", font_weight="bold", append=True)
                self._printer.print(f"Epoch: {epoch}/{self.pae_epochs}, Loss: {mean_loss:.5f}")
            else:
                self._printer.print(f"(Main {self.current_model_type}) - [Testing] ", color="#CE33FF", font_weight="bold", append=False)
                self._printer.print(f"Mean Loss: {mean_loss:.5f}")

            preds_cls = cat_tensor(preds_cls)
            scores = cat_tensor(scores)
            scores_without_ignored = cat_tensor(scores_without_ignored) # Score variable for metric calculation during model testing.
            labels_multi = cat_tensor(labels_multi)
            labels_without_ignored = cat_tensor(labels_without_ignored) # Label variable for metric calculation during model testing.
            num_labels_without_ignored = len(np.unique(labels_without_ignored)) # Number of classes excluding ignored regions.
            has_only_ignored_label = True if num_labels_without_ignored == 0 else False # Variable to check if only ignored regions are present.
            
            if not val:
                indices = cat_tensor(indices)
                labels_binary = cat_tensor(labels_binary)

            # ============= Binary =============
            # AUPR
            # Check if there are valid labels for evaluation (not just ignored labels and at least 2 different classes)
            if not has_only_ignored_label and num_labels_without_ignored > 1:
                precision, recall, thresholds = precision_recall_curve(labels_without_ignored-2, scores_without_ignored)
                aupr = average_precision_score(labels_without_ignored-2, scores_without_ignored)
                f1scores = 2.*(recall*precision)/(recall+precision+self.eps)
                best_thr = thresholds[np.argmax(f1scores)]

            if not self.is_train:
                if (tmp_thr := get_threshold_from_log(os.path.dirname(self.current_model_load_path))) is not None:
                    best_thr = tmp_thr

            # best threshold ad results
            preds_ad_without_ignored = np.where(scores_without_ignored < best_thr, 2, 3) # normal < threshold <= abnormal
            preds_ad = np.where(scores < best_thr, 2, 3)
            preds = preds_ad
            labels = labels_binary
            mean_inf_time = time_list[0] if len(time_list) == 1 else np.mean(time_list[:-1]) # Handle case where only one time exists; use mean otherwise.

            if num_labels_without_ignored > 0:
                results, cm = get_scores(preds_ad_without_ignored, labels_without_ignored)                

            # ============= Result =============
            for c in np.unique(labels_without_ignored):
                score = scores_without_ignored[np.where(labels_without_ignored == c)]
                self._printer.print(f"Class {str(c)}: Score N(mean={np.mean(score):.5f}, std={np.std(score):.5f})")
            self._printer.print(f"Average Batch Inference Time: {mean_inf_time*1000:.3f} ms")
            if aupr is not None:
                self._printer.print(f"AUPR: {aupr:.5f}")
            self._printer.print(f"Best Threshold: {best_thr:.5f}")
            if not val:
                for result in results:
                    self._printer.print(result)
                origin_images, label_images = self.visualization(indices, labels, preds)
                self.shared_data.put({"origin_images": origin_images})
                self.shared_data.put({"label_images": label_images})
                self.shared_data.put({"results": results})
                self.shared_data.put({"cm": cm})
                self.shared_data.put({"best_threshold": best_thr}) # threshold for all
                self.shared_data.put({"abnormal_scores": scores})
                self.shared_data.put({"labels": labels_binary})
                self.shared_data.put({"position_indices": indices})
                self.shared_data.put({"is_anomaly_detection": None})
                self.progress_manager.step() # last progress step
            else:
                self.shared_data.put({"abnormal_avg_f1score": float(results[-1].split(" ")[-1])}) # abnormal_average f1score
                self.shared_data.put({"val_loss": mean_loss})
            # ============= Result =============
        
        return {"aupr": aupr, "loss": mean_loss}

    def save(self, save_path):
        if self.layer_fusion:
            copied_model = PA_Encoder(n_band=self.num_bands, n_w = self.num_window, w_s=self.window_size, s=self.window_stride, n_layer=self.num_layers, n_aglayer=self.num_agg_layers, rep_dim=self.rep_dims, w_rep_dim=self.window_rep_dims, dropout=self.dropout_rate, act_verbose=self.act_verbose, factor=self.factor).to(self.device)
            
            copied_model.load_state_dict(self.pae_model.state_dict())
            optimized_pae_model = Optimize(modules=copied_model, n_band=self.num_bands, n_w=self.num_window, w_s=self.window_size, s=self.window_stride)
            output_model = PA2E_model(optimized_pae_model, self.pae_model.c)
        else:
            output_model = self.pae_model
        
        """
            Set dummy input shape based on patch_size for model tracing.

            Modified by Chansik Kim 2025.09.08
        """
        save_model(output_model, save_path, self.num_bands, self.patch_size, self.batch_size, self.device)

    def load(self, load_path:str) -> None:
        """
        Load the TorchScript model onto the specified device.

        Args:
            load_path (str): Path to the TorchScript model file.
            device (str): Device to load the model onto. Default is 'cuda:0'.

        Modified by Chansik Kim 2025.09.08
        """
        self.pae_model = load_model(load_path, device=self.device)

    def visualization(self, indices, labels, preds):
        origin_images, _, label_images = get_images(self.images, indices, labels, preds, os.path.join(self.current_model_save_path), f"{self.current_model_type.replace(' ', '_')}", list(zip(*self.data_path_dict["test"]))[0])
        return origin_images, label_images
        