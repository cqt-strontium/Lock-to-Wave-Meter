__doc__ = """
Calibrate the laser response to DAC output
"""

import time 
import numpy as np
from scipy.interpolate import interp1d 


class Calibrator: 
    def __init__(self, write_dac, read_wlm):
        self.write_dac = write_dac
        self.read_wlm = read_wlm 
    
    def calibrate(self, num=100):
        v = np.linspace(-3,3,num)
        wl = []

        for voltage in v:
            self.write_dac(voltage)
            time.sleep(.1)
            wl.append(self.read_wlm())
        
        return interp1d(v, wl) 
        
