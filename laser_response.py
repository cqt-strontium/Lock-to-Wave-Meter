import time


from time import perf_counter
from send_voltage_bytes import *

from get_comport import get_com_port

import numpy as np

if __name__ == '__main__': 
    # ser = setup_arduino_port(get_com_port())
    ser = setup_arduino_port('COM4')
    
    print('Arduino is ready. ')
    input()
    while True:
        for voltage in np.linspace(-3,3,20):
            send_voltage(ser, voltage, False)
            print(voltage)
            time.sleep(2)