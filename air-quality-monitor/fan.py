import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.OUT)

try:
    GPIO.output(16, GPIO.HIGH)
except KeyboardInterrupt:
    print('Fan unavailable.')
