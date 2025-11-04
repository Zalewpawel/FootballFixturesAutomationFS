import json
from robot.api.deco import keyword
from Utils.Common import log_info
from robot.libraries.BuiltIn import BuiltIn
from

class FlashscoreKeywords:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self.rk = BuiltIn().run_keyword

    @keyword("Load Leagues From File")
    def load_leagues_from_file(self, input_path: str):
        log_info(f"Wczytuję plik: {input_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            leagues = data.get("footballFixturesAutomationInput", next(iter(data.values())))
        else:
            leagues = data
        if not isinstance(leagues, list):
            raise ValueError("Wejście musi być listą lig albo dictem zawierającym listę.")
        log_info(f"Ligi do pobrania: {len(leagues)}")
        return leagues

    def _accept_cookies(self):
        try:
            if self.rk("Run Keyword And Return Status", "Wait For Elements State", 'text="I Accept"', "visible", "3s"):
                self.rk("Click", 'text="I Accept"')
                log_info("Kliknąłem I Accept")
        except Exception as e:
            log_info(f"I Accept: {e}")

    def _open_search_panel(self):
        if self.rk("Run Keyword And Return Status", "Wait For Elements State", "#ls-search-window", "visible", "1s"):
            return
        self.rk("Click", "#search-window")
        ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", "#ls-search-window", "visible", "5s")
        if not ok:
            ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", 'css=input.searchInput__input',
                         "visible", "5s")
        if not ok:
            raise AssertionError("Panel wyszukiwarki się nie otworzył")

    def _first_search_input_locator(self):
        candidates = [
            'css=input.searchInput__input[placeholder="Wpisz wyszukiwany tekst"]',
            'css=input.searchInput__input[placeholder="Type your search here"]',
            'css=input.searchInput__input',
            'xpath=//input[contains(@class,"searchInput__input") and (@placeholder="Wpisz wyszukiwany tekst" or @placeholder="Type your search here")]',
            'xpath=(//input[contains(@class,"searchInput__input")])[1]',
        ]
        for sel in candidates:
            try:
                cnt = self.rk("Get Element Count", sel)
                if isinstance(cnt, int) and cnt > 1 and sel.startswith("css="):
                    return sel + " >> nth=0"
            except Exception:
                pass
            if self.rk("Run Keyword And Return Status", "Wait For Elements State", sel, "visible", "3s"):
                return sel
        raise AssertionError("Nie znalazłem pola wyszukiwania (searchInput__input)")

    @keyword("Navigate To League Page")
    def navigate_to_league_page(self, league_name: str):
        log_info(f"Nawiguję do ligi: {league_name}")
        self._accept_cookies()
        self._open_search_panel()
        inp = self._first_search_input_locator()
        self.rk("Click", inp)
        self.rk("Fill Text", inp, league_name)
        self.rk("Run Keyword And Return Status", "Wait For Elements State", "css=.searchResults", "visible", "10s")
        exact = f'css=.searchResults a.searchResult >> text="{league_name}"'
        first_any = 'css=.searchResults a.searchResult >> nth=0'
        if self.rk("Run Keyword And Return Status", "Wait For Elements State", exact, "visible", "6s"):
            self.rk("Click", exact)
        elif self.rk("Run Keyword And Return Status", "Wait For Elements State", first_any, "visible", "6s"):
            self.rk("Click", first_any)
        else:
            raise AssertionError("Nie znaleziono pozycji do kliknięcia w wynikach")

    def open_standings_tab(self):
        if self.rk("Run Keyword And Return Status", "Wait For Elements State", "css=a.standings_table.selected",
                   "visible", "2s"):
            log_info("Zakładka Tabela już wybrana")
            return

        targets = [
            "css=a.standings_table",
            'css=a.tabs__tab.standings_table',
            'css=a[href*="/tabela/"]',
            'css=a[href*="/standings/"]',
            'text=Tabela',
            'text=Standings',
            'text=Table',
        ]
        for t in targets:
            if self.rk("Run Keyword And Return Status", "Wait For Elements State", t, "visible", "3s"):
                self.rk("Click", t)
                self.rk("Wait For Elements State", "css=a.standings_table.selected", "visible", "10s")
                log_info("Przełączyłem na zakładkę Tabela")
                return
        raise AssertionError("Nie znalazłem zakładki Tabela/Standings/Table")

    @keyword("Read Standings Table")
    def read_standings_table(self):
        log_info("Czytam tabelę (Wersja finalna: Mecze i Punkty)")
        try:
            self.open_standings_tab()
        except Exception as e:
            log_info(f"Nie można było kliknąć zakładki Tabela (może nie istnieje lub już jest aktywna): {e}")
        root = "css=#tournament-table .ui-table"
        ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", root, "visible", "10s")
        if not ok:
            root = "css=.ui-table"
            ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", root, "visible", "10s")
            if not ok:
                log_info("Nie znaleziono kontenera tabeli .ui-table na stronie.")
                return []
        sentinel_selector = f"{root} .ui-table__row >> .tableCellParticipant__name >> nth=0"
        try:
            self.rk("Wait For Elements State", sentinel_selector, "visible", "10s")
            log_info("Tabela (nazwy drużyn) w pełni załadowana.")
        except Exception as e:
            log_info(f"Nie znaleziono nazw drużyn. Tabela pusta? Błąd: {e}")
            return []

        def get_text(selector):
            try:
                val = (self.rk("Get Text", selector) or "").strip()
                return " ".join(val.split())
            except Exception:
                return ""
        rows_cnt = int(self.rk("Get Element Count", f"{root} .ui-table__row") or 0)
        log_info(f"Znaleziono {rows_cnt} wierszy w tabeli. Rozpoczynam pętlę.")
        data = []
        for r in range(rows_cnt):
            row_selector = f"{root} .ui-table__row >> nth={r}"
            name_sel = f"{row_selector} >> .tableCellParticipant__name"
            team = get_text(name_sel)
            if not team:
                log_info(f"Rząd {r}: Pominięty (brak nazwy drużyny).")
                continue
            cells_selector = f"{row_selector} >> .table__cell"
            matches_sel = f"{cells_selector} >> nth=2"
            points_sel = f"{cells_selector} >> nth=8"
            row_dict = {
                "Team": team,
                "Matches": get_text(matches_sel),
                "Points": get_text(points_sel)
            }
            data.append(row_dict)
            log_info(f"  Pobrano: {row_dict}")
        log_info(f"Zakończono czytanie tabeli. Pobrano {len(data)} wierszy.")
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
            results.append({"country": country, "leagueName": league, "table": table})
        log_info("Koniec zbierania tabel")
        return results

    @keyword("Save Results Json")
    def save_results_json(self, results, output_path: str):
        log_info(f"Zapisuję wynik do: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False)
