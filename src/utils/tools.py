import os
import spectral
import numpy as np
from multiprocessing.process import BaseProcess
import multiprocessing

class HSI():
    def __init__(self, path) -> None:
        self.raw_envi = spectral.io.envi.open(os.path.join(path, "data.hdr"), os.path.join(path, "data.raw")).load()
        self.raw_array = np.array(self.raw_envi)

        self.white_array = np.array(spectral.io.envi.open(os.path.join(path, "WHITEREF.hdr"), os.path.join(path, "WHITEREF.raw")).load()).mean(0)
        self.dark_array = np.array(spectral.io.envi.open(os.path.join(path, "DARKREF.hdr"), os.path.join(path, "DARKREF.raw")).load()).mean(0)

    def get_metadata(self):
        return self.raw_envi.metadata

    def get_image(self, rgb:bool=True, bands:list=None, calibration:bool=True, calibration_rate:float=1.0, normalization:bool=False):
        try:
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
        except:
            print("Failed to load HSI image")
            return None

def stopMultiprocess(process):
    """
        description: Terminate a multiprocessing process gracefully, and force kill if it does not terminate within the timeout.
        author: Hyunsu Kim (2026.05.12)
        History
            1. Modified by Hyunsu Kim (2026.05.12): Added kill function if process does not terminate within the timeout
    """
    if not isinstance(process, BaseProcess):
        return

    if not process.is_alive():
        return

    try:
        process.terminate()
        process.join(3000 / 1000)
        if (process.is_alive()):
            process.kill()
    except Exception as exc:
        print(f"Failed to terminate process: {exc}")

def shutdownRunningProcesses():
    """
        description: Shutdown all running background processes when main window is closed
        author: Hyunsu Kim (2026.05.12)
        History
            1. Modified by Hyunsu Kim (2026.05.12): Use active_children() to get all running child processes
    """

    for process in multiprocessing.active_children():
        stopMultiprocess(process)
