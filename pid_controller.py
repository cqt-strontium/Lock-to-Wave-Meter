import time
from wlm import getWaveLengthAt
from collections import deque
from time import perf_counter
from send_voltage_bytes import send_voltage, setup_arduino_port
from scipy.integrate import trapz
from logger import Logger 
from signal_test import eavesdropper, Process


class PIDController():
    def __init__(self, channel, port, wavelength=None, kp=-800., ki=-1000./1.2, kd=-10., buffer_length=10):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.channel = channel
        self.port = port
        
        self.ser = setup_arduino_port(port)
        
        self.get_wl = getWaveLengthAt(channel)
        if not wavelength:
            wavelength = self.get_wl()
        self.set_wavelength = wavelength
        
        self.buffer_length = buffer_length
        self.setup_buffer()
        

        self.logger = Logger([],[],header='Target wavelength %.6f nm\nKp=%.1f, Ki=%.2f, Kd=%.2f\n'%(self.set_wavelength, self.kp, self.ki, self.kd))
    

    def setup_buffer(self):
        self.error_buffer = deque()
        self.time_buffer = deque()  # records the time stamp when a measurement is done
        
        for _ in range(self.buffer_length):
            error = self.read_wlm() - self.set_wavelength
            self.error_buffer.append(error)
            self.time_buffer.append(perf_counter())
        
        self.int = trapz(self.error_buffer, self.time_buffer)

    def read_wlm(self):
        '''
        Returns the wavelength at the moment
        '''
        if not self.error_buffer:
            return self.get_wl()
        ret = -1.  # is underexposed, the wavemeter would return -5 which is unreasonable 
        while ret < 0. :
            wl = self.get_wl()
            while wl - self.set_wavelength == self.error_buffer[-1]: 
                wl = self.get_wl()
            ret = wl
        return ret 


    def write_dac(self, voltage):
        '''
        Write to DAC device through Arduino 
        '''
        send_voltage(self.ser, voltage)



    def loop(self):
        '''
        Main PID loop
        '''
        error = self.read_wlm() - self.set_wavelength

        self.time_buffer.append(perf_counter())
        self.error_buffer.append(error)
        self.time_buffer.popleft()
        self.error_buffer.popleft()

        self.int += .5 * (self.error_buffer[-1] + self.error_buffer[-2]) * (self.time_buffer[-1] - self.time_buffer[-2])
            
        self.logger.log([self.time_buffer[-1], self.error_buffer[-1], self.kp * error, self.ki * self.int, self.kd * (self.error_buffer[-3] - self.error_buffer[-1]
                         ) / (self.time_buffer[-3] - self.time_buffer[-1])])
        
        self.write_dac(
            self.kp * error
            + self.ki * self.int
            + self.kd * (self.error_buffer[-3] - self.error_buffer[-1]
                         ) / (self.time_buffer[-3] - self.time_buffer[-1])
        )


    def cleanup(self):
        self.logger.cleanup()
        self.write_dac(0.)
        self.ser.close()


if __name__ == '__main__': 
    th = Process(target=eavesdropper)
    th.start()

    print('Please input new PID parameters: Kp Ki Kd')
    kp, ki, kd = (float(_) for _ in input().split())
    pc = PIDController(7, "COM56", kp=kp, ki=ki, kd=kd)
    print('Current are %d, %d, %d' % (pc.kp, pc.ki, pc.kd))
    wl = pc.set_wavelength
    hp, offset = 200, 1e-4
    while True:
        pc.set_wavelength = wl + offset
        # pc.loop()

        for _ in range(hp):
            pc.loop()
            time.sleep(.05)

        pc.set_wavelength = wl - offset
        for _ in range(hp):
            pc.loop()
            time.sleep(.05)

        if not th.is_alive():
            pc.cleanup()
            print('Please input new PID parameters: Kp Ki Kd')
            print('Current are %d, %d, %d' % (pc.kp, pc.ki, pc.kd))
            kp, ki, kd = (float(_) for _ in input().split())
            pc = PIDController(7, "COM56", kp=kp, ki=ki, kd=kd)
            wl = pc.set_wavelength
            th = Process(target=eavesdropper)
            th.start()