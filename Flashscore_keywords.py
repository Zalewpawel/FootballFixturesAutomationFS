import json
from robot.api.deco import keyword
from Utils.Common import log_info, BUILT_IN


class FlashscoreKeywords:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self.br = BUILT_IN.get_library_instance("Browser")

    @keyword("Load Leagues From File")
    def load_leagues_from_file(self, input_path: str):
        log_info(f"Wczytuję plik: {input_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "footballFixturesAutomationInput" in data:
                leagues = data["footballFixturesAutomationInput"]
            else:
                leagues = next(iter(data.values()))
        else:
            leagues = data
        log_info(f"Ligi do pobrania: {len(leagues)}")
        return leagues

    @keyword("Navigate To League Page")
    def navigate_to_league_page(self, league_name: str):
        log_info(f"Nawiguję do ligi: {league_name}")
        BUILT_IN.run_keyword("Click", "#search-window")
        BUILT_IN.run_keyword("Wait For Elements State", "#searchWindow", "visible")
        BUILT_IN.run_keyword("Fill Text", 'input[placeholder*="earch"]', league_name)
        BUILT_IN.run_keyword("Wait For Elements State", f'text="{league_name}"', "visible")
        BUILT_IN.run_keyword("Click", f'text="{league_name}"')

    @keyword("Read Standings Table")
    def read_standings_table(self):
        log_info("Czytam tabelę")
        headers = self.br.get_texts("css=table thead th") or []
        rows = self.br.get_elements("css=table tbody tr") or []
        data = []
        for i, _ in enumerate(rows):
            cells = self.br.get_texts(f"css=table tbody tr >> nth={i} td") or []
            if len(headers) < len(cells):
                headers = headers + [f"Col{j+1}" for j in range(len(headers), len(cells))]
            row = {
                headers[j] if j < len(headers) else f"Col{j+1}": cells[j]
                for j in range(len(cells))
            }
            data.append(row)
        return data

    @keyword("Collect Standings For Leagues")
    def collect_standings_for_leagues(self, leagues_input):
        log_info("Start zbierania tabel")
        if not isinstance(leagues_input, list):
            raise ValueError("collect_standings_for_leagues oczekuje listy lig.")
        results = []
        for item in leagues_input:
            country = (item or {}).get("country", "")
            league = (item or {}).get("leagueName", "")
            if not league:
                continue
            self.navigate_to_league_page(league)
            table = self.read_standings_table()
            results.append({
                "country": country,
                "leagueName": league,
                "table": table
            })
        log_info("Koniec zbierania tabel")
        return results

    @keyword("Save Results Json")
    def save_results_json(self, results, output_path: str):
        log_info(f"Zapisuję wynik do: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False)
