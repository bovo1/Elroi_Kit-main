import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from .Func import *

"""
Squeeze Module
"""
class Squeeze(nn.Module):
    def __init__(self, dim=-1):
        super().__init__()
        self.dim = dim
    
    def forward(self, x):
        return torch.squeeze(x, self.dim)

"""
Unsqueeze Module
"""
class Unsqueeze(nn.Module):
    def __init__(self, dim=-1):
        super().__init__()
        self.dim = dim
    
    def forward(self, x):
        return torch.unsqueeze(x, self.dim)

"""
Scaling Module
"""
class Scaling(nn.Module):
    def __init__(self, divide=4095.0):
        super().__init__()
        self.divide = divide
    
    def forward(self, x):
        return x / self.divide

"""
Normalization Module
"""
class Normalization(nn.Module):
    def __init__(self, num_bands, patch_size, dim=-1):
        super().__init__()
        self.num_bands = num_bands
        self.patch_size = patch_size
        self.dim = dim
    
    def forward(self, x):
        # return F.normalize(x, dim=self.dim)
        return F.normalize(x.reshape(x.size(0), -1), dim=self.dim).reshape(-1, self.num_bands, self.patch_size, self.patch_size)
    
"""
Joint Classifier
description: Classification head for joint classification tasks with added hidden layer including BatchNorm, LeakyReLU, and Dropout.
modified by Chansik Kim 2025.12.09
"""
class Joint_Classifier(nn.Module):
    def __init__(self, num_classes, rep_dim):
        super().__init__()
        self.cls_head = nn.Sequential(
            nn.Linear(rep_dim, rep_dim*2, bias=False),
            nn.BatchNorm1d(rep_dim*2),
            nn.LeakyReLU(0.01),
            nn.Dropout(p=0.1),

            nn.Linear(rep_dim*2, rep_dim, bias=False),
            nn.BatchNorm1d(rep_dim),
            nn.LeakyReLU(0.01),

            nn.Linear(rep_dim, num_classes)
        )

    def forward(self, x):
        return self.cls_head(x)


"""
Encoder [MLP/CNN]
"""
class Encoder(nn.Module):
    def __init__(self, num_bands, num_layers, rep_dim, patch_size, normalization=False, CNN=False, flatten=False):
        super().__init__()
        assert num_bands > rep_dim

        self.encoder_layers = []

        self.encoder_layers.append(Scaling(4095.0))

        if normalization:
            self.encoder_layers.append(Normalization(num_bands, patch_size))

        if CNN:
            diff = (num_bands-rep_dim)/(num_layers+1)
            ker = (patch_size-1)/(num_layers+1)
            hidden_size = [num_bands]+[int(num_bands-diff*(i+1)) for i in range(num_layers-1)]+[rep_dim]
            output_size = [patch_size]+[int(patch_size-ker*(i+1)) if int(patch_size-ker*(i+1)) % 2 != 0 else int(patch_size-ker*(i+1))+1 for i in range(num_layers-1)]+[1]
            kernel_size = sorted([output_size[i]-output_size[i+1]+1 for i in range(len(output_size)-1)], reverse=True)

            # CNN Encoder
            [self.encoder_layers.append(encoder_conv_block(hidden_size[i], hidden_size[i+1], kernel_size=kernel_size[i])) for i in range(len(hidden_size)-2)]
            self.encoder_layers.append(encoder_conv_block(hidden_size[num_layers-1], hidden_size[num_layers], kernel_size=kernel_size[-1], activation=False))

            if flatten:
                self.encoder_layers.append(nn.Flatten())
        else:
            hidden_dim = num_bands*patch_size*patch_size
            diff = ((hidden_dim)-rep_dim )/(num_layers)
            hidden_size = [hidden_dim]+[int(hidden_dim-diff*(i+1)) for i in range(num_layers-1)]+[rep_dim]
            
            # MLP Encoder
            self.encoder_layers.append(nn.Flatten())
            [self.encoder_layers.append(mlp_block(hidden_size[i], hidden_size[i+1])) for i in range(len(hidden_size)-2)]
            self.encoder_layers.append(mlp_block(hidden_size[-2], hidden_size[-1], activation=False))

        self.encoder = nn.Sequential(*self.encoder_layers)

    def forward(self, x):
        return self.encoder(x)

"""
Decoder [MLP/CNN]
"""
class Decoder(nn.Module):
    def __init__(self, num_bands, num_layers, rep_dim, patch_size, CNN=False):
        super().__init__()
        assert num_bands > rep_dim

        self.num_bands = num_bands
        self.patch_size = patch_size

        self.decoder_layers = []

        if CNN:
            diff = (num_bands-rep_dim)/(num_layers+1)
            ker = (patch_size-1)/(num_layers+1)
            hidden_size = [num_bands]+[int(num_bands-diff*(i+1)) for i in range(num_layers-1)]+[rep_dim]
            output_size = [patch_size]+[int(patch_size-ker*(i+1)) if int(patch_size-ker*(i+1)) % 2 != 0 else int(patch_size-ker*(i+1))+1 for i in range(num_layers-1)]+[1]
            kernel_size = sorted([output_size[i]-output_size[i+1]+1 for i in range(len(output_size)-1)])

            # CNN Decoder
            self.decoder_layers = []
            [self.decoder_layers.append(decoder_conv_block(hidden_size[i], hidden_size[i-1], kernel_size=kernel_size[i-1])) for i in reversed(range(2, len(hidden_size)))]
            self.decoder_layers.append(decoder_conv_block(hidden_size[1], hidden_size[0], kernel_size=kernel_size[0], activation=False))
        else:
            hidden_dim = num_bands*patch_size*patch_size
            diff = ((hidden_dim)-rep_dim )/(num_layers)
            hidden_size = [hidden_dim]+[int(hidden_dim-diff*(i+1)) for i in range(num_layers-1)]+[rep_dim]
            
            # MLP Decoder
            [self.decoder_layers.append(mlp_block(hidden_size[i], hidden_size[i-1])) for i in reversed(range(2, len(hidden_size)))]
            self.decoder_layers.append(mlp_block(hidden_size[1], hidden_size[0], activation=False))
        self.decoder = nn.Sequential(*self.decoder_layers)
        
    def forward(self, x):
        """
        Performs a forward pass through the decoder and reshapes the output tensor.
        Args:
            x (torch.Tensor): Input tensor to the decoder.
        Returns:
            torch.Tensor: Output tensor reshaped to either (batch_size, num_bands) if patch_size is 1,
                          or (batch_size, num_bands, patch_size, patch_size) otherwise.

        Modified by Chansik Kim 2025.06.17
        """
        out = self.decoder(x)
        if self.patch_size == 1:
            return out.view(-1, self.num_bands)
        else:
            return out.view(-1, self.num_bands, self.patch_size, self.patch_size)

"""
AutoEncoder [MLP/CNN]
"""
class AutoEncoder(nn.Module):
    def __init__(self, num_bands, num_layers, rep_dim, patch_size, normalization=False, CNN=False, flatten=False):
        super().__init__()

        self.encoder = Encoder(num_bands, num_layers, rep_dim, patch_size, normalization, CNN, flatten)
        self.decoder = Decoder(num_bands, num_layers, rep_dim, patch_size, CNN)

    def forward(self, x):
        return self.decoder(self.encoder(x))

class P_Encoder(nn.Module):
	def __init__(self, n_band=224, n_w=1, w_s=224, s=0, n_layer=3, rep_dim=32, dropout=0, act_verbose=[1,1,1], factor=1):
		"""
			Partial Encoder
			Parameters
				- n_band (int): the number of band
				- n_w (int): the number of window
				- w_s (int): window size
				- s (int): stride size
				- n_layer (int): the number of partial layer
				- rep_dim (int): the representation dimension
				- dropout (float): dropout ratio
				- act_verbose (list): relu culling location
				- factor (float): the parameter for hidden size between layers
		"""
		super().__init__()
		self.n_w=n_w
		self.w_s=w_s
		self.n_layer = n_layer
		self.dim=n_w*w_s
		self.rep_dim = n_w*rep_dim
     
		self.encoder_layers = []
		self.encoder_layers.append(Scaling(4095.0))
		self.encoder_layers.append(nn.Flatten())

		#Sliding window layer
		window_layer = nn.Linear(n_band,n_w*w_s,bias=True)
		weight = torch.zeros((n_band,n_w*w_s))
		bias= torch.zeros((n_w*w_s))
		for i in range(n_w):
			window = np.zeros((w_s,w_s))
			window[np.diag_indices(w_s)] = 1
			weight[i*s:i*s+w_s,i*w_s:(i+1)*w_s] = torch.as_tensor(window)
		with torch.no_grad():
			window_layer.weight.copy_(weight.T)
			window_layer.bias.copy_(bias)
		window_layer.weight.requires_grad_(False)
		window_layer.bias.requires_grad_(False)

		LayerRatio= [(i/n_layer)**(1/factor) for i in range(n_layer+1)]
		LayerRatio= np.array(LayerRatio)

		self.hidden_size=list((w_s-rep_dim)*LayerRatio+rep_dim)
		self.hidden_size= np.array(self.hidden_size,dtype=np.int32)[::-1]

		#Partial Encoder
		self.encoder_layers += [block(self.hidden_size[0], self.hidden_size[1], n_w, act=act_verbose[0], dropout=dropout, pre_func=window_layer)]
		for i in range(1,len(self.hidden_size)-2):
			self.encoder_layers += [block(self.hidden_size[i], self.hidden_size[i+1], n_w, act=act_verbose[i], dropout=dropout)]
		self.encoder_layers +=[block(self.hidden_size[-2], self.hidden_size[-1], n_w, act=None, dropout=0)]
		self.encoder = nn.Sequential(*self.encoder_layers)


	def forward(self,x):
		x = self.encoder(x)
		return x
	
class P_Decoder(nn.Module):
	def __init__(self, n_w=1, w_s=224, n_layer=3, rep_dim=32, dropout=0, act_verbose=[1,1,1], factor=1):
		"""
			Partial Decoder
			Parameters
				- n_band (int): the number of band
				- n_w (int): the number of window
				- w_s (int): window size
				- n_layer (int): the number of partial layer
				- rep_dim (int): the representation dimension
				- dropout (float): dropout ratio
				- act_verbose (list): relu culling location
				- factor (float): the parameter for hidden size between layers
		"""
		super().__init__()
		self.n_w=n_w
		self.w_s=w_s
		self.n_layer = n_layer
		self.dim=n_w*w_s
		self.rep_dim = n_w*rep_dim

		LayerRatio= [(i/n_layer)**(1/factor) for i in range(n_layer+1)]
		LayerRatio= np.array(LayerRatio)

		self.hidden_size=list((w_s-rep_dim)*LayerRatio+rep_dim)
		self.hidden_size= np.array(self.hidden_size,dtype=np.int32)[::-1]

		#Encoder
		self.hidden_size=self.hidden_size[::-1]
		act_verbose = act_verbose[:n_layer-1]
		act_verbose=act_verbose[::-1]
		self.decs= []
		self.decs+= [nn.Sequential(nn.BatchNorm1d(self.rep_dim),nn.LeakyReLU())]
		for i in range(len(self.hidden_size)-2):
			self.decs+= [block(self.hidden_size[i], self.hidden_size[i+1], n_w, act=act_verbose[i], dropout=dropout)]
		self.decs+=[block(self.hidden_size[-2], self.hidden_size[-1], n_w, act=None, dropout=0)]
		self.decs = nn.Sequential(*self.decs)


	def forward(self,x):
		x = self.decs(x)
		return x


class A_Encoder(nn.Module):
	def __init__(self, n_w=1, w_s=224, n_layer=2, rep_dim=32, w_rep_dim=32, dropout=0, act_verbose=[1,1,1]):
		"""
			Aggregate Encoder
			Parameters
				- n_band (int): the number of band
				- w_s (int): window size
				- n_layer (int): the number of aggregate layer
				- rep_dim (int): the representation dimension
				- w_rep_dim (int): the representation dimension after partial encoder
				- dropout (float): dropout ratio
				- act_verbose (list): relu culling location
		"""
		super().__init__()

		diff = (w_rep_dim*n_w- rep_dim )/ n_layer
		self.hidden_size = [w_rep_dim*n_w] +[int(w_rep_dim*n_w-diff*(i+1)) for i in range(n_layer-1)] + [rep_dim]

		self.ag_enc =[]
		for i in range(len(self.hidden_size)-2):
			self.ag_enc += [block(self.hidden_size[i], self.hidden_size[i+1], 1, act=act_verbose[i-n_layer+1])]
		self.ag_enc+= [block(self.hidden_size[-2], self.hidden_size[-1], 1, act=None)]
		self.ag_enc= nn.Sequential(*self.ag_enc)

	def forward(self, x):
		x = self.ag_enc(x)
		return x

class A_Decoder(nn.Module):
	def __init__(self, n_w=1, w_s=224, n_layer=2, rep_dim=32, w_rep_dim=32, dropout=0, act_verbose=[1,1,1]):
		"""
			Aggregate Encoder
			Parameters
				- n_band (int): the number of band
				- w_s (int): window size
				- n_layer (int): the number of aggregate layer
				- rep_dim (int): the representation dimension
				- w_rep_dim (int): the representation dimension after partial encoder
				- dropout (float): dropout ratio
				- act_verbose (list): relu culling location
		"""
		super().__init__()
		diff = (w_rep_dim*n_w- rep_dim )/ n_layer
		hidden_size = [w_rep_dim*n_w] +[int(w_rep_dim*n_w-diff*(i+1)) for i in range(n_layer-1)] + [rep_dim]

		self.ag_dec=[]

		hidden_size=hidden_size[::-1]
		act_verbose = act_verbose[n_layer-1:]
		act_verbose=act_verbose[::-1]
		for i in range(len(hidden_size)-2):
			self.ag_dec+= [block(hidden_size[i], hidden_size[i+1], 1, act=act_verbose[i])]
		self.ag_dec+= [block(hidden_size[-2], hidden_size[-1], 1, act=None)]

		self.ag_dec= nn.Sequential(*self.ag_dec)

	def forward(self, x):
		x = self.ag_dec(x)
		return x

"""
Spectral Dense [CNN]
"""
class Spectral_Dense(nn.Module):
    def __init__(self, ic, oc, k, s, padding):
        super().__init__()
        self.ic = ic
        self.oc = oc
        self.k = k
        self.s = s
        if padding == "valid":
            self.p = 0
        elif padding == "same":
            self.p = 3
        self.layer = nn.Sequential(
            nn.BatchNorm3d(self.ic),
            nn.ReLU(),
            nn.Conv3d(self.ic, self.oc, (self.k,1,1), stride=(self.s,1,1), padding=(self.p,0,0)),
        )

    def forward(self, x):
        x1 = self.layer(x)
        return torch.cat([x, x1], dim=1)

"""
Spatial Dense [CNN]
"""
class Spatial_Dense(nn.Module):
    def __init__(self, ic, oc, k, s, padding):
        super().__init__()
        self.ic = ic
        self.oc = oc
        self.k = k
        self.s = s
        if padding == "valid":
            self.p = 0
        elif padding == "same":
            self.p = 1
        self.layer = nn.Sequential(
            nn.BatchNorm3d(self.ic),
            nn.ReLU(),
            nn.Conv3d(self.ic, self.oc, (1, self.k,self.k), stride=(1,self.s,self.s), padding=(0,self.p,self.p)),
        )

    def forward(self, x):
        x1 = self.layer(x)
        return torch.cat([x, x1], dim=1)

"""
Spectral Enhance [CNN]
"""
class Spectral_Enhance(nn.Module):
    def __init__(self, rep_dim, patch_size, r, dropout=0.5):
        super().__init__()
        self.rep_dim =rep_dim
        self.patch_size = patch_size
        self.r = r
        self.conv1 = nn.Conv2d(self.rep_dim, 1,1,1)
        self.LayerNorm = nn.Sequential(
            nn.Conv2d(rep_dim,int(rep_dim/r),1,1),
            nn.Dropout(dropout),
            nn.LayerNorm([int(rep_dim/r),1,1]),
            nn.ReLU(),
            nn.Conv2d(int(rep_dim/r),rep_dim,1,1),
        )
        self.soft = nn.Softmax(-1)


    def forward(self, x):
        soft_x = self.conv1(x).view(-1,1,1,self.patch_size*self.patch_size)
        soft_x = self.soft(soft_x).view(-1,1,self.patch_size*self.patch_size)

        trans_x = x.view(-1, self.patch_size*self.patch_size, self.rep_dim)

        gc = torch.bmm(soft_x , trans_x)
        
        gc = gc.view(-1, self.rep_dim, 1, 1)
        gc = self.LayerNorm(gc).expand(-1,self.rep_dim,self.patch_size,self.patch_size)
        gc = gc+ x
        return gc

"""
Spatial Enhance [CNN]
"""
class Spatial_Enhance(nn.Module):
    def __init__(self, rep_dim, patch_size, r, dropout=0.5):
        super().__init__()
        self.rep_dim =rep_dim
        self.patch_size = patch_size
        self.r = r
        self.g_avg = nn.AdaptiveAvgPool2d(1)
        self.LayerNorm = nn.Sequential(
            nn.Conv2d(self.patch_size*self.patch_size,int((self.patch_size*self.patch_size)/r),1,1),
            nn.Dropout(dropout),
            nn.LayerNorm([int((self.patch_size*self.patch_size)/r),1,1]),
            nn.ReLU(),
            nn.Conv2d(int((self.patch_size*self.patch_size)/r),self.patch_size*self.patch_size,1,1),
        )
        self.soft = nn.Softmax(-1)

    def forward(self, x):
        soft_x = self.g_avg(x).view(-1,1,1,self.rep_dim)
        soft_x = self.soft(soft_x).view(-1,1,self.rep_dim)

        trans_x = x.view(-1, self.patch_size*self.patch_size, self.rep_dim)
        trans_x = trans_x.permute(0,2,1)
        
        gc = torch.bmm(soft_x , trans_x)
        
        gc = gc.view(-1,self.patch_size*self.patch_size, 1,1)
        gc = self.LayerNorm(gc).view(-1,1,self.patch_size,self.patch_size)
        gc = gc + x
        return gc