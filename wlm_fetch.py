__doc__ = """
Automatically records wavelength when there's a change in the output of wavemeter
"""

import time
from wlm import getWaveLengthAt


get_wl = getWaveLengthAt(7)
wl = get_wl()

cnt = 0
with open('log@%s.txt'%(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())), 'w') as f:
    while True:
        while get_wl() == wl: 
            # time.sleep is not fine enough, always profile this loop before use
            # this loop costs 3ms under usage condition
            for _ in range(20000):  
                pass
        wl = get_wl()
        f.write('{}, {}, {}\n'.format(wl, time.perf_counter(), time.time()))
        cnt += 1 
        if cnt > 100000: break