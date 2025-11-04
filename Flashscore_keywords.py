import json
from robot.api.deco import keyword
from Utils.Common import log_info
from robot.libraries.BuiltIn import BuiltIn


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
        # jeśli panel już jest, nie klikamy ponownie
        if self.rk("Run Keyword And Return Status", "Wait For Elements State", "#ls-search-window", "visible", "1s"):
            return
        self.rk("Click", "#search-window")
        ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", "#ls-search-window", "visible", "5s")
        if not ok:
            # czasem nie ma nagłówka z tym id, więc czekamy na pojawienie się samego inputa
            ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", 'css=input.searchInput__input',
                         "visible", "5s")
        if not ok:
            raise AssertionError("Panel wyszukiwarki się nie otworzył")

    def _first_search_input_locator(self):
        # warianty PL/EN, bez zawężania do #searchWindow
        candidates = [
            'css=input.searchInput__input[placeholder="Wpisz wyszukiwany tekst"]',
            'css=input.searchInput__input[placeholder="Type your search here"]',
            'css=input.searchInput__input',
            'xpath=//input[contains(@class,"searchInput__input") and (@placeholder="Wpisz wyszukiwany tekst" or @placeholder="Type your search here")]',
            'xpath=(//input[contains(@class,"searchInput__input")])[1]',
        ]
        for sel in candidates:
            # jeżeli jest wiele inputów – użyj pierwszego
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

        # kontener wyników i kliknięcie pozycji
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
        # jeśli już jesteśmy na zakładce z tabelą, nic nie rób
        if self.rk("Run Keyword And Return Status", "Wait For Elements State", "css=a.standings_table.selected",
                   "visible", "2s"):
            log_info("Zakładka Tabela już wybrana")
            return

        # kliknij zakładkę Tabela (PL), fallback na Standings/Table (EN)
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
                # poczekaj aż stanie się „selected”
                self.rk("Wait For Elements State", "css=a.standings_table.selected", "visible", "10s")
                log_info("Przełączyłem na zakładkę Tabela")
                return

        raise AssertionError("Nie znalazłem zakładki Tabela/Standings/Table")

    @keyword("Read Standings Table")
    def read_standings_table(self):
        log_info("Czytam tabelę")
        try:
            self.open_standings_tab()
        except Exception:
            pass

        root = "css=#tournament-table .ui-table"
        ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", root, "visible", "10s")
        if not ok:
            root = "css=.ui-table"
            ok = self.rk("Run Keyword And Return Status", "Wait For Elements State", root, "visible", "10s")
            if not ok:
                raise AssertionError("Nie znalazłem .ui-table")

        headers = []
        h_cnt = int(self.rk("Get Element Count", f"{root} .ui-table__header .ui-table__headerCell") or 0)
        for i in range(h_cnt):
            h_sel = f"{root} .ui-table__header .ui-table__headerCell >> nth={i}"
            title = ""
            try:
                title = self.rk("Get Attribute", h_sel, "title") or ""
            except Exception:
                pass
            try:
                txt = (self.rk("Get Property", h_sel, "innerText") or "").strip()
            except Exception:
                txt = ""
            name = (title or txt or f"Col{i + 1}").strip()
            headers.append(name)

        rows_cnt = int(self.rk("Get Element Count", f"{root} .ui-table__row") or 0)
        data = []
        for r in range(rows_cnt):
            row_base = f"{root} .ui-table__row >> nth={r} .ui-table__cell"
            cells_cnt = int(self.rk("Get Element Count", row_base) or 0)
            row_vals = []
            for c in range(cells_cnt):
                c_sel = f"{row_base} >> nth={c}"
                try:
                    val = (self.rk("Get Property", c_sel, "innerText") or "").strip()
                    # porządki: spłaszcz białe znaki
                    val = " ".join(val.split())
                except Exception:
                    val = ""
                row_vals.append(val)

            if not row_vals:
                continue

            if len(headers) < len(row_vals):
                headers = headers + [f"Col{j + 1}" for j in range(len(headers), len(row_vals))]

            row_dict = {headers[j] if j < len(headers) else f"Col{j + 1}": row_vals[j]
                        for j in range(len(row_vals))}
            data.append(row_dict)

        # ewentualnie wyrzuć kolumny całkowicie puste
        if data:
            non_empty_keys = [k for k in data[0].keys()
                              if any((row.get(k) or "").strip() for row in data)]
            data = [{k: row.get(k, "") for k in non_empty_keys} for row in data]

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
