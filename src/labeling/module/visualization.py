import os
import torch
import cv2
import numpy as np
import json

from bisect import bisect
from scipy.interpolate import PchipInterpolator, interp1d
from utils.encrypt import AesEncryption
from utils.shared import resource_path

aes = AesEncryption()
def DLRGB(HSI_data, HSI_wave_length, sharpening=True, model_path=os.path.join(resource_path, "visualization/View_2_Weight.el")):
    HSI_data = (HSI_data-HSI_data.min())/(HSI_data.max()-HSI_data.min()) # min-max scaling
    model = torch.nn.Sequential(
        torch.nn.Linear(31, 16),
        torch.nn.BatchNorm1d(16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 8),
        torch.nn.BatchNorm1d(8),
        torch.nn.ReLU(),
        torch.nn.Linear(8, 3),
        torch.nn.Sigmoid() # zero to one mapping
    )
    script_model = torch.jit.load(aes.make_water(model_path, _type="model"))
    model.load_state_dict(script_model.state_dict())
    model.eval()
    HSI_wave_length[0] = 400.00 # for stable interpolation range
    height, width, channel = HSI_data.shape
    HSI_data = HSI_data.reshape(-1, channel)
    HSI_data = interp1d(HSI_wave_length, HSI_data)(np.linspace(400, 700, 31))

    image = (np.power(model(torch.from_numpy(HSI_data.copy()).type(torch.float32)).detach().numpy(), 1/1.2)*255).astype(np.uint8)
    image = image.reshape(height, width, 3)
    
    # sharpening filter
    if sharpening:
        kernel_sharpening = np.array(
            [[0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]]
        )
        image = cv2.filter2D(image, -1, kernel_sharpening)
    return image


def CMFRGB(HSI_data, HSI_wave_length, wxyz_path = os.path.join(resource_path, "visualization/View_1_Mat.el"), D_path = os.path.join(resource_path, "visualization/View_2_Mat.el"), d=65, threshold=0.002):
    HSI_data = (HSI_data-HSI_data.min())/(HSI_data.max()-HSI_data.min()) # min-max scaling
    wxyz = aes.make_water(wxyz_path, _type="mat")
    wxyz = np.array(json.loads(wxyz))
    D = aes.make_water(D_path, _type="mat")
    D = np.array(json.loads(D))
    height, width, channel = HSI_data.shape
    HSI_data = HSI_data.reshape(-1, channel)

    w,x,y,z = wxyz[:,0], wxyz[:,1], wxyz[:,2], wxyz[:,3]

    i = {50:2, 55:3, 65:1, 75:4}
    wI = D[:, 0]
    I = D[:, i[d]]
        
    # Interpolate to image wavelengths
    I = PchipInterpolator(wI, I, extrapolate=True)(HSI_wave_length)
    x = PchipInterpolator(w, x, extrapolate=True)(HSI_wave_length)
    y = PchipInterpolator(w, y, extrapolate=True)(HSI_wave_length)
    z = PchipInterpolator(w, z, extrapolate=True)(HSI_wave_length)

    # Truncate at 780nm
    i = bisect(HSI_wave_length, 780)
    HSI_data = HSI_data[:, 0:i]
    HSI_wave_length = HSI_wave_length[:i]
    I = I[:i]
    x = x[:i]
    y = y[:i]
    z = z[:i]
    
    # Compute k
    k = 1/np.trapz(y * I, HSI_wave_length)
    
    # Compute X,Y & Z for image
    X = k * np.trapz(HSI_data @ np.diag(I * x), HSI_wave_length, axis=1)
    Z = k * np.trapz(HSI_data @ np.diag(I * z), HSI_wave_length, axis=1)
    Y = k * np.trapz(HSI_data @ np.diag(I * y), HSI_wave_length, axis=1)
    
    XYZ = np.array([X, Y, Z])
    
    # Convert to RGB
    M = np.array([[3.2404542, -1.5371385, -0.4985314],
                  [-0.9692660, 1.8760108, 0.0415560],
                  [0.0556434, -0.2040259, 1.0572252]])
    sRGB=M@XYZ
    
    # Gamma correction
    gamma_map = sRGB >  0.0031308
    sRGB[gamma_map] = 1.055 * np.power(sRGB[gamma_map], (1. / 2.4)) - 0.055
    sRGB[np.invert(gamma_map)] = 12.92 * sRGB[np.invert(gamma_map)]

    # Note: RL, GL or BL values less than 0 or greater than 1 are clipped to 0 and 1.
    sRGB[sRGB > 1] = 1
    sRGB[sRGB < 0] = 0
    
    if threshold:
        for idx in range(3):
            y = sRGB[idx,:]
            a, b = np.histogram(y, 100)
            b = b[:-1] + np.diff(b)/2
            a = np.cumsum(a)/np.sum(a)
            th = b[0]
            i = a<threshold
            if i.any():
                th = b[i][-1]
            y = y-th
            y[y<0] = 0

            a, b = np.histogram(y, 100)
            b = b[:-1] + np.diff(b)/2
            a = np.cumsum(a)/np.sum(a)
            i = a > 1-threshold
            th = b[i][0]
            y[y>th] = th
            y = y/th
            sRGB[idx, :] = y

    R = np.reshape(sRGB[0,:], [height, width])
    G = np.reshape(sRGB[1,:], [height, width])
    B = np.reshape(sRGB[2,:], [height, width])

    return (np.transpose(np.array([R, G, B]),[1, 2, 0])*255).astype(np.uint8).copy()