import time
from wlm import getWaveLengthAt
from collections import deque
from time import perf_counter
from send_voltage_bytes import send_voltage, setup_arduino_port
from scipy.integrate import trapz
from get_comport import get_com_port
from online_figure import OnlineFigure
from logger import Logger 
from calibrator import Calibrator 
from scipy.interpolate import root_scalar 


class PIDController():
    fake_read_wlm_pos = -1
    def __init__(self, channel, port, wavelength=None, kp=-20., ki=-20., kd=-20., buffer_length=10, offline=False):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.channel = channel
        self.port = port
        if offline:    
            # self.read_wlm = self.fake_read_wlm
            self.write_dac = self.fake_write_dac
        else:
            self.ser = setup_arduino_port(port)
        
        self.get_wl = getWaveLengthAt(channel)
        if not wavelength:
            wavelength = self.get_wl()
        self.set_wavelength = wavelength
        
        self.buffer_length = buffer_length
        self.setup_buffer()
        self.offset = 0. 

        self.fig = OnlineFigure(self.time_buffer, self.error_buffer)
        self.fig.ax.set_title(r'Target wavelength $\lambda_0=%.6f\,\mathrm{nm}$'%self.set_wavelength)
        self.fig.ax.set_xlabel(r'Time elapsed $t\,/\,\mathrm{s}$')
        self.fig.ax.set_ylabel(r'Error $e=\lambda-\lambda_0\,/\,\mathrm{nm}$')


        self.logger = Logger(list(zip(self.time_buffer, self.error_buffer)))
    

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
        wl = self.get_wl()
        while wl - self.set_wavelength == self.error_buffer[-1]: 
            wl = self.get_wl()
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


    def need_calibration(self, threshold=5e-5):
        return abs(self.error_buffer[-1]) > threshold 


    def calibrate(self):
        cl = Calibrator(self.write_dac, self.read_wlm) 
        calibrated_function = cl.calibrate()
        self.offset = root_scalar(lambda _: calibrated_function(_) -self.set_wavelength - self.error_buffer[-1], bracket=[-1, 1])
        self.write_dac(self.offset)
        self.setup_buffer()


    def loop(self):
        '''
        Main PID loop
        '''
        error = self.read_wlm() - self.set_wavelength

        self.time_buffer.append(perf_counter())
        self.error_buffer.append(error)
        self.time_buffer.popleft()
        self.error_buffer.popleft()
            
        self.fig.append(self.time_buffer[-1], self.error_buffer[-1])
        
        self.logger.log([self.time_buffer[-1], self.error_buffer[-1], self.kp * error, self.ki * trapz(self.error_buffer, self.time_buffer) /
            (self.time_buffer[-1] - self.time_buffer[0]), self.kd * (self.error_buffer[-2] - self.error_buffer[-1]
                         ) / (self.time_buffer[-2] - self.time_buffer[-1])])
        
        self.write_dac(
            self.offset
            + self.kp * error
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