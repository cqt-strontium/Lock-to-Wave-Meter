__doc__ = """
Calibrate the laser response to DAC output
"""

import time 
import numpy as np
from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt 
import matplotlib as mpl 
from tqdm import tqdm


mpl.rc('font', size=6)  

def ls_reg(xarr, yarr):
    xmean = np.mean(xarr)
    ymean = np.mean(yarr)
    slope = np.sum((xarr-xmean)*(yarr-ymean)) / np.sum((xarr-xmean)**2) 
    intercept = ymean - slope * xmean 
    print('Slope is', slope)
    return lambda _: slope * _ + intercept 


class Calibrator: 
    def __init__(self, write_dac, get_wl):
        self.write_dac = write_dac
        self.get_wl = get_wl
        self.last_read = -1

    def read_wlm(self):
        ret = -1.  # is underexposed, the wavemeter would return -5 which is unreasonable 
        while ret < 0. :
            wl = self.get_wl()
            while wl == self.last_read: 
                wl = self.get_wl()
            ret = wl
        self.last_read = ret 
        return ret 

    
    def calibrate(self, num=100):
        v = np.linspace(-3,3,num)
        wl = []

        for voltage in tqdm(v):
            self.write_dac(voltage)
            wl.append(self.read_wlm())
        self.write_dac(0.)

        wl = np.array(wl)

        self.fig, self.ax = plt.subplots(figsize=(4,3))
        self.ax.plot(v, wl, '+')
        x1, x2 = self.retrieve_x_limit()
        mask = (v > x1) & (v < x2) 
        reg_func = ls_reg(v[mask], wl[mask])

        _, ax = plt.subplots(figsize=(4,3))
        ax.plot(v, wl)
        ax.plot([.9*x1, 1.1*x2], [reg_func(.9*x1), reg_func(1.1*x2)], '--')
        plt.show()


    def retrieve_x_limit(self):
        vlines = []
        def add_cursor(fig, ax,):
            cursor = Cursor(ax, useblit=True, horizOn=False, color='red', linewidth=2)

            def onclick(event):
                vlines.append(ax.axvline(x=event.xdata, color='k'))
                plt.pause(.2)  # have to flush the plot 
                
            fig.canvas.mpl_connect('button_press_event', onclick)
            
            return cursor  # cursor has to be returned, otherwise destroyed (due to zero ref count)
        
        _ = add_cursor(self.fig, self.ax)
        plt.show()
        if not vlines:
            return -1, 1
        
        x1, x2 = vlines[-2].get_xdata()[0], vlines[-1].get_xdata()[0]
        if x1 > x2: 
            x1, x2 = x2, x1 
        return x1, x2
        
