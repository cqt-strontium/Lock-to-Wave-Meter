import serial 
import time 

def get_line_msg():
    return ser.readline().decode('ansi') 


def send_voltage(ser, voltage): 
    '''
    Send voltage (between -10 and +10) to Arduino through Serial object ser
    '''

    number = int((voltage + 10.) / 20. * 65535.)
    if number > 65535 or number < 0:
        raise Exception('Invalid input')
    # number = 65536
    ser.write(bytes(str(number)+'#', 'ansi'))
    
    time.sleep(1)  # hold on a while for the Arduino reply
    while ser.in_waiting:
        print(get_line_msg().strip())  # remove unwanted newline characters
        time.sleep(.1)  # hold on a while in case there's multiple lines coming 

if __name__ == '__main__': 
    ser = serial.Serial('COM4', timeout=2) 
    
    # Arduino will send back "Arduino setup finished!" once it's all set
    while True: 
        msg = get_line_msg()
        if not msg.find('Control'):  
            print(msg.strip())
        elif msg.find('Arduino') == -1: 
            time.sleep(1)
        else: 
            break
    print('Arduino is ready. ')
    while True:
        send_voltage(ser, float(input('Input your voltage:')))
        