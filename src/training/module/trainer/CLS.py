"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

import os
import numpy as np
import torch
import torch.nn as nn

from time import time
from constants.constants import *

from ..utils import ProgressManager, save_model, load_model, get_scores, get_images

from ..models.DN import DDCNN
from ..models.SC import SSGCA

"""
description: training module for hyperspectral classification task
author : HyeokYoon
modified by HyeokYoon (20240219)

recently works
- removed verbose option and related parameters
"""
class T_CLS:
    def __init__(self, config):
        # Common Configuration
        self.is_train = config["is_train"]
        self.device = config["device"]
        self.num_bands = config["num_bands"]
        self.num_classes = config["num_classes"]
        self.images = config["images"]
        self.binary = config["binary"]
        self.current_model_save_path = config["current_model_save_path"]
        self.data_path_dict = config["data_path_dict"]
        self.shared_data = config["shared_data"]
        self._printer = config["_printer"]
        self.best_epoch = None

        self.current_model_type = config["hyperparameter_shared_dict"]["current_model_type"]
        current_model_settings_dict = config["hyperparameter_shared_dict"][self.current_model_type]
        self.current_model_name = current_model_settings_dict["model_name"]

        # Model Configuration
        self.batch_size = current_model_settings_dict["params_dict"]["loader"]["batch_size"]["value"]
        self.patch_size = current_model_settings_dict["params_dict"]["loader"]["patch_size"]["value"]
        
        self.learning_rate = current_model_settings_dict["params_dict"]["main_trainer"]["learning_rate"]["value"]
        self.weight_decay = current_model_settings_dict["params_dict"]["main_trainer"]["weight_decay"]["value"]
        self.dropout = current_model_settings_dict["params_dict"]["main_trainer"]["dropout"]["value"]
        self.epochs = current_model_settings_dict["params_dict"]["main_trainer"]["epochs"]["value"]
        self.save_best_model_only = current_model_settings_dict["params_dict"]["main_trainer"]["save_best_model_only"]["value"]
        self.early_stop = current_model_settings_dict["params_dict"]["main_trainer"]["early_stop"]["value"]
        self.early_stopping_patience = current_model_settings_dict["params_dict"]["main_trainer"]["early_stopping_patience"]["value"]
        self.val_interval = current_model_settings_dict["params_dict"]["main_trainer"]["val_interval"]["value"]
        
        # Loader
        self.train_loader = config["loader_dict"]["train"]
        self.val_loader = config["loader_dict"]["val"]

        # Model Selection
        if self.current_model_name == "DDCNN":
            self.model = DDCNN(self.num_bands, self.num_classes, dropout=self.dropout).to(self.device)
        elif self.current_model_name == "SSGCA":
            self.model = SSGCA(self.num_bands, self.num_classes, patch_size=self.patch_size, device=self.device, dropout=self.dropout).to(self.device)
        
        # Loss Function Selection (0: Cross Entropy)
        loss_function_index = current_model_settings_dict["params_dict"]["main_trainer"]["loss_function"]["value"]
        if loss_function_index == 0:
            self.criterion = nn.CrossEntropyLoss()
        
        # Optimizer Selection (0: Adam)
        optimizer_index = current_model_settings_dict["params_dict"]["main_trainer"]["optimizer"]["value"]
        if optimizer_index == 0:
            self.optim = torch.optim.AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        elif optimizer_index == 1:
            self.optim = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        
        # Scheduler Selection (0: Not use, 1: Cosine)
        scheduler_index = current_model_settings_dict["params_dict"]["main_trainer"]["scheduler"]["value"]
        if scheduler_index == 0:
            self.scheduler = None
        elif scheduler_index == 1:
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=self.optim, T_max=self.epochs)

    def train(self):
        # local varialbes
        total_batch = len(self.train_loader)
        loss_min = np.inf
        early_stop_counter = 0
        self.best_epoch = 1

        # progress
        self.progress_manager = ProgressManager(UPDATE_SIZE, (len(self.train_loader) + len(self.val_loader)) * self.epochs + 1, self.shared_data)
        self.progress_manager.init()

        # Classification Model train
        self.model.train()
        for epoch in range(1, self.epochs + 1):
            is_best_model = False
            is_model_saved = False
            loss_total = []
            for batch_idx, (X, Y, _, _) in enumerate(self.train_loader):
                X = X.to(self.device)
                Y = Y.to(self.device)
                if self.binary:
                    Y[Y != 0] -= self.num_classes
                
                hypothesis = self.model(X)
                loss = self.criterion(hypothesis, Y)

                self.optim.zero_grad()
                loss.backward()
                self.optim.step()

                loss_total.append(loss.item())
                self.progress_manager.step()

            mean_loss = np.mean(loss_total)
            self._printer.print(f"({self.current_model_type}) - [Training] ", color="#33FFFF", font_weight="bold", append=True)
            self._printer.print(f"Epoch: {epoch}/{self.epochs}, Loss: {mean_loss:.5f}")

            # Loss
            self.shared_data.put({"train_loss": mean_loss})

            if self.scheduler:
                self.scheduler.step()

            if epoch%self.val_interval == 0:
                val_loss = self.test(True, self.val_loader, epoch)["total_loss"]
                
                # Early stop counter
                if val_loss < loss_min:
                    early_stop_counter = 0
                    loss_min = val_loss
                    self.best_epoch = epoch
                    is_best_model = True
                else:
                    early_stop_counter += 1
                
                # Early stop
                if self.early_stop and early_stop_counter >= self.early_stopping_patience:
                    self._printer.print(f"Training early stop, Epoch: {epoch}/{self.epochs}, Loss: {mean_loss:.5f}")
                    self.progress_manager.step((len(self.train_loader) + len(self.val_loader)) * self.epochs)
                    break
            
            # Save the model if it achieves the best performance so far
            if is_best_model:
                self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}.el"))
                is_model_saved = True
            
            # Save model for each epoch if save_best_model_only is False
            if not self.save_best_model_only:
                self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}_{epoch}.el"))
                is_model_saved = True

            # Print save confirmation message if any model was saved
            if is_model_saved:
                self._printer.print(f"Model has been saved in {self.current_model_save_path}")

        self._printer.print(f"Best epoch: {self.best_epoch}/{self.epochs}")

    def test(self, val=True, data_loader=None, epoch=None):
        # local variables
        indices = []
        loss_total = []
        preds = []
        labels = []
        time_list = []

        # progress
        if not val:
            self.progress_manager = ProgressManager(UPDATE_SIZE, len(data_loader), self.shared_data)
            self.progress_manager.init()

        self.model.eval()
        with torch.no_grad():
            for X, Y, _, pos in data_loader:
                b_start = time() # start ====================

                X = X.to(self.device)
                Y = Y.to(self.device)
                if self.binary:
                    Y[Y != 0] -= self.num_classes

                hypothesis = self.model(X)
                loss = self.criterion(hypothesis, Y)
                loss_total.append(loss.item())
                hypothesis = torch.argmax(hypothesis, 1)

                time_list.append(time()-b_start) # end ======

                preds += list(hypothesis.to('cpu').numpy())
                labels += list(Y.to('cpu').numpy())
                indices += list(zip(*pos))

                # if not val:
                #     self.shared_data.put({"test_loss": loss.item()}) # test loss
                    
                self.progress_manager.step() # batch progress
            mean_loss = np.mean(loss_total)

            if val:
                self._printer.print(f"({self.current_model_type}) - [Validation] ", color="#F4FA58", font_weight="bold", append=True)
                self._printer.print(f"Epoch: {epoch}/{self.epochs}, Loss: {mean_loss:.5f}")
            else:
                self._printer.print(f"({self.current_model_type}) - [Testing] ", color="#CE33FF", font_weight="bold", append=True)
                self._printer.print(f"Mean Loss: {mean_loss:.5f}")

            preds = np.array(preds)
            labels = np.array(labels)
            
            results, cm = get_scores(preds, labels)
            # ============= Result =============
            for result in results:
                self._printer.print(result)
            self.shared_data.put({"abnormal_avg_f1score": float(results[-1].split(" ")[-1])}) # abnormal_average f1score
            self._printer.print(f"Average Batch Inference Time: {np.mean(time_list[:-1])*1000:.3f} ms")

            # last step (test visualization and save)
            if not val:
                self.visualization(indices, labels, preds)
                self.shared_data.put({"results": results})
                self.shared_data.put({"cm": cm})
                self.shared_data.put({"is_classification": None})
                self.progress_manager.step() # last progress step
            else:
                self.shared_data.put({"val_loss": mean_loss}) # validation loss
            # ============= Result =============

        return {"total_loss": np.sum(loss_total)}

    def save(self, save_path):
        """
            Set dummy input shape based on patch_size for model tracing.

            Modified by Chansik Kim 2025.09.08
        """
        save_model(self.model, save_path, self.num_bands, self.patch_size, self.batch_size, self.device)
        
    def load(self, load_path):
        """
        Load the TorchScript model onto the specified device.

        Args:
            load_path (str): Path to the TorchScript model file.
            device (str): Device to load the model onto. Default is 'cuda:0'.

        Modified by Chansik Kim 2025.09.08
        """
        self.model.load_state_dict(load_model(load_path, device=self.device).state_dict())

    def visualization(self, indices, labels, preds):
        origin_images, pred_images, label_images = get_images(self.images, indices, labels, preds, os.path.join(self.current_model_save_path, f"result_images"), f"{self.current_model_type.replace(' ', '_')}", list(zip(*self.data_path_dict["test"]))[0])
        self.shared_data.put({"origin_images": origin_images})
        self.shared_data.put({"pred_images": pred_images})
        self.shared_data.put({"label_images": label_images})