import numpy as np
from online_figure import OnlineFigure
from time import sleep 


def read_wavelength(fname):
    return float(np.genfromtxt(fname, delimiter=' ', max_rows=1, usecols=[2]))

class LocalPlotter():
    def __init__(self, fname):
        self.fname = fname 
        self.last_line = 0 

        self.fig = OnlineFigure(0,0, pause=1e-2)
        self.fig.ax.set_title(r'Target wavelength $\lambda_0=%.6f\,\mathrm{nm}$'%read_wavelength(fname))
        self.fig.ax.set_xlabel(r'Time elapsed $t\,/\,\mathrm{s}$')
        self.fig.ax.set_ylabel(r'Error $e=\lambda-\lambda_0\,/\,\mathrm{nm}$')
        
        self.update()
        self.fig.rescale_y()


    def update(self):
        data = np.genfromtxt(self.fname, delimiter=',', skip_header=12, usecols=[0,1])
        if self.last_line == len(data):  # nothing to update 
            return 
        self.fig.appendln(*(data[self.last_line:].T))
        self.last_line = len(data) 
    
    

lp = LocalPlotter('test')
while True:
    lp.update()
    sleep(1)
