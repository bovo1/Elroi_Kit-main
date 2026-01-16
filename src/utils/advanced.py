"""
	ELROILAB Kit

	Copyright 2024. Elroilab All rights reserved.
"""

from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.cluster import MiniBatchKMeans
import torch
from torch.utils.data import Dataset
import faiss
import copy
import torch
import cv2
import json
import os
import random
import time
from utils.shared import resource_path
from utils.encrypt import AesEncryption
from constants.constants import commonAbnormalDict, PATCH_SIZE

class KNN:
	def __init__(self,n_neighbors):
		self.n_neighbors = n_neighbors # k nearest neighbor value
		self.index = 0
		self.train_labels = []
		self.test_label_faiss_output = []

	def fit(self,train_features):
		self.index = faiss.IndexFlatIP(train_features.shape[1])
		faiss.normalize_L2(train_features)
		self.index.add(train_features)		 # add vectors to the index
		return self

	def kneighbors(self,test_features):
		faiss.normalize_L2(test_features)
		distance, index= self.index.search(test_features, self.n_neighbors)
		return 1-distance, index


class HSIDataset(Dataset):
    """
        HSI dataset. This is used in data loader.
        Attributes
            - datas(list): merged data that is used for train, valid, and test
            - labels(list): ground truth
            - patch_size(int): the size of patched HSI
            - binary(bool): the bool for binarized label(0: ignored, 1: normal, 2: abnormal)
            - ignored(list): the list of ignored label
            - p(int): the half of patch size
            - indices_list(list): list of the indices of ground truth
            - length(int): the length of pixels in ground truth to predict
    """
    def __init__(self, datas, labels, patch_size, binary=False, ignored=[0]):
        super(Dataset, self).__init__()
        assert patch_size > 0
        self.datas = datas
        self.labels = labels
        self.patch_size = patch_size

        self.p = self.patch_size // 2
        self.indices_list = []
        self.length = 0

        #Make ignored label 
        for i in ignored: 
            self.labels = np.where(self.labels == i, 0, self.labels)

        #AD option make [1,2] class to 2 and others(w/o 0) to 3
        for i in range(len(self.labels)):
            if binary == True:
                self.labels[i][np.logical_or(self.labels[i] == 1, self.labels[i] == 2)] = 2
                self.labels[i][self.labels[i] >= 3] = 3

        #Make pixel indices list
        for i in range(len(datas)):
            x_pos, y_pos = np.nonzero(self.labels[i])
            h, w, _ = datas[i].shape
            self.indices = np.array([(x, y) for x, y in zip(x_pos, y_pos) if x >= self.p and x < h - self.p and y >= self.p and y < w -self.p]) 
            self.indices_list.append(self.indices)
            self.length += len(self.indices)

    def __len__(self):
        """
            return length attributes
            Returns
                - length(int): the length of pixels in ground truth to predict
        """
        return self.length 

    def __getitem__(self, index):
        """
            return patch, label of center pixel, abnormality, indices
            Parameters
                - index(int): the index ranged from 0 to length
            Returns
                - data(torch): the patch image indexed by input
                - label(torch): the label of index
                - abnormality(int): if the label is abnormal, abnormality is -1, otherwise it is 0.
                - indices(tuple): the index of the image in data list, and position of pixel.
        """
        for i in range(len(self.indices_list)):
            length = len(self.indices_list[i])
            if index >= length: 
                index -= length 
                continue

            c_x, c_y = self.indices_list[i][index]

            ul_x, ul_y = c_x - self.p, c_y - self.p # Upper left x, y 
            br_x, br_y = ul_x + self.patch_size, ul_y + self.patch_size # Bottom right x, y

            # Make patch
            data = self.datas[i][c_x, c_y][None][None] if self.patch_size == 1 else self.datas[i][ul_x:br_x, ul_y:br_y,:]
            data = data.transpose((2, 0, 1))
            data = torch.from_numpy(data).float()
            
            # Make label
            label = torch.from_numpy(np.asarray(self.labels[i][c_x, c_y], dtype=np.int64))

            # Make abnormality
            abnormality = -1 if label == 2 else 1

            return data, label, abnormality, (i, c_x, c_y)


def knn_aug(feature, label, n_data, n_class, k, norm='l2'):


	knn = KNN(n_neighbors=k)
	knn= knn.fit(feature)
	values,indices= knn.kneighbors(feature)
	values = torch.as_tensor(values)

	knn_labels = label[indices]

	knn_labels_cnt = torch.zeros(n_data, n_class)
	for i in range(n_class):
		knn_labels_cnt[:, i] += torch.sum((1.0 - values) * (knn_labels == i), 1)

	return torch.nn.Softmax(1)(knn_labels_cnt)

def autoCommonLabel(data, label, path):
	"""
		Description: Common Abnormal Auto Labeling Function
		History
			1. Implemented by Hyunsu Kim (2025.11.21)
			2. Modified by Hyunsu Kim (2025.12.08) - change a create contour method using connectedComponents
	"""
	predictData = []
	try:
		model = torch.jit.load(AesEncryption().make_water(os.path.join(resource_path, "visualization/AutoLabeling.el"), _type="model")).to("cuda")
		model.eval()
		width, height, _ = data.shape

		for x in data:
			x = torch.from_numpy(x).to("cuda").float()
			hypothesis, _ = model(x)
			hypothesis = torch.argmax(torch.softmax(hypothesis, dim=1), dim=1)
			hypothesis = hypothesis.to("cpu").detach().numpy()
			predictData.append(hypothesis)

		predictData = np.array(predictData).reshape(-1, height)
		predictData[np.where(predictData <= 2)] = 0

		for label in np.unique(predictData):
			if predictData[np.where(predictData == label)].shape[0] > int((width * height) / 10):
				predictData[np.where(predictData == label)] = 0

		maskForContours = np.zeros_like(predictData).astype(np.uint8)
		for label in np.unique(predictData):
			if label == 0:
				continue
			maskForContours[np.where(predictData == label)] = 1

		cnt, labels = cv2.connectedComponents(maskForContours)

		for index in range(1, cnt):
			coords = np.where(labels == index)
			if coords[0].size == 0:
				continue
			contour = np.stack((coords[1], coords[0]), axis=-1)
			mask = np.zeros_like(predictData).astype(np.uint8)
			cv2.drawContours(mask, [contour], -1, 1, -1)
			labelCount = predictData[np.where(mask == 1)]
			unique, counts = np.unique(labelCount, return_counts=True)
			maskValue = unique[np.argmax(counts)]
			predictData[np.where(mask == 1)] = maskValue
		
		for label in np.unique(predictData):
			mask = np.zeros_like(predictData).astype(np.uint8)
			mask[np.where(predictData == label)] = 1
			mask = cv2.erode(mask, np.ones((PATCH_SIZE, PATCH_SIZE), np.uint8), iterations=1)
			predictData[(mask == 0) & (predictData == label)] = 0

		if os.path.exists(path + "/data.json"):
			with open(path + "/data.json", 'r', encoding="utf-8") as f:
				temp = json.load(f)
		else:
			temp = {}
			temp["label_info"] = path.split("/")[-1]
			temp["time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
			
		for label in commonAbnormalDict.keys():
			color = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
			commonAbnormalDict[label]['label_color'] = color
		temp['commonLabelInfo'] = commonAbnormalDict

		with open(path + "/data.json", 'w', encoding="utf-8") as f:
			json.dump(temp, f)

	except Exception as e:
		print(f"Error labeling common abnormal: {e}")

	return predictData

def fastsimifeat(data, label, k=10, pretrained=False):
	dataset=HSIDataset([data], [label], patch_size=1, binary=False, ignored=[0])
	train_loader = torch.utils.data.DataLoader(dataset=dataset, batch_size=512, shuffle=False, drop_last=False)#, num_workers=4, persistent_workers=True)

	print("fast fit")
	# #Feature Extraction
	h,w,c = np.shape(data)
	n_class = np.max(label)+1
	X=[]
	Y=[]
	pos=[]
	for x, y, _, xy in train_loader:
		X+=list(x.numpy())
		Y+=list(y.numpy())
		pos+=list(zip(*xy))
	X = np.array(X).reshape(-1,c)
	Y = np.array(Y).reshape(-1)


	# X = np.array(data.reshape(-1,c))
	# Y = np.array(label).reshape(-1)
	print("X , Y shape", X.shape, Y.shape)

	#KNN and estimate noisy ratio
	pred_label = copy.deepcopy(Y)
	for j in range(1):
		knn_label_prob = knn_aug(X, pred_label, np.shape(X)[0], n_class, k=k)
		pred_probs = torch.as_tensor(knn_label_prob)
		pred_label= torch.argmax(pred_probs, 1)

		if j ==0:
			tmp_probs = pred_probs
	t_voting = confusion_matrix(Y, pred_label, labels=[i for i in range(n_class)])
	t_voting = t_voting/(t_voting.astype(float).sum(1)+1e-12)

	#Score function
	onehot = np.eye(n_class)[Y]
	onehot=torch.as_tensor(onehot)
	smoothing_label=[]
	n_sample = np.shape(X)[0]
	for j in range(n_sample):
		tmp = copy.deepcopy(t_voting[Y[j]])
		smoothing_label += list(tmp)

	smoothing_label = np.array(smoothing_label).reshape((n_sample,-1))
	smoothing_label = torch.as_tensor(smoothing_label)

	score = torch.sum(onehot* torch.log((onehot+1e-12)/(knn_label_prob+1e-12)),1)
	score2 = torch.sum(smoothing_label * torch.log((smoothing_label+1e-12)/(tmp_probs+1e-12)),1)

	#Ranking-based noisy label detection
	mask = torch.zeros((n_sample))
	Y = torch.as_tensor(Y)
	classes=np.unique(Y)
	for j in classes:
		thr = min(t_voting[j][j], 1.0)

		if thr>= 1.0:
			thr= 0.95
		elif thr<= 0.0:
			thr= 0.05

		indices = torch.where(Y==j)

		s = score[indices]
		s2 = score2[indices]
		top = torch.topk(torch.as_tensor(t_voting[j]),k=min(k+2,n_class)).values

		if top[1] > torch.sum(top[2:]):
			s = s-0.1*s2
		else:
			s = s+0.1*s2
		q = torch.quantile(s, thr)

		correct_label_masking = torch.where(s <q, 1,0)
		mask[indices] = correct_label_masking.float()

	#Masking only for anomaly
	Y2 = torch.where((mask==1)|(Y<=2), Y, 0)
	_, x, y = list(zip(*pos))
	relabel = copy.deepcopy(label)
	for i in range(len(x)):
		x_pos = x[i]
		y_pos = y[i]
		relabel[x_pos][y_pos] = Y2[i]
	relabel = np.array(relabel)
	return relabel, _


class Kmeans:
	def __init__(self) -> None:
		self.name = "Kmeans"
		self.data = None
		self.c_num = 1
		
	def extract_sparse(self, data, c_num:int=1) -> np.ndarray:
		# print(f"{self.name} Extracting Sparse")
		kmeans = MiniBatchKMeans(init ='k-means++', n_clusters = c_num, 
                      batch_size = 512, 
                      max_no_improvement = 50, verbose = 0)
		kmeans.fit(data)
		# print("Extracting Complete")
		return kmeans.cluster_centers_

def simplelabeling(data, label, label_num=0, c_num=2):
	"""
		Description: SAL(Simple Auto Labeling) Function
		Implemented by MyoungHwan (2024.02.05)

	"""
	w, h, b= data.shape
	data_f = data.reshape(-1, 224)
	label_f = label.flatten()
	"""
		Description: Add Exception error
		Modified by Myounghwan (20240205)
	"""
	try:
		indices = np.where(label_f==label_num)
		kmeans = MiniBatchKMeans(init ='k-means++', n_clusters = c_num, 
						batch_size = 512, 
						max_no_improvement = 50, verbose = 0)
		kmeans.fit(data_f[indices])
		"""
			description
			modified by MyoungHwan(20240603) : output 결과값 변경
		"""
		return [1, indices, kmeans.cluster_centers_, kmeans.labels_]
	except Exception as e:
		return [0, str(e)]
				

if __name__ == "__main__":
    print("test mode")
    test = Kmeans()
    data = np.random.randint(4096, size=(10,224))
    result = test.extract_sparse(data=data, c_num=1)
    print(result.shape)
    ll = []
    ll.append(result)
    print(np.array(ll).squeeze().shape)