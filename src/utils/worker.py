"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import sys
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, QObject
import inspect

def testfunc(data, label, label_num=0, c_num=2):
	w, h, b= data.shape
	data_f = data.reshape(-1, 224)
	label_f = label.flatten()
	label_f = label_f + 1000
	return label_f.reshape(w,h), 0


class Threading_Worker(QThread):
    output = pyqtSignal(dict)    # 사용자 정의 시그널
    """
        1.self.Func : 스레딩 처리할 함수로 return annotation 명시 필수
            ex: def abc(i1, i2, i3) -> None 혹은 출력타입 명시!
    """
    def __init__(self):
        super().__init__()
        self.reset_()
    
    def reset_(self):
        self.status = True
        self.Func = None
        self.cur_id = 0
        self.output_dict = {
            "id": -1
        }

    def check_(self, Func, input_):
        func_parameter = inspect.signature(Func).parameters
        if set(func_parameter) == set(input_):
            return True
        else:
            return False
        
    def staging(self, Func):
        self.Func = Func
        self.cur_id = id(self.Func)
        self.output_dict['id'] = self.cur_id

    def run(self):
        print("Threading Process.")
        if self.status:
            self.status = False
            if isinstance(self.Func , type(None)):
                print("self.Func is None")
            else:
                print("Threading Target id:", self.cur_id)
                if self.Func.__annotations__['return'] is not None:
                    print("Function is wrong.")
                else:
                    self.Func()
                    self.output.emit(self.output_dict)     # 방출
            self.reset_()
            self.quit()
            print("Threading Complete")
        else:
            print(f"Threading Target id: {id(self.Func)} is not complete")
    
    def stop(self):
        """
            @description: Stop Threading Worker
            @author : GaEun Hwang (26.02.10)
        """
        # check thread status
        if self.status == False:
            self.terminate()
            # use wait to ensure thread has completely stopped
            self.wait()
            self.reset_()
            print("Threading Stopped")
            self.output.emit(self.output_dict)

class AutoLabel_Worker(QThread):
    """
        Description: AutoLabel Threading worker Function
        Implement By MyoungHwan
    """
    output = pyqtSignal(dict)    # 사용자 정의 시그널

    def __init__(self):
        super().__init__()
        self.status = True
        self.Func = None
        self.output_dict = {}
        self.datapack = []

    def run(self):
        print("Threading Process.")
        if self.status:
            self.status = False
            if isinstance(self.Func , type(None)):
                print("self.Func is None")
                print("Thread out.")
            else:
                print("Threading Target id:", id(self.Func))
                print("process mode:",self.output_dict['mode'])
                if len(self.datapack): 
                    data, label, path = self.datapack
                    """
                        Description: Modify return value process
                        History
                            1. Modified by MyoungHwan (2024.02.05)
                            2. Modified by Hyunsu Kim (2025.11.21) : Add path parameter for common abnormal auto labeling

                    """
                    if self.output_dict["mode"] == 2:
                        result = self.Func(data, label, path)
                    else:
                        result = self.Func(data, label)
                    self.output_dict['path'] = path
                    self.output_dict['id'] = id(self.Func)
                    self.output_dict['result'] = result
            print("Threading Complete")
            self.output.emit(self.output_dict)     # 방출
            self.status = True
            self.output_dict = {}
            self.datapack = []
            self.quit()
        else:
            print(f"Threading Target id: {id(self.Func)} is not complete")

class test_MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # self.el = test(100,250)
        self.worker = AutoLabel_Worker()
        self.worker.Func = testfunc
        self.worker.datapack = [np.random.rand(3,3,224), np.zeros((3,3)), "/"]
        self.worker.start()
        self.worker.output_dict = {
            'mode': 1
        }
        self.worker.output.connect(self.result)   # 시그널 슬롯 등록

    @pyqtSlot(dict)
    def result(self, output):
        print(output)


if __name__ == "__main__":
    print("test mode")
    app = QtWidgets.QApplication(sys.argv)
    mywindow = test_MyWindow()
    mywindow.show()
    app.exec_()

