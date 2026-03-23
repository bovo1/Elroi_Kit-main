import copy
import torch
import torch.nn as nn
from typing import Optional, cast
from torch.nn.utils import fuse_conv_bn_eval, fuse_linear_bn_eval


def _has_normalization(module: nn.Module) -> bool:
    """
        description : Check if the module contains a normalization layer.
        author : ChanSik Kim (2026.03.18)
    """
    return any(child.__class__.__name__ == "Normalization" for child in module.modules())


def _has_leading_scaling(module: nn.Module) -> bool:
    """
        description : Check if the top-most layer is a Scaling layer (either directly in a Sequential,
                      or in the `.encoder` Sequential of a wrapper module).
        author : ChanSik Kim (2026.03.20)
    """
    if isinstance(module, nn.Sequential):
        first = next(iter(module.children()), None)
        return first is not None and type(first).__name__ == "Scaling"

    encoder = getattr(module, "encoder", None)
    if isinstance(encoder, nn.Sequential):
        first = next(iter(encoder.children()), None)
        return first is not None and type(first).__name__ == "Scaling"

    return False


def make_full_optimized_model(model: nn.Module) -> nn.Module:
    """
        description : Create a fully optimized model by folding batch normalization layers and removing scaling layers.
        author : ChanSik Kim (2026.03.18)
    """
    m = copy.deepcopy(model)
    m.eval()
    encoder = cast(nn.Module, m.encoder)
    m.encoder = fold_bn_inplace(encoder)
    has_norm = _has_normalization(cast(nn.Module, m.encoder))
    had_leading_scaling = _has_leading_scaling(cast(nn.Module, m.encoder))
    m.encoder = remove_scaling_completely(cast(nn.Module, m.encoder))
    if (not has_norm) and had_leading_scaling:
        bake_scaling_into_first_affine(cast(nn.Module, m.encoder), 4095.0)
    return m.eval()


def bake_scaling_into_first_affine(module: nn.Module, divide: float = 4095.0):
    """
        description : Bake scaling into the first affine layer (nn.Linear or nn.Conv2d) by dividing its weights by the specified factor.
                      Here, "bake scaling" means removing an explicit input Scaling layer and absorbing the same effect
                      directly into the first affine layer's weights.
        author : ChanSik Kim (2026.03.18)
    """
    affine = find_first_affine(module)
    if affine is None:
        raise RuntimeError("No affine layer (nn.Linear or nn.Conv2d) found in the model to bake scaling into.")

    with torch.no_grad():
        # Absorb x / divide into the first affine layer so the separate Scaling layer is no longer needed.
        affine.weight.div_(divide)


def find_first_affine(module: nn.Module):
    """
        description : Find the first affine layer (nn.Linear or nn.Conv2d) in the module.
        author : ChanSik Kim (2026.03.18)
    """
    if isinstance(module, (nn.Linear, nn.Conv2d)):
        return module
    for child in module.children():
        found = find_first_affine(child)
        if found is not None:
            return found
    return None


def _get_fusable_pair_kind(first: nn.Module, second: nn.Module) -> Optional[str]:
    """
        description : Identify whether the given pair can be fused.
        author : ChanSik Kim (2026.03.20)
    """
    if isinstance(first, nn.Linear) and isinstance(second, nn.BatchNorm1d):
        return "linear"
    if isinstance(first, nn.Conv2d) and isinstance(second, nn.BatchNorm2d):
        return "conv2d"
    return None


def _fuse_pair(first: nn.Module, second: nn.Module) -> nn.Module:
    """
        description : Fuse the given pair of layers (Linear + BN1d or Conv2d + BN2d) into a single layer.
        author : ChanSik Kim (2026.03.18)
    """
    pair_kind = _get_fusable_pair_kind(first, second)

    if pair_kind == "linear":
        return fuse_linear_bn_eval(cast(nn.Linear, first), cast(nn.BatchNorm1d, second))

    if pair_kind == "conv2d":
        return fuse_conv_bn_eval(cast(nn.Conv2d, first), cast(nn.BatchNorm2d, second))

    raise TypeError(
        f"Unsupported fuse pair: {type(first).__name__} + {type(second).__name__}"
    )


def fold_bn_inplace(module: nn.Module) -> nn.Module:
    """    
        description : Recursively fold batch normalization layers into preceding affine layers (Linear or Conv2d) within the given module.
        author : ChanSik Kim (2026.03.18)
    """
    module.eval()

    # 1. Recursively search and modify child modules
    for name, child in list(module.named_children()):
        setattr(module, name, fold_bn_inplace(child))

    # 2. Fuse adjacent (Linear/Conv2d) + BN patterns within Sequential
    if isinstance(module, nn.Sequential):
        layers = list(module.children())
        new_layers = []
        i = 0

        while i < len(layers):
            if i + 1 < len(layers) and _get_fusable_pair_kind(layers[i], layers[i + 1]) is not None:
                fused = _fuse_pair(layers[i], layers[i + 1])
                new_layers.append(fused)
                i += 2
            else:
                new_layers.append(layers[i])
                i += 1

        module = nn.Sequential(*new_layers)
    return module


def _strip_leading_scaling_from_sequential(seq: nn.Sequential) -> nn.Sequential:
    layers = list(seq.children())
    while layers and type(layers[0]).__name__ == "Scaling":
        layers.pop(0)
    new_seq = nn.Sequential(*layers)
    new_seq.eval()
    return new_seq


def remove_scaling_completely(module: nn.Module) -> nn.Module:
    """
        description : Remove only the leading(top-most) Scaling layer if present.
        author : ChanSik Kim (2026.03.18)
    """
    module = copy.deepcopy(module)
    module.eval()

    # If the module itself is a Sequential, strip only the leading Scaling.
    if isinstance(module, nn.Sequential):
        return _strip_leading_scaling_from_sequential(module)

    # Common pattern: wrapper module with `.encoder` being an nn.Sequential
    encoder = getattr(module, "encoder", None)
    if isinstance(encoder, nn.Sequential):
        module.encoder = _strip_leading_scaling_from_sequential(encoder)

    return module
