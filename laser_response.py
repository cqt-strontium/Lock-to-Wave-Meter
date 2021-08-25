import time
from send_voltage_bytes import *

import numpy as np
import time 
from tqdm import tqdm

if __name__ == '__main__': 
    ser = setup_arduino_port('COM4')  # this is tested on local computer, so COM port is fixed 
    
    print('Arduino is ready. ')
    input()  
    f = open('loglog.txt', 'w')
    while True:
        for voltage in tqdm(np.linspace(-3,3,100)):
            send_voltage(ser, voltage, False)
            f.write('{}, {}, {}\n'.format(voltage, time.perf_counter(), time.time()))
            time.sleep(.1)
            