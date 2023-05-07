import serial
import time

def connect(ports=['ttyACM0', 'ttyACM1']):
    for port in ports:
        try:
            ser = serial.Serial(
                port=f'/dev/{port}',
                
                baudrate=9600,
                
                parity=serial.PARITY_NONE,
                
                stopbits=serial.STOPBITS_ONE,
                
                bytesize=serial.EIGHTBITS,
                
                timeout=1
                )
            return ser
        except serial.serialutil.SerialException:
            print(f'Port {port} unavailable.')
    return None

ser = None
while True:
    if ser:
        try:
            print(ser.readline())
        except serial.serialutil.SerialException:
            ser = connect()
    else:
        ser = connect()
    time.sleep(0.1)

