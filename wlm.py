import ctypes
from ctypes import cdll

def getWaveLengthAt(channel):
    '''
    Sample call: 
    1. wl = getWaveLengthAt(8)()
    2. getWaveLength = getWaveLengthAt(8)
       wl = getWaveLength()
    '''


    #Load functions from HighFinesse .dll file
    wm_dll = cdll.LoadLibrary("C:\Windows\System32\wlmData.dll")

    #Read wavelength
    wm_dll.GetWavelengthNum.restype = ctypes.c_double
    return lambda: wm_dll.GetWavelengthNum(ctypes.c_long(channel), ctypes.c_double(0))
    
if __name__ == '__main__':
    import time 
    channel = 8
    getWaveLength = getWaveLengthAt(channel)
    wl = getWaveLength()
    for i in range(10):
        print(wl)
        time.sleep(2) 

