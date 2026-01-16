import torch
import torch.nn as nn
from .Module import *

class SSGCA(nn.Module):
    def __init__(self, num_bands, num_classes, patch_size=7, device="cuda", dropout=0.5):
        super().__init__()
        self.num_bands = num_bands
        self.num_classes = num_classes
        self.device = device
        self.patch_size = patch_size
        self.dropout=dropout
    
        self.n_skip = 3
        self.init_dim = 24
        self.inter_dim = 12
        self.rep_dim = self.init_dim + self.inter_dim*self.n_skip
        self.r = 16
        self.p_band = int((self.num_bands- 7)/2)+1

        # Spectral Feature Extraction
        self.spectral = []
        self.spectral.append(nn.Conv3d(1, 24, (7, 1, 1), stride=(2, 1, 1)))
        for i in range(self.n_skip):
            self.spectral.append(Spectral_Dense(24+i*12, 12, k=7, s=1, padding="same"))
        self.spectral.append(nn.Sequential(
                                    nn.BatchNorm3d(24+(i+1)*12),
                                    nn.ReLU(),
                                    nn.Conv3d(24+(i+1)*12, 24+(i+1)*12, (self.p_band, 1, 1), (1, 1, 1))
                                )
                            )
        self.spectral = nn.Sequential(*self.spectral)

        # Spectral Feature Enhancement
        self.spectral_e = Spectral_Enhance(self.rep_dim,self.patch_size,self.r, dropout=self.dropout).to(device)
        
        # Spatial Feature Extraction
        self.spatial = []
        self.spatial.append(nn.Conv3d(1, 24, (self.num_bands, 1, 1), stride=(1, 1, 1)))
        for i in range(self.n_skip):
            self.spatial.append(Spatial_Dense(24+i*12, 12, k=3, s=1, padding="same"))
        self.spatial= nn.Sequential(*self.spatial)

        # Spatial Feature Enhancement
        self.spatial_e = Spatial_Enhance(self.rep_dim,self.patch_size,self.r, dropout=self.dropout).to(device)


        #Feature Fusion
        self.spectral_avg = nn.Sequential(
                                nn.BatchNorm2d(self.rep_dim),
                                nn.ReLU(),
                                nn.AdaptiveAvgPool2d(1)
                            )
        self.spatial_avg = nn.Sequential(
                                nn.BatchNorm2d(self.rep_dim),
                                nn.ReLU(),
                                nn.AdaptiveAvgPool2d(1)
                            )

        self.fc = nn.Linear(self.rep_dim*2, num_classes)

    def forward(self, img):
        img = img/4095.0
        img = img.unsqueeze(1)
        
        #Spectral feature extraction stage
        spectral_stack = self.spectral(img).view(-1, self.rep_dim, self.patch_size, self.patch_size)

        # Spectral Feature Enhancement stage
        spectral_stack = self.spectral_e(spectral_stack)

        #Spatial feature extraction stage
        spatial_stack = self.spatial(img).view(-1, self.rep_dim, self.patch_size, self.patch_size)
            
        # Spatial Feature Enhancement stage
        spatial_stack = self.spatial_e(spatial_stack)

        # Feature Fusion stage
        spectral_stack = self.spectral_avg(spectral_stack).view(-1, self.rep_dim)
        spatial_stack = self.spatial_avg(spatial_stack)
        spatial_stack = spatial_stack.view(-1, self.rep_dim)
        
        return self.fc(torch.cat([spectral_stack, spatial_stack], 1))