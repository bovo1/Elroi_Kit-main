import os
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from collections import deque
from core.sub_core_labeling import Sub_Core_Labeling

EIGHTDIR = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

class semiAutoLabeling:
    """
        Description: Algorithms and utilities for Semi Auto Labeling
        Parameters
            1. eps: Numerical stability constant
            2. maxSamples: Maximum number of samples for building endmember
            3. randomState: Random seed
            4. dirPath:Normal data directory path
        Author: Yugyeong Hong (2026.02.04)
    """
    
    def __init__(self, eps=1e-8, maxSamples=500000, randomState=0, dirPath=""):
        self.eps = eps
        self.maxSamples = maxSamples
        self.randomState = randomState
        self.dirPath = dirPath

    def sampleData(self, data):
        """
            Description: Sampling data for building endmember
            Author: Yugyeong Hong (2026.02.04)
        """
        numOfSamples = data.shape[0]
        if numOfSamples <= self.maxSamples:
            return data
        rng = np.random.default_rng(self.randomState)
        idx = rng.choice(numOfSamples, size=self.maxSamples, replace=False)
        return data[idx]
    
    def buildEndmember(self, dirPath, normalMaxClass=2, clusterK=8, pcaDim=6):
        """
            Description: Build Endmember and save as .npy
            Parameters
                1. dirPath: input data path
                2. normalMaxClass: maximum normal class id (default: 2)
                3. clusterK: number of KMeans clusters (default: 8)
                4. pcaDim: PCA dimension (default: 4)
            Author: Yugyeong Hong (2026.02.04)
        """
        tmp = {}
        try:
            dataPath, folderName = os.path.split(dirPath) # Split the directory path into dataPath and folderName to use load_data function

            _, label_data, hsi_data, _, \
                _, _, _, \
                    _, _, _ = Sub_Core_Labeling.load_data(self, path=dataPath, folder_name=folderName)
            
            normalMask = (label_data > 0) & (label_data <= normalMaxClass) & np.isfinite(hsi_data).all(axis=2)
            normalData=hsi_data[normalMask]
            normalData=self.sampleData(normalData)

            pca = PCA(n_components=pcaDim, random_state=self.randomState)
            normalPCA = pca.fit_transform(normalData)

            km = KMeans(n_clusters=clusterK, n_init=20, random_state=self.randomState).fit(normalPCA)
            centers = km.cluster_centers_
            kEndmember = pca.inverse_transform(centers)

            np.save(os.path.join(dirPath, "endmember.npy"), kEndmember)
            tmp['kEndmember'] = kEndmember
            tmp['status'] = "success"
        except Exception as e:
            tmp['status'] = e
            print(f"Error in buildEndmember: {e}")   
        return tmp
    
    def unitVec(self, normData, eps=1e-12):
        """
            Description: L2 normalization
            Parameter
                1. normData: (..., B)
            Author: Yugyeong Hong (2026.02.04)
        """
        normalization = np.linalg.norm(normData, axis=-1, keepdims=True) # Band axis normalization
        normData /= (normalization + eps)
        return normData

    def samAmap(self, dataVec, endmemberVec, eps=1e-12):
        """
            Description: Spectral Angle Mapper (SAM) calculation at once
                         This method computes the spectral angle between each pixel in the abnormal image data and each endmember, 
                         resulting in a similarity map (aMap) that indicates how closely each pixel matches the endmembers.
            Parameters
                1. dataVec: (width*height,Band)
                2. endmemberVec: (Number of Endmember K,Band)
                returns (M,K) angles
            Author: Yugyeong Hong (2026.02.04)
        """
        dataVec = self.unitVec(np.asarray(dataVec, dtype=np.float32), eps)
        endmemberVec = self.unitVec(np.asarray(endmemberVec, dtype=np.float32), eps)

        # Compute cosine via dot / matmul with broadcasting
        # u (...,B) @ v (...,B)^T -> handles (M,B)@(K,B).T and also vector cases
        cos = dataVec @ np.swapaxes(endmemberVec, -1, -2)

        cos = np.clip(cos, -1.0, 1.0)
        ang = np.arccos(cos).astype(np.float32, copy=False)
        return ang
    
    def samAngle(self, spectrum1, spectrum2, eps=1e-12):
        """
            Description: Spectral Angle Mapper (SAM) calculation
                         This method computes the spectral angle between two spectra, which is a measure of similarity.
            Parameters
                1. spectrum1: (1,B)
                2. spectrum2: (1,B)
            Author: Yugyeong Hong (2026.02.04)
        """
        spectrum1 = self.unitVec(np.asarray(spectrum1, dtype=np.float32), eps)
        spectrum2 = self.unitVec(np.asarray(spectrum2, dtype=np.float32), eps)
        cos = np.clip(np.dot(spectrum1,spectrum2), -1.0, 1.0)
        ang = np.arccos(cos)
        return ang


    def aMap(self, kEndmember, data, eps=1e-12):
        """
            Description: Spectral Angle Mapper calculation between an image data and Endmembers
            Parameters
                1. kEndmember: Endmembers(K, 224)
                2. data: Selected image data
                3. eps: numerical constant
                return: aMap(2D similarity map of shape (Height, Width)
            Author: Yugyeong Hong (2026.02.04)
        """
        
        lines, samples, band = data.shape
        data_ = data.reshape(-1, band).astype(np.float32, copy=False)          # (N,B), N=H*W
        kEndmember = np.asarray(kEndmember, dtype=np.float32)                  # (K,B)
        
        # Validate input dimensions and shape
        if kEndmember.ndim != 2 or kEndmember.shape[1] != band:
            return None
        
        similarity = self.samAmap(data_, kEndmember, eps=eps)                  # (N,K)

        # Validate similarity computation
        if not np.isfinite(similarity).all():
            print("Invalid similarity detected (NaN or Inf)")
            return None
        
        out = np.min(similarity, axis=1).astype(np.float32, copy=False)        # (N,)
        
        return out.reshape(lines, samples)
    

    def adaptiveThresholding(self, aMap, seed, win=50, strictnessPercentile=None):
        """
            Description: Compute a local strictness threshold from an aMap around a seed pixel
            Parameters
                1. aMap: 2D similarity map of shape (H, W)
                2. seed: pixel location as (row, col)
                3. win: half-window size for the local neighborhood
                4. strictnessPercentile: percentile(0-100), provided from user
            Author: Yugyeong Hong (2026.02.04)
        """
        lines, samples = aMap.shape
        row, col = seed
        simSeed = aMap[row, col]

        # Define the local window boundaries, ensuring they stay within the image dimensions
        rowStart = max(0, row - win); rowEnd = min(lines, row + win + 1)
        colStart = max(0, col - win); colEnd = min(samples, col + win + 1)
        localWindow = aMap[rowStart:rowEnd, colStart:colEnd]

        # Compute the strictness threshold based on the specified percentile of the local window values and the similarity at the seed pixel
        strictnessPercentileValue = float(np.nanpercentile(localWindow, strictnessPercentile))
        margin = float(0.2 * simSeed)
        strictnessThreshold = float(max(strictnessPercentileValue, simSeed-margin))
        thetaIntraThreshold = None
        return float(strictnessThreshold), thetaIntraThreshold
       
    
    def neighbors(self, row, col, height, width):
        # Retrieve 8 directions of center
        for directionRow, directionCol in EIGHTDIR:
            neighRow, neighCol = row + directionRow, col + directionCol
            if 0 <= neighRow < height and 0 <= neighCol < width:
                yield neighRow, neighCol
    
    def InitializeThetaIntra(self, data, seed, seedSpec, H, W, thetaIntraPercentile):
        """
            Description: Docstring for InitializeThetaIntra
            Parameters
                1. data: spectrum data data from selected image
                2. seed: pixel location as (row, col)
                3. seedSpec: spectrum data of seed pixel
             Author: Yugyeong Hong (2026.02.04)
        """
        neigh = []
        seedRow, seedCol = seed
        for neighRow, neighCol in self.neighbors(seedRow, seedCol, H, W):
            specN = data[neighRow, neighCol, :].astype(np.float64)
            sim = self.samAngle(specN, seedSpec)
            neigh.append(sim)

        
        return float(np.nanpercentile(neigh, thetaIntraPercentile) + 0.01)
    
    def updateThetaIntra(self, seedSpecs, center, thetaIntraPercentile):
        """
            Description: Adaptive threshold of thetaIntra
            Parameters
                1. seedSpec: spectrum data of seed pixel
                2. center: current center spectrum (can be updated every 10 pixels)
                3. thetaIntraPercentile: percentile(0-100), provided from user
             Author: Yugyeong Hong (2026.02.04)
        """
        recent = np.vstack(seedSpecs)  # (N,B)
        similarityList = []
        for rr in range(recent.shape[0]):
            sim = self.samAngle(recent[rr], center)
            similarityList.append(sim)
        return float(np.nanpercentile(np.array(similarityList), thetaIntraPercentile) + 1e-6)
    
    
    def regionGrowing(self, data, aMap, seed, strictnessPercentile = 90, thetaIntraPercentile=90, maxPixel=100):
            """
                Description: Process labeling starting from a seed based on strictness and thetaIntra thresholds
                Parameters:
                    1. data: Selected image data
                    2. aMap: 2D similarity map of shape (H, W)
                    3. seed: pixel location as (row, col)
                    4. strictnessPercentile: percentile(0-100), provided from user
                    5. thetaIntraPercentile: percentile(0-100), provided from user
                    6. maxPixel: Upper limit on the number of labeled pixels per seed
                 Author: Yugyeong Hong (2026.02.04)
            """
            strictnessThreshold, thetaIntraThreshold = self.adaptiveThresholding(
                aMap=aMap,
                seed=seed,
                strictnessPercentile=strictnessPercentile
            )

            lines, samples, band = data.shape
            visited = np.zeros((lines, samples), np.uint8) # Visited mask to prevent re-processing of pixels

            seedRow, seedCol = seed
            seedSpec = data[seedRow, seedCol, :] # Spectrum of the seed pixel
            seedSpecs = [seedSpec]

            visited[seedRow, seedCol] = 1
            count = 1
            accepted = [(seedRow, seedCol)]

            # thetaIntra init
            if thetaIntraThreshold is None:
                thetaIntraThreshold = self.InitializeThetaIntra(data, seed, seedSpec, lines, samples, thetaIntraPercentile)

            # ---------- BFS ----------
            # The region growing process uses a breadth-first search (BFS) approach, starting from the seed pixel 
            # and exploring its neighbors iteratively
            queue = deque([(seedRow, seedCol)])

            while queue and count < maxPixel:
                row, col = queue.popleft()
                center = np.nanmedian(np.vstack(seedSpecs), axis=0) if (count % 10 == 0) else seedSpec

                for neighRow, neighCol in self.neighbors(row, col, lines, samples):
                    if visited[neighRow, neighCol]:
                        continue
                    visited[neighRow, neighCol] = 1

                    # 1) Check the strictness Threshold
                    if aMap[neighRow, neighCol] < strictnessThreshold:
                        continue

                    # 2) Check the thetaIntra Threshold
                    spec = data[neighRow, neighCol, :].astype(np.float32) # Spectrum of the neighboring pixel 
                    similarity = self.samAngle(spec, center)   # Similarity between the neighboring pixel and the current center (or seedSpec)
                    if similarity > thetaIntraThreshold:
                        continue

                    # 3) Labelling
                    queue.append((neighRow, neighCol))
                    seedSpecs.append(spec)
                    accepted.append((neighRow, neighCol))
                    count += 1

                    # ThetaIntra threshold updata every 10 labelled pixels
                    if count % 10 == 0:
                        new_theta = self.updateThetaIntra(seedSpecs, center, thetaIntraPercentile)
                        if new_theta is not None:
                            thetaIntraThreshold = new_theta

                    if count >= maxPixel:
                        break

            # return indices only
            idx = np.asarray(accepted, dtype=np.int32)
            indice = (idx[:, 0], idx[:, 1])
            return indice