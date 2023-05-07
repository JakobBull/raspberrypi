import json
import subprocess
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(11, GPIO.FALLING, bouncetime=200)
arduino_mode = True

try:
    with open('button_state.json') as f:
        button_state = json.load(f)
        arduino_mode = button_state['power']
    subprocess.run(['sudo', 'uhubctl', '-l', '2', '-a', str(int(arduino_mode))], stdout=subprocess.DEVNULL)
except FileNotFoundError:
    print("No information about button power state available.")
            
def response():
    global arduino_mode
    while True:
        if GPIO.event_detected(11):
            print("Button was pushed!")
            arduino_mode = not arduino_mode
            print('Running power subprocess with:', str(int(arduino_mode)))
            subprocess.run(['sudo', 'uhubctl', '-l', '2', '-a', str(int(arduino_mode))], stdout=subprocess.DEVNULL)
            button_state = json.dumps({'power': arduino_mode})
            with open('button_state.json', 'w') as f:
                f.write(button_state)
        else:
            print("Waiting...", end='\r')
        time.sleep(10)
    
response()