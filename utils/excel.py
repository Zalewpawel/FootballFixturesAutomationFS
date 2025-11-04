import os
import pandas as pd
from openpyxl.utils import datetime

def save_league_to_excel(league_name, country, league_table_data, meteo_data, folder_path):
    safe_league_name = league_name.replace(":", "").replace("/", "").replace("\\", "")
    file_path = os.path.join(folder_path, f"{safe_league_name}.xlsx")
    try:
        header_info = {
            "Date": [datetime.datetime.now().strftime("%d.%m.%Y")],
            "Country": [country],
            "LeagueName": [league_name],
            "Latitude": [f"{meteo_data['latitude']:.2f}"],
            "Longitude": [f"{meteo_data['longitude']:.2f}"],
            "Temperature [°C]": [meteo_data['current_weather']['temperature_celsius']],
            "Temperature [°F]": [meteo_data['current_weather']['temperature_fahrenheit']]
        }
        df_header = pd.DataFrame(header_info)
        if not league_table_data:
            df_table = pd.DataFrame(columns=["Club", "Games", "Points"])
        else:
            df_table = pd.DataFrame(league_table_data)
            df_table = df_table.rename(columns={"Team": "Club", "Matches": "Games"})

        df_table.index = df_table.index + 1
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_header.to_excel(writer, sheet_name='LeagueData', startrow=0, index=False)
            df_table.to_excel(writer, sheet_name='LeagueData', startrow=2, index=True, index_label=None)
        return file_path
    except Exception as e:
        print(f"  BŁĄD: Nie można zapisać pliku Excel '{file_path}': {e}")
        return None