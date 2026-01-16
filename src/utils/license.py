import os
import sys
import platform, psutil
import random, string
from utils.encrypt import AesEncryption

from .shared import license_path


version = sys.version_info

def check_lic_status(lic_file=os.path.join(license_path, "license.lic")):

    if os.path.exists(lic_file):
        value = get_your_status()
        result = AesEncryption().make_water(lic_file)
        for i in range(len(value['MAC_Address'])):
            if value['MAC_Address'][i] in result['LIC_MAC']:
                # print("lic valid")
                return True
        return False
    else:
        # print("license is not found.") 
        return False

def make_HW_status(sub_file=os.path.join(license_path, "Submission")):
    value = get_your_status()
    AesEncryption().make_fire(value, sub_file)
    # print("make hw stats sucess")

def get_your_status():
    HW_DICT = {}
    HW_DICT['MAC_Address'] = []

    uname = platform.uname()
    HW_DICT['System'] = uname.system
    HW_DICT['Node_Name'] = uname.node
    HW_DICT['Release'] = uname.release
    HW_DICT['Version'] = uname.version
    HW_DICT['Machine'] = uname.machine
    HW_DICT['Processor'] = uname.processor


    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            if version < (3,10,11):
                if str(address.family) == 'AddressFamily.AF_LINK':
                    HW_DICT['MAC_Address'].append(address.address)
            elif version > (3,11,0):
                if address.family == -1:
                    HW_DICT['MAC_Address'].append(address.address)

    random_value_length = 4096
    HW_DICT['random_value'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(random_value_length))

    return HW_DICT
