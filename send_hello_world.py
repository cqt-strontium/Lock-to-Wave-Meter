import serial

ser = serial.Serial(port='COM3', timeout=2)

if not ser.in_waiting:
    print(ser.readline())  # let us see if there's any rubbish, usually there is. 

msg = 'hello world!'

ser.write(bytes(msg, 'utf-8'))
if not ser.in_waiting:
    print(ser.readline().decode('utf-8'))
