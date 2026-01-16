import torch
import torch.nn as nn
from .Module import P_Encoder, A_Encoder, P_Decoder, A_Decoder

class PA2Ev2(nn.Module):
	def __init__(self, n_band=224, n_w=1, w_s=224, s=0, n_layer=5, n_aglayer=2, rep_dim=32, w_rep_dim=32, dropout=0, act_verbose=[1,1,1], factor=0.5):
		"""
			Partial and Aggregate Autoencoder Model
			Parameters
				- n_band (int): the number of band
				- n_w (int): the number of window
				- w_s (int): window size
				- s (int): stride size
				- n_layer (int): the number of partial layer
				- n_aglayer (int): the number of aggregate layer
				- rep_dim (int): the representation dimension
				- w_rep_dim (int): the representation dimension after partial encoder
				- dropout (float): dropout ratio
				- act_verbose (list): relu culling location
				- factor (float): the parameter for hidden size between layers
		"""
		super().__init__()
		self.n_w=n_w
		self.w_s=w_s
		self.n_layer = n_layer
		self.rep_dim = rep_dim
		self.w_rep_dim = w_rep_dim
		self.n_layer = n_layer

		#Encoder
		self.encoder = P_Encoder(n_band, n_w, w_s, s, n_layer, w_rep_dim, dropout, act_verbose, factor)
		self.ag_enc= A_Encoder(n_w, w_s, n_aglayer, rep_dim, w_rep_dim, dropout, act_verbose)

		self.ag_dec= A_Decoder(n_w, w_s, n_aglayer, rep_dim, w_rep_dim, dropout, act_verbose)
		self.decoder = P_Decoder(n_w, w_s, n_layer, w_rep_dim, dropout, act_verbose, factor)


	def forward(self,x):
		zp = self.encoder(x)
		z = self.ag_enc(zp)

		zp_hat = self.ag_dec(z)
		x_hat = self.decoder(zp_hat)

		xp_hat = self.decoder(zp)
		return x_hat, xp_hat
	

class PA_Encoder(nn.Module):
	def __init__(self, n_band=224, n_w=1, w_s=224, s=0, n_layer=5, n_aglayer=2, rep_dim=32, w_rep_dim=32, dropout=0, act_verbose=[1,1,1], factor=0.5):
		"""
			Partial and Aggregate Encoder Model
			Parameters
				- n_band (int): the number of band
				- n_w (int): the number of window
				- w_s (int): window size
				- s (int): stride size
				- n_layer (int): the number of partial layer
				- n_aglayer (int): the number of aggregate layer
				- rep_dim (int): the representation dimension
				- w_rep_dim (int): the representation dimension after partial encoder
				- dropout (float): dropout ratio
				- act_verbose (list): relu culling location
				- factor (float): the parameter for hidden size between layers
		"""
		super().__init__()
		self.n_w=n_w
		self.w_s=w_s
		self.n_layer = n_layer
		self.n_aglayer= n_aglayer
		self.rep_dim = rep_dim
		self.w_rep_dim = w_rep_dim
		self.dropout=dropout
		self.act_verbose=act_verbose
		self.factor=factor
		self.fuse = False
		self.c = nn.Parameter(torch.zeros(self.rep_dim, requires_grad=False))

		#Encoder
		self.encoder = P_Encoder(n_band, n_w, w_s, s, n_layer, w_rep_dim, dropout, act_verbose, factor)

		#Aggregate Encoder
		self.ag_enc= A_Encoder(n_w, w_s, n_aglayer, rep_dim, w_rep_dim, dropout, act_verbose)

		self.decoder = P_Decoder(n_w, w_s, n_layer, w_rep_dim, dropout, act_verbose, factor)

	def forward(self,x, inference=False):
		zp = self.encoder(x)
		z = self.ag_enc(zp)
		xp_hat=None

		if inference==False:
			xp_hat = self.decoder(zp)

		return z, xp_hat


class PA2E_model(nn.Module):
    def __init__(self, model, center):
        super().__init__()
        self.model = model
        self.c = center
        self.fuse = True

    def forward(self, x):
        x = self.model(x)
        dist = torch.sum((x - self.c)**2, dim=1)
        return dist
