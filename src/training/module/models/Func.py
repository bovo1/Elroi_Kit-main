import math
import torch
import torch.nn as nn
from torch.nn.utils import prune
from utils.optimize_nn import fuse_linear_and_linear


def mlp_block(in_size, out_size, relu=0.01, activation=True):
    if activation:
        return nn.Sequential(
            nn.Linear(in_size, out_size),
            nn.BatchNorm1d(out_size),
            nn.LeakyReLU(relu)
        )
    else:
        return nn.Sequential(
            nn.Linear(in_size, out_size)
        )


def encoder_conv_block(in_size, out_size, kernel_size=1, stride_size=1, padding_size=0, relu=0.01, activation=True):
    if activation:
        return nn.Sequential(
            nn.Conv2d(in_size, out_size, kernel_size, stride_size, padding_size),
            nn.BatchNorm2d(out_size),
            nn.LeakyReLU(relu)
        )
    else:
        return nn.Sequential(
            nn.Conv2d(in_size, out_size, kernel_size, stride_size, padding_size)
        )


def decoder_conv_block(in_size, out_size, kernel_size=1, stride_size=1, padding_size=0, relu=0.01, activation=True):
    if activation:
        return nn.Sequential(
            nn.ConvTranspose2d(in_size, out_size, kernel_size, stride_size, padding_size),
            nn.BatchNorm2d(out_size),
            nn.LeakyReLU(relu)
        )
    else:
        return nn.Sequential(
            nn.ConvTranspose2d(in_size, out_size, kernel_size, stride_size, padding_size)
        )


def group_conv_block(in_size, out_size, num_windows=1, relu=0.01, activation=True):
    if activation:
        return nn.Sequential(
            nn.Conv1d(in_size, out_size, kernel_size=1, groups=num_windows),
            nn.BatchNorm1d(out_size),
            nn.LeakyReLU(relu),
        )
    else:
        return nn.Sequential(
            nn.Conv1d(in_size, out_size, kernel_size=1, groups=num_windows),
        )
    

def kaiming(linear, fan_in=None):
	"""
		linear kaiming initialization
		- linear (nn.Linear): fully connected layer
		- fan_in (int): fan in size (in_features) if None calculate by the weight of linear
	"""
	weight = linear.weight
	bias= linear.bias
	a=math.sqrt(5)
	if fan_in==None:
		fan_in = nn.init._calculate_correct_fan(weight, "fan_in")
	gain = nn.init.calculate_gain("leaky_relu", a)
	std = gain / math.sqrt(fan_in)
	w_bound = math.sqrt(3.0) * std	# Calculate uniform bounds from standard deviation

	bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0

	with torch.no_grad():
		nn.init.uniform_(weight,-w_bound, w_bound)
		nn.init.uniform_(bias,-bound, bound)
		linear.weight.copy_(weight)
		linear.bias.copy_(bias)
            

def block(in_size, out_size, n_w=1, relu =0.01, act = True, dropout=0.0, pre_func=None):
	"""
		Model Block
		Parameters
			- in_size (int): input channel size
			- out_size (int): output channel size
			- n_w (int): the number of window
			- relu (float): relu gradient
			- act (bool): if act is false, return only linear layer.
			- dropout (float): dropout ratio
			- pre_func (nn.Linear): prefix function, it will be combined with linear layer
		Returns
			- Sequential nn.Module Block
	"""
	linear = nn.Linear(in_size*n_w, out_size*n_w, bias=True if act!= None else True)

	kaiming(linear, in_size)
	mask = torch.zeros((out_size*n_w, in_size*n_w))
	for i in range(n_w):
		mask[i*out_size:(i+1)*out_size,i*in_size:(i+1)*in_size]=1

	if pre_func !=None:
		linear=fuse_linear_and_linear(pre_func, linear)
		mask = torch.matmul(mask, pre_func.weight)

	linear=prune.custom_from_mask(linear,name='weight',mask=mask)

	if act==None:
		return nn.Sequential(
				linear
				)
	elif act == True:
		return nn.Sequential(
					linear,
					nn.BatchNorm1d(out_size*n_w),
					nn.LeakyReLU(relu),
					nn.Dropout(dropout)
				)
	elif act == False:
		return nn.Sequential(
					linear,
					nn.BatchNorm1d(out_size*n_w),
					nn.Dropout(dropout)
				)
	else:
		raise ValueError(f"Unexpected value: act {act}")
      