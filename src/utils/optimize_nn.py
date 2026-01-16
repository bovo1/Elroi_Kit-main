"""
	ElroiLab Template Code
	Copyright 2024. Elroilab All rights reserved.

	@description: Partial and aggregate autoencoder
	@author: JungiLee
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils import prune


def prunetolinear(layer):
    """
    Convert a pruned linear layer to a standard linear layer
    Args:
        layer: The pruned linear layer to convert
    Returns:
        A standard linear layer with the pruned weights applied
    """
    #Pruned linear to linear transform
    if isinstance(layer, nn.Linear) and hasattr(layer, 'weight_mask'):
        device=next(layer.parameters()).device
        linear = torch.nn.Linear(
            layer.in_features,
            layer.out_features,
            bias=True
        )
        with torch.no_grad():
            linear.weight.copy_(layer.weight_orig*layer.weight_mask)
            linear.bias.copy_(layer.bias)
        layer=linear.to(device)
    return layer


def fuse_linear_and_linear(linear1, linear2):
    """
    Fuse two consecutive linear layers into a single linear layer
    Args:
        linear1: First linear layer
        linear2: Second linear layer
    Returns:
        A single linear layer equivalent to the two input layers
    """
    #Layer fusion: linear + linear = linear
    device=next(linear1.parameters()).device

    linear1=linear1.cpu()
    linear2=linear2.cpu()

    linear1=prunetolinear(linear1)
    linear2=prunetolinear(linear2)

    fusedlinear = torch.nn.Linear(
        linear1.in_features,
        linear2.out_features,
        bias=True
    )
    w_linear = linear1.weight.clone().view(linear1.out_features, -1).cpu()
    b_linear = linear1.bias.clone().view(linear1.out_features,-1).cpu()

    w_linear2 = linear2.weight.clone().view(linear2.out_features, -1).cpu()
    b_linear2 = linear2.bias.clone().view(linear2.out_features,-1).cpu()
    with torch.no_grad():
        w = torch.mm(w_linear2,w_linear)
        b = torch.mm(w_linear2,b_linear)+b_linear2
        b = b.view(-1)

        fusedlinear.weight.copy_(w)
        fusedlinear.bias.copy_(b)
    return fusedlinear.to(device)


def fuse_linear_and_bn(linear, bn):
    """
    Fuse a linear layer followed by batch normalization into a single linear layer
    Args:
        linear: Linear layer
        bn: Batch normalization layer
    Returns:
        A single linear layer equivalent to linear+bn
    """
    #Layer fusion: linear + BatchNorm = linear
    device=next(linear.parameters()).device

    linear=prunetolinear(linear)
    linear = linear.cpu()
    bn = bn.cpu()
    fusedlinear = torch.nn.Linear(
        linear.in_features,
        linear.out_features,
        bias=True
    )

    if bn.weight==None:
        with torch.no_grad():
            bn.weight=torch.nn.Parameter(torch.ones_like(bn.running_mean))
    if bn.bias==None:
        with torch.no_grad():
            bn.bias=torch.nn.Parameter(torch.zeros_like(bn.running_mean))
    weight, bias=torch.nn.utils.fusion.fuse_linear_bn_weights(linear.weight, linear.bias, bn.running_mean, bn.running_var, bn.eps, bn.weight, bn.bias)
    with torch.no_grad():
        fusedlinear.weight.copy_(weight)
        fusedlinear.bias.copy_(bias)
    return fusedlinear.to(device)


def fuse_bn_and_linear(bn, linear):
    """
    Fuse a batch normalization layer followed by linear layer into a single linear layer
    Args:
        bn: Batch normalization layer
        linear: Linear layer
    Returns:
        A single linear layer equivalent to bn+linear
    """
    #Layer fusion: BatchNorm + Linear = linear
    device=next(linear.parameters()).device
    linear=prunetolinear(linear)
    fusedlinear = torch.nn.Linear(
        linear.in_features,
        linear.out_features,
        bias=True
    )

    w_linear = linear.weight.clone().view(linear.out_features, -1).to(device)
    w_bn = torch.diag(bn.weight.div(torch.sqrt(bn.eps+bn.running_var)))

    with torch.no_grad():
        fusedlinear.weight.copy_(torch.mm(w_linear, w_bn).view(fusedlinear.weight.size()) )

        if linear.bias is not None:
            b_linear= linear.bias
        else:
            b_linear= torch.zeros( linear.weight.size(0) )
        b_bn = bn.bias - torch.matmul(w_bn,bn.running_mean)
        b_bn = torch.matmul(b_bn, w_linear.T)
        fusedlinear.bias.copy_(b_linear+b_bn)
    return fusedlinear.to(device)


def optimizeLinear(modules):
    """
    Optimize a sequence of layers by fusing consecutive linear and batch norm layers
    Args:
        modules: Sequential module containing layers to optimize
    Returns:
        Optimized sequential module with fused layers
    """
    fuse_layer =None
    layer_list=[]
    for i, layer in enumerate(modules):
        if i<=2:
            # Exclude the Scaling, Flatten, first linear layer from layer fusion
            if isinstance(layer, nn.Linear):
                device=next(layer.parameters()).device
                linear = torch.nn.Linear(
                    layer.in_features,
                    layer.out_features,
                    bias=True
                )
                with torch.no_grad():
                    linear.weight.copy_(layer.weight_orig*layer.weight_mask)
                    linear.bias.copy_(layer.bias)
                layer = linear.to(device)
            layer_list.append(layer)
        else:
            if fuse_layer==None:
                fuse_layer = layer
            elif isinstance(fuse_layer, nn.Linear) and isinstance(layer, nn.BatchNorm1d):
                fuse_layer = fuse_linear_and_bn(fuse_layer, layer)
            elif isinstance(fuse_layer, nn.Linear) and isinstance(layer, nn.Linear):
                fuse_layer = fuse_linear_and_linear(fuse_layer, layer)
            elif isinstance(fuse_layer, nn.BatchNorm1d) and isinstance(layer, nn.Linear):
                fuse_layer = fuse_bn_and_linear(fuse_layer, layer)
            else:
                layer_list.append(fuse_layer)
                fuse_layer=layer
    if fuse_layer !=None:
        layer_list.append(fuse_layer)
    return nn.Sequential(*layer_list)


def Optimize(modules, n_band, n_w, w_s, s):
    """
    Optimize a neural network module by removing dropout layers and fusing consecutive layers
    Args:
        modules: Neural network module to optimize
        n_band: Number of bands
        n_w: Number of windows
        w_s: Window size
        s: Stride
    Returns:
        Optimized neural network module
    """
    device=next(modules.parameters()).device
    module=[]

    # Serialization layers without Dropout
    for i, enc in enumerate(modules.encoder.encoder):
        if i<2 and isinstance(enc, nn.Module):
            module.append(enc)
            continue

        for layer in enc.children():
            if isinstance(layer, nn.Dropout):
                pass
            else:
                module.append(layer)

    for enc in modules.ag_enc.ag_enc:
        for layer in enc.children():
            if isinstance(layer, nn.Dropout):
                pass
            else:
                module.append(layer)
    return optimizeLinear(module)
