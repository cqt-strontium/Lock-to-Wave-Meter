import serial 
import time 

def get_line_msg(ser):
    return ser.readline().decode('ansi') 

def get_msg(ser):
    return ser.read().decode('ansi') 


def send_voltage(ser, voltage, readback=False): 
    '''
    Send voltage (between -10 and +10) to Arduino through Serial object ser
    '''

    number = int(voltage / 6. * 65535)
    if number > 32767 or number < -32768:
        raise Exception('Invalid input')
        
    ser.write(number.to_bytes(2, 'big', signed=True))
    
    if readback:
        time.sleep(.02)  # hold on a while for the Arduino reply
        while ser.in_waiting:
            print(get_line_msg(ser).strip())  # remove unwanted newline characters
            time.sleep(.02)  # hold on a while in case there's multiple lines coming 


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
    ser = setup_arduino_port('COM4')
    print('Arduino is ready. ')
    while True:
        send_voltage(ser, float(input('Input your voltage:')), True)
        