__doc__ = """
Calibrate the laser response to DAC output
"""

import time 
import numpy as np
from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt 

def ls_reg(xarr, yarr):
    xmean = np.mean(xarr)
    ymean = np.mean(yarr)
    slope = np.sum((xarr-xmean)*(yarr-ymean)) / np.sum((xarr-xmean)**2) 
    intercept = ymean - slope * xmean 
    print('Intercept is', intercept)
    return lambda _: slope * _ + intercept 


class Calibrator: 
    def __init__(self, write_dac, read_wlm):
        self.write_dac = write_dac
        self.read_wlm = read_wlm 
    
    def calibrate(self, num=100, repeat=1):
        v = np.linspace(-3,3,num)
        wl = []

        for voltage in v:
            self.write_dac(voltage)
            time.sleep(.1)
            wl.append(self.read_wlm())
        
        # wlv = interp1d(v, wl) 
        wl = np.array(wl)
        self.fig, self.ax = plt.subplots()
        self.ax.plot(v, wl)
        x1, x2 = self.retrieve_x_limit()
        mask = (v > x1) & (v < x2) 
        reg_func = ls_reg(v[mask], wl[mask])

        _, ax = plt.subplots()
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
        
        x1, x2 = vlines[-2].get_xdata()[0], vlines[-1].get_xdata()[0]
        if x1 > x2: 
            x1, x2 = x2, x1 
        return x1, x2
        
