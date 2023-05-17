from .calibrator import Calibrator
from util.wlm import getWaveLength
from collections import deque
from time import perf_counter
from util.send_voltage_bytes import setup_arduino_port
from scipy.integrate import trapz
from util.logger import Logger 


class PIDController():
    get_wl = getWaveLength
    
    def __init__(self, channel, port, sspin=10, wavelength=None, kp=-800., ki=-1000./1.2, kd=-10., buffer_length=10):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.channel = channel
        self.port = port
        self.sspin = sspin

        self.ser = setup_arduino_port(port, 115200)
        
        self.get_wl = lambda : PIDController.get_wl()(channel)
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
        num = int(voltage / 6. * 65535)
        num = min(max(num, -32768), 32767)
        # self.ser.write(self.sspin.to_bytes(1, 'little'))
        self.ser.write(num.to_bytes(2, 'big', signed=True))


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
            
        # reset the integral if it becomes too large (due to fiber/wave meter glitches)
        if abs(self.int * self.ki) > 3.:  
            self.int = 0.
        print(f'{self.channel}: {self.error_buffer[-1]}')
        self.logger.log([self.time_buffer[-1], self.error_buffer[-1], self.kp * error, self.ki * self.int, self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
                         ) / (self.time_buffer[-2] - self.time_buffer[-1])])
        
        self.write_dac(
            self.kp * error
            + self.ki * self.int
            + self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
                         ) / (self.time_buffer[-2] - self.time_buffer[-1])
        )

    def calibrate(self):
        Calibrator(self.write_dac, self.get_wl).calibrate()
        return self

    def cleanup(self):
        self.logger.cleanup()
        self.write_dac(0.)
