"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""


import numpy as np
import os
import spectral
import torch
from utils.encrypt import AesEncryption
from constants.constants import AGGREGATION_DATA
from PyQt5.QtCore import *

class gen_module(object):
	"""
		Description: Class for predicting data using trained models and extracting noise areas and merging data.
		Implement by MyoungHwan(2024.05.13)
    """
	def gen_hdr_info(self, hyp="VNIR", info="None"):
		"""
			Description: Add header declaration part when generating data
			Implement by MyoungHwan(2024.05.13)
			@history:
				1. GaEun Hwang(26.01.26):
					- Modify default band info format
    	"""
		_dict = {}
		if hyp == "NIR":
			_dict = {
				"information":info,
				"data type": 12,
				"interleave": "bil",
				"byte order": 0,
				"samples": 640,
				"bands": 224,
				"lines": 400,
				"default band":{192,113,51},
				"WaveCount":224,
				"wavelength":[
					900.00,903.57,907.14,910.71,914.29,917.86,921.43,925.00,928.57,932.14,935.71,939.29,942.86,946.43,950.00,953.57,
					957.14,960.71,964.29,967.86,971.43,975.00,978.57,982.14,985.71,989.29,992.86,996.43,1000.00,1003.57,1007.14,1010.71,
					1014.29,1017.86,1021.43,1025.00,1028.57,1032.14,1035.71,1039.29,1042.86,1046.43,1050.00,1053.57,1057.14,1060.71,1064.29,
					1067.86,1071.43,1075.00,1078.57,1082.14,1085.71,1089.29,1092.86,1096.43,1100.00,1103.57,1107.14,1110.71,1114.29,1117.86,
					1121.43,1125.00,1128.57,1132.14,1135.71,1139.29,1142.86,1146.43,1150.00,1153.57,1157.14,1160.71,1164.29,1167.86,1171.43,
					1175.00,1178.57,1182.14,1185.71,1189.29,1192.86,1196.43,1200.00,1203.57,1207.14,1210.71,1214.29,1217.86,1221.43,1225.00,
					1228.57,1232.14,1235.71,1239.29,1242.86,1246.43,1250.00,1253.57,1257.14,1260.71,1264.29,1267.86,1271.43,1275.00,1278.57,
					1282.14,1285.71,1289.29,1292.86,1296.43,1300.00,1303.57,1307.14,1310.71,1314.29,1317.86,1321.43,1325.00,1328.57,1332.14,
					1335.71,1339.29,1342.86,1346.43,1350.00,1353.57,1357.14,1360.71,1364.29,1367.86,1371.43,1375.00,1378.57,1382.14,1385.71,
					1389.29,1392.86,1396.43,1400.00,1403.57,1407.14,1410.71,1414.29,1417.86,1421.43,1425.00,1428.57,1432.14,1435.71,1439.29,
					1442.86,1446.43,1450.00,1453.57,1457.14,1460.71,1464.29,1467.86,1471.43,1475.00,1478.57,1482.14,1485.71,1489.29,1492.86,
					1496.43,1500.00,1503.57,1507.14,1510.71,1514.29,1517.86,1521.43,1525.00,1528.57,1532.14,1535.71,1539.29,1542.86,1546.43,
					1550.00,1553.57,1557.14,1560.71,1564.29,1567.86,1571.43,1575.00,1578.57,1582.14,1585.71,1589.29,1592.86,1596.43,1600.00,
					1603.57,1607.14,1610.71,1614.29,1617.86,1621.43,1625.00,1628.57,1632.14,1635.71,1639.29,1642.86,1646.43,1650.00,1653.57,
					1657.14,1660.71,1664.29,1667.86,1671.43,1675.00,1678.57,1682.14,1685.71,1689.29,1692.86,1696.43
				]
			}
		elif hyp == "VNIR":
			_dict = {
				"information":info,
				"data type": 12,
				"interleave": "bil",
				"byte order": 0,
				"samples": 512,
				"bands": 224,
				"lines": 400,
				"default band":{192,113,51},
				"WaveCount":224,
				"wavelength":[
					400.67,403.35,406.03,408.71,411.38,414.06,416.74,419.42,422.10,424.78,427.46,430.13,432.81,435.49,
					438.17,440.85,443.53,446.21,448.88,451.56,454.24,456.92,459.60,462.28,464.96,467.63,470.31,472.99,
					475.67,478.35,481.03,483.71,486.38,489.06,491.74,494.42,497.10,499.78,502.46,505.13,507.81,510.49,
					513.17,515.85,518.53,521.21,523.88,526.56,529.24,531.92,534.60,537.28,539.96,542.63,545.31,547.99,
					550.67,553.35,556.03,558.71,561.38,564.06,566.74,569.42,572.10,574.78,577.46,580.13,582.81,585.49,
					588.17,590.85,593.53,596.21,598.88,601.56,604.24,606.92,609.60,612.28,614.96,617.63,620.31,622.99,
					625.67,628.35,631.03,633.71,636.38,639.06,641.74,644.42,647.10,649.78,652.46,655.13,657.81,660.49,
					663.17,665.85,668.53,671.21,673.88,676.56,679.24,681.92,684.60,687.28,689.96,692.63,695.31,697.99,
					700.67,703.35,706.03,708.71,711.38,714.06,716.74,719.42,722.10,724.78,727.46,730.13,732.81,735.49,
					738.17,740.85,743.53,746.21,748.88,751.56,754.24,756.92,759.60,762.28,764.96,767.63,770.31,772.99,
					775.67,778.35,781.03,783.71,786.38,789.06,791.74,794.42,797.10,799.78,802.46,805.13,807.81,810.49,
					813.17,815.85,818.53,821.21,823.88,826.56,829.24,831.92,834.60,837.28,839.96,842.63,845.31,847.99,
					850.67,853.35,856.03,858.71,861.38,864.06,866.74,869.42,872.10,874.78,877.46,880.13,882.81,885.49,
					888.17,890.85,893.53,896.21,898.88,901.56,904.24,906.92,909.60,912.28,914.96,917.63,920.31,922.99,
					925.67,928.35,931.03,933.71,936.38,939.06,941.74,944.42,947.10,949.78,952.46,955.13,957.81,960.49,
					963.17,965.85,968.53,971.21,973.88,976.56,979.24,981.92,984.60,987.28,989.96,992.63,995.31,997.99
					]
			}

		return _dict

	def gen_merge_raw(self, save_path, data, label, ref, description="", hyperspectralType="VNIR"):
		"""
			Description: Generate merged raw data
			Implement by MyoungHwan(2024.05.13)
			@history:
				1. GaEun Hwang(26.01.26):
					- Add ref parameter to save custom WHITEREF/DARKREF data
					- Add stopFunc parameter to handle thread interruption for label aggregation mode
    	"""
		print("Generate merged data...")
		print(f"file save path:{save_path}")
		savePath = []
		headerDict = self.gen_hdr_info(hyperspectralType, AGGREGATION_DATA)
		lines, samples, band = headerDict["lines"], headerDict["samples"], headerDict["WaveCount"]
		outputNum = data.shape[0] // (lines*samples)
		if data.shape[0] % (lines*samples) != 0:
			outputNum += 1
		tmp_data = np.zeros((lines*samples*outputNum, band), dtype=np.uint16)
		tmp_label = np.zeros((lines*samples*outputNum), dtype=np.int64)
		tmpWhiteRef = np.zeros((lines*samples*outputNum, band), dtype=np.float32)
		tmpDarkRef = np.zeros((lines*samples*outputNum, band), dtype=np.float32)
		
		tmp_data[:data.shape[0]] = data.astype(np.uint16)
		tmp_label[:data.shape[0]] = label
		tmpWhiteRef[:data.shape[0]] = ref[0][:data.shape[0]].astype(np.float32)
		tmpDarkRef[:data.shape[0]] = ref[1][:data.shape[0]].astype(np.float32)

		for idx in range(outputNum):
			file_name = f"/{description}_{idx}"
			output_path = save_path + file_name
			if not os.path.isdir(output_path):
				os.mkdir(output_path)
			savePath.append(output_path)
			print("-"*50)
			print(f"Index:{idx}, file:{file_name}.")

			si, ei = (idx)*lines*samples, (idx+1)*lines*samples
			tmp_save_data = tmp_data[si:ei].astype(np.uint16)
			tmp_save_label = tmp_label[si:ei]
			tmpSaveWhiteRef = tmpWhiteRef[si:ei].astype(np.float32)
			tmpSaveDarkRef = tmpDarkRef[si:ei].astype(np.float32)

			save_data = tmp_save_data.reshape(lines,samples,-1).astype(np.uint16)
			save_label = tmp_save_label.reshape(lines,samples)
			saveWhiteRef = tmpSaveWhiteRef.reshape(lines,samples,-1).astype(np.float32)
			saveDarkRef = tmpSaveDarkRef.reshape(lines,samples,-1).astype(np.float32)

			np.save(f"{output_path}/label.npy",save_label)
			print(f"Index:{idx}, file:{file_name}, label.npy saved.")
			
			output_data_hdr_path = output_path +"/data.hdr"
			spectral.io.envi.save_image(output_data_hdr_path, save_data, ext=".raw", interleave="bil",
										byteorder=0, dtype=np.uint16, force=True, metadata=headerDict)
			print(f"Index:{idx}, file:{file_name}, Generated Merged raw data.")
			
			headerDict["data type"] = 4  # float32
			output_dark_hdr_path = output_path+"/DARKREF.hdr"
			spectral.io.envi.save_image(output_dark_hdr_path, saveDarkRef, ext=".raw", interleave="bil", 
										dtype=np.float32, force=True, metadata=headerDict)
			print(f"Index:{idx}, file:{file_name}, Generated Merged DARK REF raw data.")
			
			output_white_hdr_path = output_path+"/WHITEREF.hdr"
			spectral.io.envi.save_image(output_white_hdr_path, saveWhiteRef, ext=".raw", interleave="bil", 
										dtype=np.float32, force=True, metadata=headerDict)
			print(f"Index:{idx}, file:{file_name}, Generated Merged WHITE REF raw data.")
			print(f"Index:{idx}, file:{file_name}, Generate complete.")

		return savePath
			
	def get_sample(self, path):
		"""
			Description: Return meta data when data is called
			Implement by MyoungHwan(2024.05.13)
    	"""
		meta_data = spectral.io.envi.open(path + "/data.hdr", path + "/data.raw").metadata
		return meta_data
	
	def load_data(self, data_path, calibration=True, calibration_rate=1.0) -> np.ndarray:
		"""
			Description: Return data when data is called
			Implement by MyoungHwan(2024.05.13)
    	"""
		data = np.array(spectral.io.envi.open(data_path + "/data.hdr", data_path + "/data.raw").load())
		if calibration:
			dark_data = np.array(spectral.io.envi.open(data_path + "/DARKREF.hdr", data_path + "/DARKREF.raw").load()).mean(0)
			white_data = np.array(spectral.io.envi.open(data_path + "/WHITEREF.hdr", data_path + "/WHITEREF.raw").load()).mean(0)
			data = (((data-dark_data)/(white_data-dark_data))*4095.0)*calibration_rate
			data = np.array(np.clip(data, 0, 4095), dtype=np.float32)
		return data
		
	def load_model(self, load_path, gpu="cuda"):
		"""
			Description: Return trained model when model is called
			Implement by MyoungHwan(2024.05.13)
    	"""
		model = torch.jit.load(AesEncryption().make_water(load_path, _type="model"))
		model = model.to(gpu)
		return model
		