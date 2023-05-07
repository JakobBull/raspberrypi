from csv import DictWriter
from datetime import datetime
import sys
import json
from time import sleep
from sps30 import SPS30

file_names = {"mass_density": ["pm1.0", "pm2.5", "pm4.0", "pm10"],
              "particle_count": ["pm0.5", "pm1.0", "pm2.5", "pm4.0", "pm10"]}

if __name__ == "__main__":
    pm_sensor = SPS30()
    pm_sensor.start_measurement()
    
    while True:
        try:
            measurement = pm_sensor.get_measurement()
            if measurement:
                print(measurement)
                break

        except KeyboardInterrupt:
            print("Stopping measurement...")
            pm_sensor.stop_measurement()
            sys.exit()
    
    pm_sensor.stop_measurement()
    
    for category, headers in file_names.items():
        field_names = [key+"_"+suffix for key, suffices in file_names.items() for suffix in suffices]
        data_dict = {key+"_"+suffix: measurement["sensor_data"][key][suffix] for key, suffices in file_names.items() for suffix in suffices}
        field_names.insert(0, "timestamp")
        data_dict["timestamp"] = str(datetime.now())

    # List that we want to add as a new row 
    # Open our existing CSV file in append mode
    # Create a file object for this file
    with open('/home/pi/Documents/air-quality-monitor/air_data.csv', 'a') as f_object:
    
        dictwriter_object = DictWriter(f_object, fieldnames=field_names)
        # Pass the dictionary as an argument to the Writerow()
        print("data\n", data_dict)
        dictwriter_object.writerow(data_dict)
    
        # Close the file object
        f_object.close()
        
    print("Written to file.")
    sys.exit()