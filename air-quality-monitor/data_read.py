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

global data_dict
global aqi_list
data_dict = {'Pressure': [], 'CO2': [], 'TVOC': []}
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

def serial_read(connection, data_dict = {'Pressure': [], 'CO2': [], 'TVOC': []}, n=5):
    ser = None
    print('Serial read...')
    enough_readings = False
    while not enough_readings:
        if ser:
            reading = ser.readline().decode('utf8')
            match = lambda key, text: re.search(f'{key} - (.+?);', text)
            for pollutant in data_dict.keys():
                match_obj = match(pollutant, reading)
                if match_obj:
                    found = match_obj.group(1)
                    if len(data_dict[pollutant]) < n+25:
                        data_dict[pollutant].append(int(found))
                    else:
                        sufficient_lengths = [(len(data_dict[pollutant]) == n+25) for pollutant in data_dict.keys()]
                        enough_readings = True if all(sufficient_lengths) else False
        else:
            time.sleep(0.1)
            ser=connect_serial()
    time.sleep(1)
    print('Serial read terminated...')
    data_dict = {key: data_dict[key][25:] for key in data_dict.keys()}
    connection.send(data_dict)

def sps_read(connection, aqi_list, n=20):
    print("SPS read...")
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
    print("SPS read terminated...")
    pm_sensor.stop_measurement()
    aqi_list.pop(0)
    connection.send(aqi_list)

def get_aqi(item):
    return int(aqi.to_aqi([
                        (aqi.POLLUTANT_PM25, str(item['pm2_5'])),
                        (aqi.POLLUTANT_PM10, str(item['pm10'])),
                        ]))

def to_hours(time_object):
    return str(int(time_object.days*24 + time_object.seconds/3600))

def fetch_pollution():
    req = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={current_geolocation['latitude']}&lon={current_geolocation['longitude']}&appid={openweather_api_key}"
    print("Fetching...")
    data = requests.get(req)
    print("Fetched...")
    start_time = datetime.fromtimestamp(data.json()["list"][0]['dt'])
    aqis = {to_hours((datetime.fromtimestamp(item['dt'])-start_time)): get_aqi(item['components']) for item in data.json()["list"]}
    return aqis

def fetch_weather():
    req  = f"https://api.openweathermap.org/data/2.5/weather?lat={current_geolocation['latitude']}&lon={current_geolocation['longitude']}&appid={openweather_api_key}"
    print("Fetching...")
    data = requests.get(req).json()
    print("Fetched...")
    wind_speed = data["wind"]["windspeed"]
    wind_dir = data["wind"]["dir"]
    wind_gust = data["wind"]["gust"]
    return wind_speed, wind_dir, wind_gust




def write_to_file(aqi, resistance, co2, tvoc, path='/home/jakob/Documents/raspberrypi/air-quality-monitor/air_data.csv'):
    with open(path, 'a') as f_object:
        data_dict = {}
        field_names = ['timestamp', 'AQI', 'Window open', 'CO2', 'TVOC', 'Outside AQI'] + [str(integer) for integer in range(1, 73)] + ['Wind speed', "Wind direction", "Wind direction"]
        data_dict['timestamp'] = str(datetime.now())
        data_dict['AQI'] = str(aqi)
        data_dict['Window open'] = str(resistance < 50)
        data_dict['CO2'] = co2
        data_dict['TVOC'] = tvoc
        pollution_forecast = fetch_pollution()
        data_dict['Outside AQI'] = pollution_forecast["0"]
        del pollution_forecast["0"]
        for integer in range(1, 73):
            data_dict[str(integer)] = pollution_forecast[str(integer)]
        wind_speed, wind_dir, wind_gust = fetch_weather()
        data_dict["Wind speed"] = wind_speed
        data_dict["Wind direcion"] = wind_dir
        data_dict["Wind gust"] = wind_gust
        dictwriter_object = DictWriter(f_object, fieldnames=field_names)
        # Pass the dictionary as an argument to the Writerow()
        dictwriter_object.writerow(data_dict)
        # Close the file object
        f_object.close()

def main():
    global data_dict
    global aqi_list
    print("Initialising...")
    GPIO.output(13, GPIO.HIGH)
    #setup()
    conn11, conn12 = multiprocessing.Pipe()
    conn21, conn22 = multiprocessing.Pipe()
    p1 = multiprocessing.Process(target=serial_read, args=(conn12, data_dict,))
    p2 = multiprocessing.Process(target=sps_read, args=(conn22, aqi_list,))
    p1.start()
    p2.start()
    data_dict = conn11.recv()
    aqi_list = conn21.recv()
    p1.join()
    p2.join()
    #close_down()
    resistance = int(statistics.median(data_dict['Pressure']))
    co2 = int(statistics.median(data_dict['CO2']))
    tvoc = int(statistics.median(data_dict['TVOC']))
    aqi =  int(statistics.median(aqi_list))
    print("Writing to file...")
    write_to_file(aqi, resistance, co2, tvoc)
    print("Done.")
main()