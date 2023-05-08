import asyncio
import aqi
from csv import DictWriter
from datetime import datetime
import json
import multiprocessing
import re
import requests
import serial
import statistics
import subprocess
import sys
import time
import RPi.GPIO as GPIO
from sps30.sps30 import SPS30
from settings import current_geolocation, openweather_api_key

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(11, GPIO.FALLING, bouncetime=200)

GPIO.setup(13, GPIO.OUT)

arduino_mode = True

global window_resistance
global aqi_list
window_resistance = []
aqi_list = []


def setup():
    global arduino_mode
    try:
        with open('button_state.json') as f:
            button_state = json.load(f)
            arduino_mode = button_state['power']
    except FileNotFoundError:
        print("No information about button power state available.")

    if not arduino_mode:
        subprocess.run(['sudo', 'uhubctl', '-l', '2', '-a', '1'], stdout=subprocess.DEVNULL)
        GPIO.output(13, GPIO.HIGH)

def close_down():
    global arduino_mode
    if not arduino_mode:
        subprocess.run(['sudo', 'uhubctl', '-l', '2', '-a', '0'], stdout=subprocess.DEVNULL)
        GPIO.output(13, GPIO.LOW)

def connect_serial(ports=['ttyACM0', 'ttyACM1']):
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

def serial_read(connection, window_resistance, n=20):
    ser = None
    for _ in range(n+1):
        try:
            value = None
            while not value:
                if ser:
                    reading = ser.readline().decode('utf8')
                    value = re.search('[0-9]+', reading)
                else:
                    time.sleep(0.1)
                    ser=connect_serial()
            window_resistance.append(int(value.group()))
        except serial.serialutil.SerialException:
            ser = connect_serial()
        time.sleep(1)
    window_resistance.pop(0)
    connection.send(window_resistance)

def sps_read(connection, aqi_list, n=20):
    pm_sensor = SPS30()
    pm_sensor.start_measurement()
    for _ in range(n+1):
        try:
            measurement = None
            while not measurement:
                measurement = pm_sensor.get_measurement()                
                if measurement:
                    aqi_list.append(int(aqi.to_aqi([
                        (aqi.POLLUTANT_PM25, str(measurement['sensor_data']['mass_density']['pm2.5'])),
                        (aqi.POLLUTANT_PM10, str(measurement['sensor_data']['mass_density']['pm10'])),
                        ])))
        except KeyboardInterrupt:
            print("Stopping measurement...")
            pm_sensor.stop_measurement()
            sys.exit() 
        time.sleep(1)
    pm_sensor.stop_measurement()
    aqi_list.pop(0)
    connection.send(aqi_list)

def fetch_pollution():
    req = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={current_geolocation["latitude"]}&lon={current_geolocation["longitude"]}&appid={openweather_api_key}'
    data = requests.get(req).text
    aqi = int(aqi.to_aqi([
                        (aqi.POLLUTANT_PM25, str(data['list'][1]['components']['pm2_5'])),
                        (aqi.POLLUTANT_PM10, str(data['list'][1]['components']['pm10'])),
                        ]))
    return aqi

def write_to_file(aqi, window, path='air_data.csv'):
    with open(path, 'a') as f_object:
        data_dict = {}
        field_names = ['timestamp', 'AQI', 'Window open', 'Outside AQI']
        data_dict['timestamp'] = str(datetime.now())
        data_dict['AQI'] = str(aqi)
        data_dict['Window open'] = str(window < 50)
        data_dict['Outside AQI'] = fetch_pollution()
        dictwriter_object = DictWriter(f_object, fieldnames=field_names)
        # Pass the dictionary as an argument to the Writerow()
        dictwriter_object.writerow(data_dict)
        # Close the file object
        f_object.close()

def main():
    global window_resistance
    global aqi_list
    print("Initialising...")
    setup()
    conn11, conn12 = multiprocessing.Pipe()
    conn21, conn22 = multiprocessing.Pipe()
    p1 = multiprocessing.Process(target=serial_read, args=(conn12, window_resistance,))
    p2 = multiprocessing.Process(target=sps_read, args=(conn22, aqi_list,))
    p1.start()
    p2.start()
    window_resistance = conn11.recv()
    aqi_list = conn21.recv()
    p1.join()
    p2.join()
    close_down()
    w =  int(statistics.median(window_resistance))
    aqi =  int(statistics.median(aqi_list))
    write_to_file(aqi, w)
    print("Done.")    
main()