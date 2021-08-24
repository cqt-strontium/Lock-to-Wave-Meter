import serial.tools.list_ports as list_ports


def get_com_port():
    '''
    Return COM port name by testing. Saves the device manager step. 
    '''
    s = input("Unplug the Arduino device. Enter [y/Y] when done.\n")
    while not (s.strip().lower() == 'y' or not s.strip()):
        s = input("Unplug the Arduino device. Enter [y/Y] when done.\n")

    without_arduino = set(port.name for port in list_ports.comports())

    s = input("Replug the Arduino device. Enter [y/Y] when done.\n")
    while not (s.strip().lower() == 'y' or not s.strip()):
        s = input("Replug the Arduino device. Enter [y/Y] when done.\n")

    with_arduino = set(port.name for port in list_ports.comports())

    arduino = with_arduino - without_arduino
    if not len(arduino):
        raise Exception("No device event detected")
    
    if len(arduino) > 1:
        raise Exception("Multiple device events detected") 
    
    return arduino[0]

if __name__ == '__main__':
    get_com_port()