import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import datetime # Dodany import do formatowania czasu

# Setup the Open-Meteo API client (BEZ ZMIAN)
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# URL (BEZ ZMIAN)
url = "https://api.open-meteo.com/v1/forecast"

# Parametry (ZMIENIONE)
params = {
	"latitude": 52.52,
	"longitude": 13.41,
    # Prosimy o aktualną temperaturę. Domyślną jednostką jest Celsius.
	"current": "temperature_2m",
	# Usunięto 'hourly', 'start_date', 'end_date'
}
responses = openmeteo.weather_api(url, params=params)

# Przetwarzanie odpowiedzi (BEZ ZMIAN)
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")


# --- NOWA SEKCJA - PRZETWARZANIE AKTUALNEJ POGODY ---

# Zamiast danych godzinowych (hourly), bierzemy aktualne (current)
current = response.Current()

# Poprosiliśmy tylko o "temperature_2m", więc jest pod indeksem 0
# .Value() pobiera pojedynczą aktualną wartość
current_temperature_celsius = current.Variables(0).Value()

# Obliczamy stopnie Fahrenheita
current_temperature_fahrenheit = (current_temperature_celsius * 9/5) + 32

# Pobieramy aktualny czas pomiaru i formatujemy go
current_time = datetime.datetime.fromtimestamp(current.Time(), datetime.timezone.utc)

# Drukujemy wyniki
print("\nAktualna pogoda:")
print(f"Czas pomiaru: {current_time.strftime('%Y-%m-%d %H:%M %Z')}")
print(f"Temperatura: {current_temperature_celsius:.2f} °C")
print(f"Temperatura: {current_temperature_fahrenheit:.2f} °F")

# Usunięto całą sekcję przetwarzania 'hourly' i 'pandas'