import datetime
import json
import logging
import os

from robot import run as robot_run

from Config.config import DATA_FOLDER, INPUT_PATH, OUTPUT_PATH
from utils.save_excel import save_league_to_excel
from utils.save_meteo import get_meteo_data


def main():
    """
    Main function for the automation pipeline.

    This function coordinates the entire process:
    1. Sets up logging.
    2. Runs the Robot Framework task to scrape Flashscore data.
    3. Loads the input leagues (from input.json) and the scraped results (from results.json).
    4. Iterates through each league.
    5. Fetches current weather data from Open-Meteo API.
    6. Creates a timestamped directory for the league's output.
    7. Saves the raw weather data to 'meteo.json'.
    8. Saves the combined weather data and league table to an Excel file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    os.makedirs(DATA_FOLDER, exist_ok=True)
    logging.info("Running Robot Framework (Flashscore.robot)...")
    rc = robot_run(
        "Flashscore.robot",
        variable=[f"INPUT_PATH:{INPUT_PATH}", f"OUTPUT_PATH:{OUTPUT_PATH}"],
    )
    if rc != 0:
        logging.critical(f"Robot Framework exited with code {rc}. Stopping script.")
        raise SystemExit(f"Robot Framework exited with code {rc}")
    logging.info("Robot Framework task finished.")
    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            input_data = json.load(f)["footballFixturesAutomationInput"]
    except Exception as e:
        logging.critical(
            f"Failed to read file {INPUT_PATH}: {e}. Stopping script."
        )
        return
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            results_data = json.load(f)
    except Exception as e:
        logging.critical(
            f"Failed to read file {OUTPUT_PATH}: {e}. Stopping script."
        )
        return
    coord_lookup = {
        item["leagueName"]: {
            "country": item.get("country", "N/A"),
            "latitude": item["latitude"],
            "longitude": item["longitude"],
        }
        for item in input_data
    }
    logging.info("=" * 60)
    logging.info(
        f"Loaded {len(results_data)} leagues from Robot. Starting processing..."
    )
    logging.info("=" * 60)
    for league_result in results_data:
        league_name = league_result.get("leagueName")
        if not league_name:
            continue
        logging.info(f"--- Processing league: {league_name} ---")
        if league_name not in coord_lookup:
            logging.warning(
                f"No coordinates found for '{league_name}' in {INPUT_PATH}. Skipping league."
            )
            continue
        coords = coord_lookup[league_name]
        meteo_data = get_meteo_data(coords["latitude"], coords["longitude"])
        if not meteo_data:
            logging.warning(
                f"Failed to fetch weather data for '{league_name}'. Skipping league."
            )
            continue
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H-%M")
        safe_league_name = (
            league_name.replace(":", "").replace("/", "").replace("\\", "")
        )
        folder_name_base = f"{timestamp} {safe_league_name}"
        folder_path = os.path.join(DATA_FOLDER, folder_name_base)
        try:
            os.makedirs(folder_path, exist_ok=True)
        except OSError as e:
            logging.error(
                f"Failed to create directory '{folder_path}': {e}. Skipping league."
            )
            continue
        meteo_json_path = os.path.join(folder_path, "meteo.json")
        try:
            with open(meteo_json_path, "w", encoding="utf-8") as f:
                json.dump(meteo_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved weather data to: {meteo_json_path}")
        except Exception as e:
            logging.error(f"Failed to save meteo.json: {e}")
        country = coords.get("country", "N/A")
        table_data = league_result.get("table", [])
        excel_path = save_league_to_excel(
            league_name, country, table_data, meteo_data, folder_path
        )
        if excel_path:
            logging.info(f"Saved Excel report to: {excel_path}")
        weather = meteo_data["current_weather"]
        logging.info(
            f"Temperature: {weather['temperature_celsius']}°C / {weather['temperature_fahrenheit']}°F"
        )
        logging.info(f"Measurement time (UTC): {weather['time_utc']}")
        if table_data:
            logging.info(f"Table (top 2): {table_data[:2]}")
        else:
            logging.info("No table data found.")
    logging.info("=" * 60)
    logging.info("Processing of all leagues finished.")


if __name__ == "__main__":
    main()