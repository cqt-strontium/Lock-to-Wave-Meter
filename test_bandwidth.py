__doc__ = """
Test bandwidth of the Python script. 

Be sure to turn off DEBUG switch in the Arduino code. 
"""

from send_voltage_bytes import * 
import numpy as np 
from tqdm import tqdm  # use tqdm if you want to test without oscilloscope

if __name__ == '__main__': 
    ser = serial.Serial('COM4', 115200, timeout=1) 
    
    # Arduino will send back "Arduino setup finished!" once it's all set
    while True: 
        msg = get_line_msg(ser)
        if not msg.strip():
            time.sleep(1)
        else:   
            print(msg)
            if msg.find('Control') + 1: 
                print(msg.strip())
            if msg.find('Arduino') + 1: 
                break
            
    print('Arduino is ready. ')
    while True:
        for voltage in np.linspace(-3,3,20):
            while get_msg(ser) != 'a':
                pass
            send_voltage(ser, voltage, False)
            # time.sleep(0.0005)
