# Import writer class from csv module
from csv import DictWriter
from datetime import datetime

data_1 = {
  "sensor_data": {
    "mass_density": {
      "pm1.0": 2.883,
      "pm2.5": 5.889,
      "pm4.0": 7.232,
      "pm10": 7.7
    },
    "particle_count": {
      "pm0.5": 3.402,
      "pm1.0": 6.695,
      "pm2.5": 12.526,
      "pm4.0": 10.164,
      "pm10": 43.967
    },
    "particle_size": 1.63,
    "mass_density_unit": "ug/m3",
    "particle_count_unit": "#/cm3",
    "particle_size_unit": "um"
  },
  "timestamp": 1630217804
}

data_2 = {
  "sensor_data": {
    "mass_density": {
      "pm1.0": 2.883,
      "pm2.5": 5.889,
      "pm4.0": 7.232,
      "pm10": 7.7
    },
    "particle_count": {
      "pm0.5": 3.402,
      "pm1.0": 6.695,
      "pm2.5": 12.526,
      "pm4.0": 10.164,
      "pm10": 43.967
    },
    "particle_size": 1.63,
    "mass_density_unit": "ug/m3",
    "particle_count_unit": "#/cm3",
    "particle_size_unit": "um"
  },
  "timestamp": 1630217804
}

file_names = {"mass_density": ["pm1.0", "pm2.5", "pm4.0", "pm10"],
              "particle_count": ["pm0.5", "pm1.0", "pm2.5", "pm4.0", "pm10"]}

for data_item in [data_1, data_2]:

    for category, headers in file_names.items():
        field_names = [key+"_"+suffix for key, suffices in file_names.items() for suffix in suffices]
        data_dict = {key+"_"+suffix: data_item["sensor_data"][key][suffix] for key, suffices in file_names.items() for suffix in suffices}
        field_names.insert(0, "timestamp")
        data_dict["timestamp"] = str(datetime.now())

    # List that we want to add as a new row 
    # Open our existing CSV file in append mode
    # Create a file object for this file
    with open('air_data.csv', 'a') as f_object:
    
        dictwriter_object = DictWriter(f_object, fieldnames=field_names)
        # Pass the dictionary as an argument to the Writerow()
        dictwriter_object.writerow(data_dict)
    
        # Close the file object
        f_object.close()
        
        
        
        


if __name__ == "__main__":
    pm_sensor = SPS30()
    print(f"Firmware version: {pm_sensor.firmware_version()}")
    print(f"Product type: {pm_sensor.product_type()}")
    print(f"Serial number: {pm_sensor.serial_number()}")
    print(f"Status register: {pm_sensor.read_status_register()}")
    print(
        f"Auto cleaning interval: {pm_sensor.read_auto_cleaning_interval()}s")
    print(f"Set auto cleaning interval: {pm_sensor.write_auto_cleaning_interval_days(2)}s")
    pm_sensor.start_measurement()

    while True:
        try:
            print(json.dumps(pm_sensor.get_measurement(), indent=2))
            sleep(2)

        except KeyboardInterrupt:
            print("Stopping measurement...")
            pm_sensor.stop_measurement()
            sys.exit()