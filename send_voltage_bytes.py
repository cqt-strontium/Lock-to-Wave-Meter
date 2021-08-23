import serial 
import time 

def get_line_msg(ser):
    return ser.readline().decode('ansi') 


def send_voltage(ser, voltage): 
    '''
    Send voltage (between -10 and +10) to Arduino through Serial object ser
    '''

    number = int(voltage / 6. * 65535)
    if number > 32767 or number < -32768:
        raise Exception('Invalid input')
        
    ser.write(number.to_bytes(2, 'big', signed=True))

    time.sleep(.02)  # hold on a while for the Arduino reply
    while ser.in_waiting:
        print(get_line_msg(ser).strip())  # remove unwanted newline characters
        time.sleep(.02)  # hold on a while in case there's multiple lines coming 

if __name__ == '__main__': 
    ser = serial.Serial('COM4', 115200, timeout=1) 
    
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
            
    print('Arduino is ready. ')
    while True:
        send_voltage(ser, float(input('Input your voltage:')))
        