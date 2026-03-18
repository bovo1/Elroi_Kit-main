"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import os
import numpy as np
import copy
import random

#random generate color
gen_color = lambda : [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

class DB_Control_Labeling(object):
    def __init__(self, Core_DB_Labeling=None, functions=None, Sync=None) -> None:
        self.Core_DB_Labeling = Core_DB_Labeling
        self.Sync = Sync
        self.load_data, self.load_label_info, self.send_core_db_to_label, self.send_core_to_image_sub, self.send_core_to_graph_sub = functions

        self.Sub_Core_Sync_Labeling = self.Sync.Sub_Core_Sync_Labeling
        self.image_control_dict = self.Sub_Core_Sync_Labeling.image_control_dict
        self.label_obj_dict = self.Sub_Core_Sync_Labeling.label_obj_dict

    def query_db_labeling(self, output):
        '''
            @Description: 모든 기능들로부터 데이터에 대한 모든 정보를 Core DB에 저장하고 업데이트 하기 위한 함수이다.
            @Autorh: MyoungHwan
            @Parameters
                1.  output(dict): 데이터 정보 및 액션 명령어
                    - mode: Core DB를 업데이트하기 위한 명령어 수행
                        1. create : 초기 데이터 리스트 받고 DB에 생성
                        2. modify : DB에 생성된 데이터 정보 수정
                        3. select : DB에 데이터 요청
                        4. delete : DB에 데이터 제거
            @History
                1. Improvemented by MyoungHwan (2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
                2. Improvemented by MyoungHwan (2024.12.13): 데이터 로딩코드 수정

        '''
        output_cmd = output['mode']
        if output_cmd == 'create':
            output_type = output['type']
            # create image list, and load rgb, label, hsi data
            if output_type == 'image':
                image_number = output['image_number']
                
                self.Core_DB_Labeling['image_list'][image_number] = {}
                self.Core_DB_Labeling['image_list'][image_number]['image_info'] = {}
                self.Core_DB_Labeling['image_list'][image_number]['label_list'] = {}
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_name'] = output['image_name']
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_path'] = output['image_path']

                
                # Improvemented by MyoungHwan (2024.12.13): 데이터 로딩코드 수정
                image_rgb_data, image_label_data, image_hsi_data, \
                    image_rgb_name, image_label_name, image_hsi_name, \
                        hsi_metadata, image_hsi_data_origin, \
                            dark_data, white_data = self.load_data(output['image_path'], output['image_name'], label_name=output['label_name'], raw_name=output['raw_name'])

                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data'] = image_rgb_data
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label_origin'] = copy.deepcopy(image_label_data.astype(np.int64))
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label_origin'])
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw'] = image_hsi_data
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_origin'] = image_hsi_data_origin
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_white'] = white_data
                self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_dark'] = dark_data
                if len(hsi_metadata) != 0 :
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_metadata'] = hsi_metadata
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_shape'] = [int(hsi_metadata['lines']), int(hsi_metadata['samples']), int(hsi_metadata['bands'])]
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_default_bands'] = list(map(int, hsi_metadata['default band']))
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_length'] = list(map(float, hsi_metadata['wavelength']))
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_count'] = int(hsi_metadata['wavecount'])
                else:
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_metadata'] = {}
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_shape'] = [0,0,0]
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_default_bands'] = []
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_length'] = []
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_count'] = []

                if image_rgb_name:
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data_name'] = image_rgb_name
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data_path'] = output['image_path'] + '/' +  output['image_name']
                else:
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data_name'] = ''
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data_path'] = ''
                if image_label_name:        
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label_name'] = image_label_name
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label_path'] = output['image_path']+ '/' +  output['image_name']
                else:
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label_name'] = ''
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label_path'] = ''
                if image_hsi_name:                
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_name'] = image_hsi_name
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_path'] = output['image_path'] + '/' +  output['image_name']
                else:
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_name'] = ''
                    self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_path'] = ''

                label_list = list(map(int, np.unique(image_label_data)))
                label_info_data = self.load_label_info(output['image_path'], output['image_name'])
                if 0 not in label_list:
                    label_list = [0] + label_list
                for label in label_list:
                    self.Core_DB_Labeling['image_list'][image_number]['label_list'][label] = {}
                    if label in label_info_data:
                        # print('load success label:',label)
                        self.Core_DB_Labeling['image_list'][image_number]['label_list'][label]['label_name'] = label_info_data[label]['label_name']
                        self.Core_DB_Labeling['image_list'][image_number]['label_list'][label]['label_color'] = label_info_data[label]['label_color']
                    else:
                        # print('load fail label:',label)
                        self.Core_DB_Labeling['image_list'][image_number]['label_list'][label]['label_name'] = f''
                        if label == 0:
                            self.Core_DB_Labeling['image_list'][image_number]['label_list'][label]['label_color'] = [255,255,255]
                        else:
                            self.Core_DB_Labeling['image_list'][image_number]['label_list'][label]['label_color'] = gen_color()
                
                self.Core_DB_Labeling['graph_info'][image_number] = {}
                tmp_shape = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_shape']
                if tmp_shape != [0,0,0]:
                    tmp_w, tmp_h, _ = tmp_shape
                    self.Core_DB_Labeling['graph_info'][image_number]['rgb'] = np.full((tmp_w, tmp_h, 3), -1)

            # if label widget is created,,,
            elif output_type == 'label':
                output_type_detail = output['type_detail']
                if output_type_detail == 'new':
                    image_number = self.image_control_dict['select_image_number']
                    label_number = output['label_number']
                    self.Core_DB_Labeling['image_list'][image_number]['label_list'][label_number] = {}
                    self.Core_DB_Labeling['image_list'][image_number]['label_list'][label_number]['label_name'] = output['label_name']
                    self.Core_DB_Labeling['image_list'][image_number]['label_list'][label_number]['label_color'] = output['label_color']

                elif output_type_detail == 'load':
                    image_number = self.image_control_dict['select_image_number']
                    label_number = output['label_number']
                    self.Core_DB_Labeling['image_list'][image_number]['label_list'][label_number]['label_name'] = output['label_name']
                    self.Core_DB_Labeling['image_list'][image_number]['label_list'][label_number]['label_color'] = output['label_color']

        # modify mode
        elif output_cmd =='modify':
            output_type = output['type']
            output_type_detail = output['type_detail']
            if output_type == 'image':
                if output_type_detail == 'select':
                    pass
                    # select_image_number = output['image_number']
                    # self.image_control_dict['select_image_number'] = select_image_number
                    # for image_number in list(self.Core_DB_Labeling['image_list'].keys()):
                    #     if image_number == select_image_number:
                    #         if self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_select_obj'].isChecked() == False:
                    #             self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_select_obj'].toggle()
                    #     elif image_number != select_image_number:
                    #         if self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_select_obj'].isChecked():
                    #             self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_select_obj'].toggle()
                
                elif output_type_detail == 'detail':
                    output_type_detail_2 = output['type_detail_2']
                    output_select_image_number = output['select_image_number']
                    output_file_path = output['file_path']
                    image_hsi_shape = self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_raw_shape']
                    commonAbnormalUse = False
                    # Improvemented by MyoungHwan (2024.12.13): 데이터 로딩코드 수정
                    # 불필요 로딩(rgb, hsi) 코드 제거
                    check_, data = self.load_data(output_file_path,'',mode=output_type_detail_2, shape=image_hsi_shape)
                    if check_: # name이 존재하는 경우 성공적으로 load 했다는 말
                        self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label_path'] = os.path.split(output_file_path)[0]
                        self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label_name'] = os.path.split(output_file_path)[1]
                        self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label'] = copy.deepcopy(data)
                        """
                            description
                            Modified by MyoungHwan(20240529) : label_list initialization when loading other label.npy
                        """
                        self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'] = {}
                        
                        """
                            @Description: data.json으로부터 label 정보를 불러와서 존재하는 label에 대한 정보를 업데이트한다.
                            @author: Hyunsu
                            @History
                                1. Added by Hyunsu(2025.03.19): update label information from data.json
                                2. Added by Hyunsu Kim(2025.11.21) : Setting the conditions required for the load_label_info function
                        """
                        label_list = list(map(int, np.unique(self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label'])))
                        image_path = os.path.dirname(self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label_path'])
                        image_name = os.path.basename(self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label_path'])
                        if self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']['image_label_name'] == "auto_common_label.npy":
                            commonAbnormalUse = True
                        label_info_data = self.load_label_info(image_path, image_name, labelChange=commonAbnormalUse)
                        if 0 not in label_list:
                            label_list = [0] + label_list
                        for label in label_list:
                            self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'][label] = {}
                            if label in label_info_data:
                                self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'][label]['label_name'] = label_info_data[label]['label_name']
                                self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'][label]['label_color'] = label_info_data[label]['label_color']
                            else:
                                self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'][label]['label_name'] = f'Label_{label}'
                                if label == 0:
                                    self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'][label]['label_color'] = [255,255,255]
                                else:
                                    self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list'][label]['label_color'] = gen_color()
                        
                    else:
                        print(f'Label load failed : {output_file_path}')
                    
                    # Improvemented by MyoungHwan (2024.12.13): 데이터 로딩코드 수정
                    # Label load 후 결과 전달
                    if 'from' not in output:
                        tmp_dict = {}
                        tmp_dict['mode'] = 1
                        tmp_dict['status'] = check_
                        tmp_dict['path'] = output_file_path
                        self.send_core_to_image_sub(tmp_dict)
                    else:
                        # Label load 후 Core DB Labeling 정보 전달
                        tmp_dict = {}
                        tmp_dict['mode'] = 'load'
                        tmp_dict['image_info'] = self.Core_DB_Labeling['image_list'][output_select_image_number]['image_info']
                        tmp_dict['label_info'] = self.Core_DB_Labeling['image_list'][output_select_image_number]['label_list']
                        tmp_dict['image_number'] = output_select_image_number
                        self.send_core_db_to_label(tmp_dict)

            elif output_type == 'label':
                select_label_number = output['label_number']
                select_image_number = self.image_control_dict['select_image_number']

                if output_type_detail == 'number':
                    label_old_number = output['label_old_number']
                    """
                        Description: Prevent to overwrite the label list
                        Modified by Hyeok Yoon (2025.11.06) 
                    """
                    if select_label_number not in self.Core_DB_Labeling['image_list'][select_image_number]['label_list']:
                        self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][select_label_number] = {
                            'label_name': self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][label_old_number]['label_name'],
                            'label_color':self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][label_old_number]['label_color']
                        }

                    """
                        Description: Added code to delete old label number to DB
                        Modified by MyoungHwan (2024.09.06) 
                    """
                    self.Core_DB_Labeling['image_list'][select_image_number]['label_list'].pop(label_old_number, None)
                    self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'] = np.where(self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'] == label_old_number, select_label_number,\
                        self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'])

                elif output_type_detail == 'color':
                    select_image_number = self.image_control_dict['select_image_number']
                    select_label_number = output['label_number']
                    label_color = output['label_color']
                    self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][select_label_number]['label_color'] = label_color

                elif output_type_detail == 'name':
                    select_image_number = self.image_control_dict['select_image_number']
                    select_label_number = output['label_number']
                    label_name = output['label_name']
                    self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][select_label_number]['label_name'] = label_name
            
            elif output_type == 'display':
                if output_type_detail == 'drawing_label_data':
                    select_image_number = self.image_control_dict['select_image_number']
                    select_label_number = output['label_number']
                    indice = output['indice']
                    self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'][indice] = select_label_number

                elif output_type_detail == 'label_data_from_memory':
                    select_image_number = self.image_control_dict['select_image_number']
                    label = output['label']
                    self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'] = label

                elif output_type_detail == 'graph_data':
                    select_image_number = self.image_control_dict['select_image_number']
                    indice, color = output['point_info']
                    self.Core_DB_Labeling['graph_info'][select_image_number]['rgb'][indice] = color
                
            elif output_type == 'pen':
                if output_type_detail == 'none':
                    pass
                elif output_type_detail == 'drawing':
                    pass
                elif output_type_detail == 'erase':
                    pass
                elif output_type_detail == 'part_scale':
                    pass
                elif output_type_detail == 'part_move':
                    pass
                elif output_type_detail == 'pen_detail':
                    output_type_detail_2 = output['type_detail_2']
                    if output_type_detail_2 =='pen_size':
                        pass
                    elif output_type_detail_2 =='pen_drawing_type':
                        pass
                    elif output_type_detail_2 =='eraser_size':
                        pass
                elif output_type_detail == 'painting':
                    pass
                elif output_type_detail == 'rectangle':
                    pass
                elif output_type_detail == 'polygon':
                    pass
                elif output_type_detail == 'semiAutoLabeling':
                    pass

        # delete mode, All or Select one deletee
        elif output_cmd == 'delete':
            output_type = output['type']
            if output_type == 'image':
                select_type = output['select_type']
                if select_type == 'all':
                    del self.Core_DB_Labeling['image_list']
                    self.Core_DB_Labeling['image_list'] = {}
                else:
                    select_image_number = output['image_number']
                    del self.Core_DB_Labeling['image_list'][select_image_number]

            elif output_type == 'label':
                select_type = output['select_type']
                if select_type == 'all':
                    select_image_number = self.image_control_dict['select_image_number']
                    for label in list(self.Core_DB_Labeling['image_list'][select_image_number]['label_list'].keys()):
                            del self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][label]
                    self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'].fill(0)
                    
                elif select_type == 'one':
                    select_image_number = self.image_control_dict['select_image_number']
                    select_label_number = output['label_number']
                    del self.Core_DB_Labeling['image_list'][select_image_number]['label_list'][select_label_number]
                    self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'] = np.where(self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'] == select_label_number, 0, \
                        self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label'])
            
            elif output_type == 'display':
                select_image_number = self.image_control_dict['select_image_number']
                select_type = output['select_type']
                output_type_detail = output['type_detail']
                if select_type == 'graph_data':
                    if output_type_detail == 'one':
                        indice = output['point_info'][0]
                        self.Core_DB_Labeling['graph_info'][select_image_number]['rgb'][indice] = [-1,-1,-1]
                    elif output_type_detail == 'all':
                        tmp_shape = self.Core_DB_Labeling['graph_info'][select_image_number]['rgb'].shape
                        del self.Core_DB_Labeling['graph_info'][select_image_number]['rgb']
                        self.Core_DB_Labeling['graph_info'][select_image_number]['rgb'] = np.full(tmp_shape, -1)