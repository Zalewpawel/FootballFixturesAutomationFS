import json
import os
import datetime
import logging
from robot import run as robot_run
from utils.save_excel import save_league_to_excel
from utils.save_meteo import get_meteo_data
from config import INPUT_PATH, OUTPUT_PATH, DATA_FOLDER

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    os.makedirs(DATA_FOLDER, exist_ok=True)
    logging.info("Uruchamiam Robot Framework (Flashscore.robot)...")
    rc = robot_run(
        "Flashscore.robot",
        variable=[f"INPUT_PATH:{INPUT_PATH}", f"OUTPUT_PATH:{OUTPUT_PATH}"]
    )
    if rc != 0:
        logging.critical(f"Robot zwrócił kod {rc}. Zatrzymuję skrypt.")
        raise SystemExit(f"Robot zwrócił kod {rc}")
    logging.info("Robot zakończył pracę.")
    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            input_data = json.load(f)["footballFixturesAutomationInput"]
    except Exception as e:
        logging.critical(f"Nie można wczytać pliku {INPUT_PATH}: {e}. Zatrzymuję skrypt.")
        return
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            results_data = json.load(f)
    except Exception as e:
        logging.critical(f"Nie można wczytać pliku {OUTPUT_PATH}: {e}. Zatrzymuję skrypt.")
        return
    coord_lookup = {
        item["leagueName"]: {
            "country": item.get("country", "N/A"),
            "latitude": item["latitude"],
            "longitude": item["longitude"]
        } for item in input_data
    }
    logging.info("=" * 60)
    logging.info(f"Pobrano {len(results_data)} lig z Robota. Rozpoczynam przetwarzanie...")
    logging.info("=" * 60)
    for league_result in results_data:
        league_name = league_result.get("leagueName")
        if not league_name:
            continue
        logging.info(f"--- Przetwarzanie ligi: {league_name} ---")
        if league_name not in coord_lookup:
            logging.warning(f"Brak współrzędnych dla '{league_name}' w {INPUT_PATH}. Pomijam tę ligę.")
            continue
        coords = coord_lookup[league_name]
        meteo_data = get_meteo_data(coords["latitude"], coords["longitude"])
        if not meteo_data:
            logging.warning(f"Nie udało się pobrać danych pogodowych dla '{league_name}'. Pomijam tę ligę.")
            continue
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H-%M")
        safe_league_name = league_name.replace(":", "").replace("/", "").replace("\\", "")
        folder_name_base = f"{timestamp} {safe_league_name}"
        folder_path = os.path.join(DATA_FOLDER, folder_name_base)
        try:
            os.makedirs(folder_path, exist_ok=True)
        except OSError as e:
            logging.error(f"Nie można utworzyć folderu '{folder_path}': {e}. Pomijam tę ligę.")
            continue
        meteo_json_path = os.path.join(folder_path, "meteo.json")
        try:
            with open(meteo_json_path, "w", encoding="utf-8") as f:
                json.dump(meteo_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Zapisano dane meteo w: {meteo_json_path}")
        except Exception as e:
            logging.error(f"Nie można zapisać pliku meteo.json: {e}")
        country = coords.get("country", "N/A")
        table_data = league_result.get("table", [])
        excel_path = save_league_to_excel(
            league_name,
            country,
            table_data,
            meteo_data,
            folder_path
        )
        if excel_path:
            logging.info(f"Zapisano dane Excel w: {excel_path}")
        weather = meteo_data["current_weather"]
        logging.info(f"Temperatura: {weather['temperature_celsius']}°C / {weather['temperature_fahrenheit']}°F")
        logging.info(f"Data pomiaru: {weather['time_utc']}")
        if table_data:
            logging.info(f"Tabela (top 2): {table_data[:2]}")
        else:
            logging.info("Brak pobranych danych tabeli.")
    logging.info("=" * 60)
    logging.info("Przetwarzanie wszystkich lig zakończone.")
if __name__ == "__main__":
    main()