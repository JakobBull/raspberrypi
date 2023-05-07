from airpyllution.airpyllution import get_air_pollution
import requests
from settings import current_geolocation, openweather_api_key

req = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={current_geolocation["latitude"]}&lon={current_geolocation["longitude"]}&appid={openweather_api_key}'
print(req)
print(requests.get(req).text)
#print(type(get_air_pollution(current_geolocation['latitude'], current_geolocation['longitude'], openweather_api_key, "Current Air Pollution")))