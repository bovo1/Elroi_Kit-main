"""
    Elroi Kit

    Copyright 2025. Elroilab All rights reserved.
"""

import numpy as np

from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA


# Smoothing Filter
def setSavitzkyGolay(spectralData):
    """
        @description : Apply Savitzky-Golay Filter
        @author : GaEun Hwang
    """
    # The parameter values of the Savitzky-Golay filter were referenced from a paper using a hyperspectral dataset
    filteredData = savgol_filter(spectralData, window_length=11, polyorder=3)

    return filteredData

def setGaussian(spectralData):
    """
        @description : Apply Gaussian Filter
        @author : GaEun Hwang
    """
    # The sigma of the Gaussian filter was set to 2.5 after testing values ​​from 1.0 to 3.0
    filteredData = gaussian_filter1d(spectralData, sigma=2.5)

    return filteredData

# LDA
def setLDA(rawData, labelData):
    """
        @description : Apply LDA
        @author : GaEun Hwang
    """
    labelIndice = np.nonzero(labelData)
    labels = labelData[labelIndice]
    spectralData = rawData[labelIndice]
    scaler = StandardScaler()
    scaledData = scaler.fit_transform(spectralData)

    # solver, shrinkage, covariance_estimator are LDA options that can change the results significantly.
    # shrinkage, covariance_estimator is make data stable
    # the purpose of LDA graph is to show outlier data like mislabeling.
    # therefore, we do not use shrinkage or covariance_estimator.
    # use 'svd' solver. not 'lsqr'/'eigen' because 'lsqr'/'eigen' is covariance based.
    # store_covariance=True, because it can be used elsewhere.

    model = LDA(solver='svd', store_covariance=True)
    ldaData = model.fit_transform(scaledData, labels)

    return ldaData, scaler, model
