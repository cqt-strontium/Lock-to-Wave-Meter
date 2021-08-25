import time
from wlm import getWaveLengthAt
from collections import deque
from time import perf_counter
from send_voltage_bytes import send_voltage, setup_arduino_port
from scipy.integrate import trapz
from get_comport import get_com_port


class PIDController():
    fake_read_wlm_pos = -1
    def __init__(self, channel, port, wavelength=None, kp=1., ki=1., kd=1., buffer_length=10, offline=False):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.channel = channel
        self.port = port
        self.error_buffer = deque()
        self.time_buffer = deque()  # records the time stamp when a measurement is done
        
        if offline:    
            self.read_wlm = self.fake_read_wlm
            self.write_dac = self.fake_write_dac
        else:
            self.ser = setup_arduino_port(port)
        
        self.get_wl = getWaveLengthAt()
        if not wavelength:
            wavelength = self.read_wlm()
        self.set_wavelength = wavelength
        
        for _ in range(buffer_length):
            error = self.read_wlm() - self.set_wavelength
            self.error_buffer.append(error)
            self.time_buffer.append(perf_counter())

    def read_wlm(self):
        '''
        Returns the wavelength at the moment
        '''
        wl = self.get_wl(self.channel)
        while wl - self.set_wavelength == self.error_buffer[-1]: 
            wl = self.get_wl(self.channel)
        return wl 

    def fake_read_wlm(self):
        data = [707.2007608,
                707.2007595,
                707.2007597,
                707.2007611,
                707.2007597,
                707.2007595,
                707.2007595,
                707.2007578,
                707.2007582,
                707.2007582,
                707.2007602,
                707.200759,
                707.2007595,
                707.2007586,
                707.200759,
                707.2007596,
                707.2007582,
                707.2007613,
            ]
        PIDController.fake_read_wlm_pos += 1 
        return data[PIDController.fake_read_wlm_pos]


    def write_dac(self, voltage):
        '''
        Write to DAC device through Arduino 
        '''
        send_voltage(self.ser, voltage)

    def fake_write_dac(self, voltage):
        print(voltage)

        
    def loop(self):
        '''
        Main PID loop
        '''
        error = self.set_wavelength - self.read_wlm()

        self.time_buffer.append(perf_counter())
        self.error_buffer.append(error)
        self.time_buffer.popleft()
        self.error_buffer.popleft()
            
        
        print(self.kp * error)
        print(self.ki * trapz(self.error_buffer, self.time_buffer) /
            (self.time_buffer[-1] - self.time_buffer[0]))
        print(self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
                         ) / (self.time_buffer[-2] - self.time_buffer[-1]))
        print()
        # self.write_dac(
        #     self.kp * error
        #     + self.ki * trapz(self.error_buffer, self.time_buffer) /
        #     (self.time_buffer[-1] - self.time_buffer[0])
        #     + self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
        #                  ) / (self.time_buffer[-2] - self.time_buffer[-1])
        # )


# pc = PIDController(8, get_com_port())
pc = PIDController(8, "COM4", offline=True)
while True:
    pc.loop()
    time.sleep(.05)
