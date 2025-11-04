import openmeteo_requests
import requests_cache
from retry_requests import retry
import datetime # Dodany import do formatowania czasu

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)
url = "https://api.open-meteo.com/v1/forecast"

params = {
	"latitude": 52.52,
	"longitude": 13.41,
	"current": "temperature_2m",
}
responses = openmeteo.weather_api(url, params=params)
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
current = response.Current()
current_temperature_celsius = current.Variables(0).Value()
current_temperature_fahrenheit = (current_temperature_celsius * 9/5) + 32
current_time = datetime.datetime.fromtimestamp(current.Time(), datetime.timezone.utc)
print("\nAktualna pogoda:")
print(f"Czas pomiaru: {current_time.strftime('%Y-%m-%d %H:%M %Z')}")
print(f"Temperatura: {current_temperature_celsius:.2f} °C")
print(f"Temperatura: {current_temperature_fahrenheit:.2f} °F")

def get_meteo_data(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m",
        "temperature_unit": "fahrenheit",
    }
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        current = response.Current()
        current_temp_f = current.Variables(0).Value()
        current_temp_c = (current_temp_f - 32) * 5 / 9
        current_time_utc = datetime.datetime.fromtimestamp(current.Time(), datetime.timezone.utc)
        parsed_data = {
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
            "elevation": response.Elevation(),
            "utc_offset_seconds": response.UtcOffsetSeconds(),
            "current_weather": {
                "time_utc": current_time_utc.isoformat(),
                "temperature_celsius": round(current_temp_c, 2),
                "temperature_fahrenheit": round(current_temp_f, 2)
            }
        }
        return parsed_data

    except Exception as e:
        print(f"  BŁĄD API Meteo dla ({latitude}, {longitude}): {e}")
        return None