import torch
import torch.nn as nn
from .Module import Encoder, Joint_Classifier

class DSAD(nn.Module):
    def __init__(self, num_bands, num_layers=4, rep_dim=64, patch_size=1, normalization=False, CNN=False):
        super().__init__()
        self.num_bands = num_bands
        self.num_layers = num_layers
        self.rep_dim = rep_dim
        self.CNN = CNN
        self.modelType = "AD"
        
        '''
            descriptoin: Changed the center vector c, originally declared as torch.tensor, to register_buffer so that it can be saved and loaded as part of the model's state.
            modified by Chansik Kim 2025.12.09
        '''
        self.register_buffer("c", torch.zeros(rep_dim))
        if CNN:
            self.encoder = Encoder(num_bands, num_layers, rep_dim, patch_size, normalization, CNN=True, flatten=True)
        else:
            self.encoder = Encoder(num_bands, num_layers, rep_dim, patch_size, normalization)

    def forward(self, x):
        x = self.encoder(x)
        """
            description : Modify power operation to element-wise multiplication for better inference speed, as the original code's power operation can be computationally expensive.
            modified by Chansik Kim 2026.03.18
        """
        diff = x - self.c
        dist = (diff * diff).sum(dim=1)
        return dist

class CDSAD(DSAD):
    def __init__(self, num_bands, num_layers=4, rep_dim=64, patch_size=1, normalization=False, CNN=False, num_classes=2):
        super().__init__(num_bands, num_layers, rep_dim, patch_size, normalization, CNN)
        self.cls_head = Joint_Classifier(num_classes, rep_dim)
        self.modelType = "AD_CLS"
        
    def forward(self, x):
        lv = self.encoder(x)
        fc = self.cls_head(lv)
        """
            description : Modify power operation to element-wise multiplication for better inference speed, as the original code's power operation can be computationally expensive.
            modified by Chansik Kim 2026.03.18
        """
        diff = lv - self.c
        dist = (diff * diff).sum(dim=1)
        return fc, dist