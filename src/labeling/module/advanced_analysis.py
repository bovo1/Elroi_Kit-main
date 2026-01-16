"""
    Elroi Kit

    Copyright 2025. Elroilab All rights reserved.
"""

import numpy as np
import copy
import pyqtgraph as pg

from .graph_adv_option import setLDA
from utils.custom_item import customScatterItem

class visualizerLDA:
    """
        @description : Visualizer LDA results
        @author : GaEun Hwang (2025.08.29)
    """
    def __init__(self):
        self.ldaData = None
        self.ldaScaler = None
        self.ldaModel = None
        self.defaultSettings = {
            'size': 10,
            'pen': None,
            'brush': (0,0,0),
            'hoverable': True,
            'hoverPen': (0,0,0)
        }
    
    def fitModel(self, rawData, labelData):
        """
            @description : fit LDA model
            @author : GaEun Hwang (2025.08.29)
        """
        self.ldaData, self.ldaScaler, self.ldaModel = setLDA(rawData, labelData)
        
        return self.ldaData, self.ldaScaler, self.ldaModel
    
    def transformSpectralData(self, spectralData):
        """
            @description : transform spectralData to plot as LDA item
            @author : GaEun Hwang (2025.08.29)
        """
        if self.ldaScaler is not None and self.ldaModel is not None:
            # reshape to (sample, feature)
            reshapedSpectralData = spectralData.reshape(1,-1)
            scaledSpectralData = self.ldaScaler.transform(reshapedSpectralData)
            modelOutSpectralData = self.ldaModel.transform(scaledSpectralData)

            return modelOutSpectralData

    def makePlotItem(self, ldaData, **kwargs):
        """
            @description : make ldaData to plot as scatteritem
            @author : GaEun Hwang (2025.08.29)
        """
        plotSettings = copy.deepcopy(self.defaultSettings)
        # kwargs is keyword arguments to update plotSettings like brush, pen, size, hoverable, hoverPen etc.
        plotSettings.update(kwargs)
        plotSettings['brush'] = pg.mkBrush(plotSettings.get('brush'))
        plotSettings['pen'] = pg.mkPen(plotSettings.get('pen'))
        scatterItem = customScatterItem(x=[ldaData[0,0]], y=[ldaData[0,1]], **plotSettings)

        return scatterItem

    def makePlotItems(self, ldaData, labelData, labelInfoDict, **kwargs):
        """
            @description : make a lot of ldaData to plot as scatteritem
            @author : GaEun Hwang (2025.08.29)
        """
        labelIndices = np.nonzero(labelData)
        labels = labelData[labelIndices]
        scatterItems = []
        basePlotSettings = copy.deepcopy(self.defaultSettings)
        basePlotSettings.update(kwargs)

        if labelInfoDict is not None:
            for labelNum, labelValue in labelInfoDict.items():
                # proceed only if label number is not 0
                if labelNum != 0:
                    tmpPlotSettings = {}
                    # extract the same value as labelNum from ldaData and designate it as classData
                    # classData shape (n_samples, n_features)
                    classData = ldaData[labels == labelNum]
                    # for 2D plot, use the first, second LDA components. use classData[:, 0], classData[:, 1]
                    # reason is the most important axis in classifying classes.
                    xData, yData = classData[:, 0], classData[:, 1]
                    # when hoverable is True, make coordinates data for hover tooltip.
                    if basePlotSettings['hoverable']:
                        yCoord, xCoord = labelIndices[1][labels == labelNum], labelIndices[0][labels == labelNum]
                        tmpPlotSettings['data'] = [f"({y}, {x})" for x, y in zip(xCoord, yCoord)]
                    tmpPlotSettings['name'] = labelValue['label_name']
                    tmpPlotSettings['brush'] = pg.mkBrush(*labelValue['label_color'])
                    # merge plot settings use | operator (Python 3.9+)
                    plotSettings = basePlotSettings | tmpPlotSettings
                    scatterItem = customScatterItem(x=xData, y=yData, **plotSettings)
                    scatterItems.append(scatterItem)

        return scatterItems