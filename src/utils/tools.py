import os
import spectral
import numpy as np

class HSI():
    def __init__(self, path) -> None:
        self.raw_envi = spectral.io.envi.open(os.path.join(path, "data.hdr"), os.path.join(path, "data.raw")).load()
        self.raw_array = np.array(self.raw_envi)

        self.white_array = np.array(spectral.io.envi.open(os.path.join(path, "WHITEREF.hdr"), os.path.join(path, "WHITEREF.raw")).load()).mean(0)
        self.dark_array = np.array(spectral.io.envi.open(os.path.join(path, "DARKREF.hdr"), os.path.join(path, "DARKREF.raw")).load()).mean(0)

    def get_metadata(self):
        return self.raw_envi.metadata

    def get_image(self, rgb:bool=True, bands:list=None, calibration:bool=True, calibration_rate:float=1.0, normalization:bool=False):
        data = self.raw_array
        if calibration:
            data = np.clip((data-self.dark_array)/(self.white_array-self.dark_array), 0, 1.0)
            data = data*calibration_rate

        if normalization:
            data = data / np.linalg.norm(data, ord=2, axis=-1, keepdims=True) # unit vectorization

        if rgb:
            data = ((data*255)**1.65 if normalization else data*255).astype(np.uint8) # convert to uint8 type with gamma correction
            if bands:
                return np.copy(data[:, :, bands])
            else:
                return np.copy(data[:, :, list(map(int, self.raw_envi.metadata["default band"]))])
        else:
            return data