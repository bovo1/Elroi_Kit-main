import os
import torch
import numpy as np

from time import time
from sklearn.preprocessing import OneHotEncoder
from constants.constants import *

from ..models.PD import PLSDA

from ..utils import ProgressManager, makeMetadata, modelMetadata, save_model, load_model, get_scores, get_images

class T_PLSDA():
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
        self.config = config
        self.current_model_param_dict = config["current_model_param_dict"]
        self.hyperparameter_shared_dict = config["hyperparameter_shared_dict"]
        self.current_model_type = config["hyperparameter_shared_dict"]["current_model_type"]
        current_model_settings_dict = config["hyperparameter_shared_dict"][self.current_model_type]

        # Model Configuration
        self.max_iter = int(current_model_settings_dict["params_dict"]["main_trainer"]["max_iter"]["value"])
        self.num_lv = current_model_settings_dict["params_dict"]["main_trainer"]["num_lv"]["value"]
        self.thr = current_model_settings_dict["params_dict"]["main_trainer"]["thr"]["value"]
        self.batch_size = int(current_model_settings_dict["params_dict"]["loader"]["batch_size"]["value"])
        self.patch_size = int(current_model_settings_dict["params_dict"]["loader"]["patch_size"]["value"])

        # Train Loader
        if self.is_train:
            # Loader
            self.train_loader = config["loader_dict"]["train"]
            # Progress
            self.progress_manager = ProgressManager(UPDATE_SIZE, self.num_lv, config["shared_data"])
            self.progress_manager.init()

            self._printer.print(f"({self.current_model_type}) Preparing training dataset...")
            self.train_data = []; self.train_label = []; self.train_indices = []
            for _, (X, Y, _, _) in enumerate(self.train_loader):
                self.train_data += list(X.numpy())
                self.train_label += list(Y.numpy())
            self.train_data = np.array(self.train_data)
            self.train_label = np.array(self.train_label)

            # Build a Dummy Values
            self.train_label = self.train_label.reshape(-1, 1)
            self.labelMapping = np.unique(self.train_label)
            self.encoder = OneHotEncoder()
            self.dummy_values = self.encoder.fit_transform(self.train_label).toarray().astype(np.float32)
        else:
            # Init ProgressManager for test
            self.test_loader = config["loader_dict"]["test"]
            self.progress_manager = ProgressManager(UPDATE_SIZE, len(self.test_loader), config["shared_data"])

        # Build a Model
        self.model = PLSDA(self.num_bands, self.num_classes, max_iter=self.max_iter, num_lv=self.num_lv, progress_manager=self.progress_manager, device=self.device)
        self._printer.print(f"({self.current_model_type}) parameters -> max_iter: {self.max_iter}, num_lv: {self.num_lv}")
        
        """
            @description : Collect and save model metadata for PD
            @author : Hyunsu Kim(2026.03.03)
        """
        self.metadatas = {}
        if self.is_train:
            self.metadatas = makeMetadata(config, self.num_bands, not self.binary, self.batch_size, self.patch_size,\
                                        self.num_classes, self.current_model_type, self.hyperparameter_shared_dict, self.current_model_param_dict, self.model.modelType)

    def train(self):
        """
            description : Collect and save model metadata after each epoch
            author : Hyunsu Kim(2026.03.03)
        """
        self._printer.print(f"({self.current_model_type}) - [Training]...", color="#33FFFF", font_weight="bold")
        self.model.fit(self.train_data, self.dummy_values)

        self.modelMetadata = modelMetadata.setMetadata(self.metadatas).to_dict()
        self.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}.el"), self.modelMetadata)
    
    def test(self, val:bool=False, data_loader=None):
        self._printer.print(f"({self.current_model_type}) - [Testing]...", color="#CE33FF", font_weight="bold")
        preds = []; labels = []; indices = []
        time_list = []

        # Progress
        if not self.is_train:
            self.progress_manager.init()
            
        for _, (X, Y, _, pos) in enumerate(self.test_loader):
            X = X.to(self.device)

            # Prediction
            # Transform the original label using label mapping
            b_start = time()
            hypothesis = torch.argmax(self.model(X), dim=1)
            hypothesis = hypothesis.to('cpu').numpy()
            hypothesis = np.array(self.labelMapping)[hypothesis]
            preds += list(hypothesis)
            time_list.append(time() - b_start)

            labels += list(Y.numpy())
            indices += list(zip(*pos))

            self.progress_manager.step()

        preds = np.array(preds)
        labels = np.array(labels)
        # ============= Result =============
        results, cm = get_scores(preds, labels)
        for result in results:
            self._printer.print(result)

        # Save Prediction Image
        self.visualization(indices, labels, preds)
        self.shared_data.put({"results": results})
        self.shared_data.put({"cm": cm})
        self._printer.print(f"Average batch inference time: {np.mean(time_list[:-1])*1000:.3f} ms")
        self.shared_data.put({"is_classification": None})
        # ============= Result =============

        self.progress_manager.step() # last progress step
        return None

    def save(self, save_path, modelMetadata=None):
        patch_size = 1
        batch_size = 512
        """
            Set dummy input shape based on patch_size for model tracing.

            Modified by Chansik Kim 2025.09.08

            History:
                1. Save label mapping file along with the model Modified by Hyunsu Kim 2025.09.10
        """
        save_model(self.model, save_path, self.num_bands, patch_size, batch_size, self.device, modelMetadata)
        np.save(os.path.join(self.current_model_save_path, f"{self.current_model_type.replace(' ', '_')}_labelMapping.npy"), self.labelMapping)
        self._printer.print(f"Model has been saved in {self.current_model_save_path}")

    def load(self, load_path):
        """
        Load the TorchScript model onto the specified device.

        Args:
            load_path (str): Path to the TorchScript model file.
            device (str): Device to load the model onto. Default is 'cuda:0'.

        Modified by Chansik Kim 2025.09.08

        History:
            1. Load label mapping file along with the model Modified by Hyunsu Kim 2025.09.10
        """
        self.model, self.modelMetadata = load_model(load_path, device=self.device)
        self.labelMapping = np.load(os.path.join("\\".join(load_path.split("\\")[:-1]), f"{self.current_model_type}_labelMapping.npy"))

    def visualization(self, indices, labels, preds):
        origin_images, pred_images, label_images = get_images(self.images, indices, labels, preds, os.path.join(self.current_model_save_path, f"result_images"), f"{self.current_model_type.replace(' ', '_')}", list(zip(*self.data_path_dict["test"]))[0])
        self.shared_data.put({"origin_images": origin_images})
        self.shared_data.put({"pred_images": pred_images})
        self.shared_data.put({"label_images": label_images})