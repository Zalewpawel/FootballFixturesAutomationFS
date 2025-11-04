import datetime
import os
import logging
import pandas as pd


def save_league_to_excel(
    league_name, country, league_table_data, meteo_data, folder_path
):
    """
    Saves league and weather data to a formatted .xlsx file.

    Creates an Excel file with two parts:
    1. A header (row 1) containing metadata (Date, Country, Weather).
    2. The league standings table (starting from row 3), leaving a blank row.

    Args:
        league_name (str): The name of the league.
        country (str): The country of the league.
        league_table_data (list[dict]): A list of dictionaries, where each dict
                                       represents a team's row in the table.
        meteo_data (dict): The processed weather data from the Open-Meteo API.
        folder_path (str): The full path to the directory where the file
                           should be saved.

    Returns:
        str | None: The full path to the created .xlsx file if successful,
                    or None if an error occurred.
    """
    safe_league_name = league_name.replace(":", "").replace("/", "").replace("\\", "")
    file_path = os.path.join(folder_path, f"{safe_league_name}.xlsx")
    try:
        header_info = {
            "Date": [datetime.datetime.now().strftime("%d.%m.%Y")],
            "Country": [country],
            "LeagueName": [league_name],
            "Latitude": [f"{meteo_data['latitude']:.2f}"],
            "Longitude": [f"{meteo_data['longitude']:.2f}"],
            "Temperature [°C]": [meteo_data["current_weather"]["temperature_celsius"]],
            "Temperature [°F]": [
                meteo_data["current_weather"]["temperature_fahrenheit"]
            ],
        }
        df_header = pd.DataFrame(header_info)
        if not league_table_data:
            df_table = pd.DataFrame(columns=["Club", "Games", "Points"])
        else:
            df_table = pd.DataFrame(league_table_data)
            df_table = df_table.rename(columns={"Team": "Club", "Matches": "Games"})

        df_table.index = df_table.index + 1
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df_header.to_excel(writer, sheet_name="LeagueData", startrow=0, index=False)
            df_table.to_excel(
                writer,
                sheet_name="LeagueData",
                startrow=2,
                index=True,
                index_label=None,
            )
        return file_path
    except Exception as e:
        logging.error(f"Failed to save Excel file '{file_path}': {e}")
        return None