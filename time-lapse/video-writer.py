import cv2
import numpy as np
import glob
import os

frameSize = (1024, 768)

out = cv2.VideoWriter('output_video.avi', cv2.VideoWriter_fourcc(*'DIVX'), 60, frameSize)
filenames = glob.glob('/home/pi/Documents/time-lapse/*.jpg')

for filename in sorted(filenames):
    print(filename)
    img = cv2.imread(filename)
    out.write(img)

print('Releasing')
out.release()
print('Released.')