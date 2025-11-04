import json
import os
import datetime
from robot import run as robot_run
import openmeteo_requests
import requests_cache
from retry_requests import retry
import utils.excel
import utils.meteo

INPUT_PATH = "input.json"
OUTPUT_PATH = "results.json"

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def main():
    print("Uruchamiam Robot Framework (Flashscore.robot)...")
    rc = robot_run(
        "Flashscore.robot",
        variable=[f"INPUT_PATH:{INPUT_PATH}", f"OUTPUT_PATH:{OUTPUT_PATH}"]
    )
    if rc != 0:
        raise SystemExit(f"Robot zwrócił kod {rc}")
    print("Robot zakończył pracę.")
    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            input_data = json.load(f)["footballFixturesAutomationInput"]
    except Exception as e:
        print(f"Nie można wczytać pliku {INPUT_PATH}: {e}")
        return
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            results_data = json.load(f)
    except Exception as e:
        print(f"Nie można wczytać pliku {OUTPUT_PATH}: {e}")
        return
    coord_lookup = {
        item["leagueName"]: {
            "country": item.get("country", "N/A"),
            "latitude": item["latitude"],
            "longitude": item["longitude"]
        } for item in input_data
    }
    print("\n" + "=" * 60)
    print(f"Pobrano {len(results_data)} lig z Robota. Rozpoczynam przetwarzanie...")
    print("=" * 60)
    for league_result in results_data:
        league_name = league_result.get("leagueName")
        if not league_name:
            continue
        print(f"\nLiga: {league_name}")
        if league_name not in coord_lookup:
            print(f"  BŁĄD: Brak współrzędnych dla '{league_name}' w {INPUT_PATH}")
            continue
        coords = coord_lookup[league_name]
        meteo_data = utils.get_meteo_data(coords["latitude"], coords["longitude"])
        if not meteo_data:
            print("  Nie udało się pobrać danych pogodowych.")
            continue
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H-%M")
        folder_name = f"{timestamp} {league_name}"
        folder_name = folder_name.replace(":", "").replace("/", "").replace("\\", "")
        try:
            os.makedirs(folder_name, exist_ok=True)
        except OSError as e:
            print(f"  BŁĄD: Nie można utworzyć folderu '{folder_name}': {e}")
            continue
        meteo_json_path = os.path.join(folder_name, "meteo.json")
        try:
            with open(meteo_json_path, "w", encoding="utf-8") as f:
                json.dump(meteo_data, f, indent=2, ensure_ascii=False)
            print(f"  Zapisano dane meteo w: {meteo_json_path}")
        except Exception as e:
            print(f"  BŁĄD: Nie można zapisać pliku meteo.json: {e}")
        country = coords.get("country", "N/A")
        table_data = league_result.get("table", [])
        excel_path = utils.save_league_to_excel(
            league_name,
            country,
            table_data,
            meteo_data,
            folder_name
        )
        if excel_path:
            print(f"  Zapisano dane Excel w: {excel_path}")
        weather = meteo_data["current_weather"]
        print(f"  Temperatura: {weather['temperature_celsius']}°C / {weather['temperature_fahrenheit']}°F")
        print(f"  Data pomiaru: {weather['time_utc']}")
        if table_data:
            print(f"  Tabela (top 2): {table_data[:2]}")
        else:
            print("  Brak pobranych danych tabeli.")

    print("\n" + "=" * 60)
    print("Przetwarzanie wszystkich lig zakończone.")

if __name__ == "__main__":
    main()