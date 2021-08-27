import time
from wlm import getWaveLengthAt
from collections import deque
from time import perf_counter
from send_voltage_bytes import send_voltage, setup_arduino_port
from scipy.integrate import trapz
from logger import Logger 



class PIDController():
    def __init__(self, channel, port, wavelength=None, kp=-20., ki=-20., kd=-20., buffer_length=10):
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
        

        self.logger = Logger(list(zip(self.time_buffer, self.error_buffer)), header=r'Target wavelength %.6f nm\nKp=%.1f, Ki=%.1f, Kd=%.1f\n$'%(self.set_wavelength, self.kp, self.ki, self.kd))
    

    def setup_buffer(self):
        self.error_buffer = deque()
        self.time_buffer = deque()  # records the time stamp when a measurement is done
        
        for _ in range(self.buffer_length):
            error = self.read_wlm() - self.set_wavelength
            self.error_buffer.append(error)
            self.time_buffer.append(perf_counter())

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
            
        self.logger.log([self.time_buffer[-1], self.error_buffer[-1], self.kp * error, self.ki * trapz(self.error_buffer, self.time_buffer) /
            (self.time_buffer[-1] - self.time_buffer[0]), self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
                         ) / (self.time_buffer[-2] - self.time_buffer[-1])])
        
        self.write_dac(
            self.kp * error
            + self.ki * trapz(self.error_buffer, self.time_buffer) /
            (self.time_buffer[-1] - self.time_buffer[0])
            + self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
                         ) / (self.time_buffer[-2] - self.time_buffer[-1])
        )


# pc = PIDController(8, get_com_port())
pc = PIDController(7, "COM56", offline=False)
while True:
    pc.loop()
    # if pc.need_calibration():
    #     pc.calibrate()
    time.sleep(.05)