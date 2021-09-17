import serial 
import time 

def get_line_msg(ser):
    return ser.readline().decode('ansi') 

def get_msg(ser):
    return ser.read().decode('ansi') 


def send_voltage(ser, voltage, sspin=10, readback=False): 
    '''
    Send voltage (between -3 and +3) to Arduino through Serial object ser
    '''

    number = int(voltage / 6. * 65535)
    if number > 32767:
        number = 32767
    if number < -32768:
        number = -32768

    ser.write(sspin.to_bytes(1, 'big', signed=True))    
    ser.write(number.to_bytes(2, 'big', signed=True))
    
    if readback:
        time.sleep(.02)  # hold on a while for the Arduino reply
        while ser.in_waiting:
            print(get_line_msg(ser).strip())  # remove unwanted newline characters
            time.sleep(.02)  # hold on a while in case there's multiple lines coming 


class CachedPort:
    ports = {}
    def __init__(self, func) -> None:
        self.func = func
        
    def __call__(self, *args):
        if args[0] in CachedPort.ports:
            return CachedPort.ports[args[0]]
        CachedPort.ports[args[0]] = self.func(*args)
        return CachedPort.ports[args[0]]


@CachedPort
def setup_arduino_port(port, baud=115200, timeout=1):
    ser = serial.Serial(port, baud, timeout=timeout) 
    
    # Arduino will send back "Arduino setup finished!" once it's all set
    while True: 
        msg = get_line_msg(ser)
        if not msg.strip():
            time.sleep(1)
        else:   
            if msg.find('Control') + 1: 
                print(msg.strip())
            if msg.find('Arduino') + 1: 
                break
    return ser
           
           

if __name__ == '__main__': 
    ser = setup_arduino_port('COM3')
    print('Arduino is ready. ')
    while True:
        send_voltage(ser, float(input('Input your voltage:')), True)
        