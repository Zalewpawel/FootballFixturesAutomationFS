import json

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn

from utils.common import log_info


class FlashscoreKeywords:
    """
    Python keyword library for Robot Framework.

    This class contains all the custom keywords used to interact with
    the Flashscore website, including navigation, scraping, and data processing.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self.rk = BuiltIn().run_keyword

    @keyword("Load Leagues From File")
    def load_leagues_from_file(self, input_path: str):
        log_info(f"Loading file: {input_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            leagues = data.get(
                "footballFixturesAutomationInput", next(iter(data.values()))
            )
        else:
            leagues = data
        if not isinstance(leagues, list):
            raise ValueError(
                "Input must be a list of leagues or a dict containing a list."
            )
        log_info(f"Leagues to load: {len(leagues)}")
        return leagues

    def _accept_cookies(self):
        try:
            if self.rk(
                "Run Keyword And Return Status",
                "Wait For Elements State",
                'text="I Accept"',
                "visible",
                "3s",
            ):
                self.rk("Click", 'text="I Accept"')
                log_info("Clicked I Accept")
        except Exception as e:
            log_info(f"I Accept cookie banner error: {e}")

    def _open_search_panel(self):
        if self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            "#ls-search-window",
            "visible",
            "1s",
        ):
            return
        self.rk("Click", "#search-window")
        ok = self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            "#ls-search-window",
            "visible",
            "5s",
        )
        if not ok:
            ok = self.rk(
                "Run Keyword And Return Status",
                "Wait For Elements State",
                "css=input.searchInput__input",
                "visible",
                "5s",
            )
        if not ok:
            raise AssertionError("Search panel did not open")

    def _first_search_input_locator(self):
        candidates = [
            'css=input.searchInput__input[placeholder="Wpisz wyszukiwany tekst"]',
            'css=input.searchInput__input[placeholder="Type your search here"]',
            "css=input.searchInput__input",
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
            if self.rk(
                "Run Keyword And Return Status",
                "Wait For Elements State",
                sel,
                "visible",
                "3s",
            ):
                return sel
        raise AssertionError("Could not find search input field (searchInput__input)")

    @keyword("Navigate To League Page")
    def navigate_to_league_page(self, league_name: str):
        log_info(f"Navigating to league: {league_name}")
        self._accept_cookies()
        self._open_search_panel()
        inp = self._first_search_input_locator()
        self.rk("Click", inp)
        self.rk("Fill Text", inp, league_name)
        self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            "css=.searchResults",
            "visible",
            "10s",
        )
        exact = f'css=.searchResults a.searchResult >> text="{league_name}"'
        first_any = "css=.searchResults a.searchResult >> nth=0"
        if self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            exact,
            "visible",
            "6s",
        ):
            self.rk("Click", exact)
        elif self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            first_any,
            "visible",
            "6s",
        ):
            self.rk("Click", first_any)
        else:
            raise AssertionError("Could not find any item to click in search results")

    def open_standings_tab(self):
        if self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            "css=a.standings_table.selected",
            "visible",
            "2s",
        ):
            log_info("Standings tab is already selected")
            return

        targets = [
            "css=a.standings_table",
            "css=a.tabs__tab.standings_table",
            'css=a[href*="/tabela/"]',
            'css=a[href*="/standings/"]',
            "text=Tabela",
            "text=Standings",
            "text=Table",
        ]
        for t in targets:
            if self.rk(
                "Run Keyword And Return Status",
                "Wait For Elements State",
                t,
                "visible",
                "3s",
            ):
                self.rk("Click", t)
                self.rk(
                    "Wait For Elements State",
                    "css=a.standings_table.selected",
                    "visible",
                    "10s",
                )
                log_info("Switched to Standings tab")
                return
        raise AssertionError("Could not find Tabela/Standings/Table tab")

    @keyword("Read Standings Table")
    def read_standings_table(self):
        log_info("Reading standings table (Final version: Matches and Points)")
        try:
            self.open_standings_tab()
        except Exception as e:
            log_info(
                f"Could not click Standings tab (might not exist or already be active): {e}"
            )
        root = "css=#tournament-table .ui-table"
        ok = self.rk(
            "Run Keyword And Return Status",
            "Wait For Elements State",
            root,
            "visible",
            "10s",
        )
        if not ok:
            root = "css=.ui-table"
            ok = self.rk(
                "Run Keyword And Return Status",
                "Wait For Elements State",
                root,
                "visible",
                "10s",
            )
            if not ok:
                log_info("Could not find table container .ui-table on the page.")
                return []
        sentinel_selector = (
            f"{root} .ui-table__row >> .tableCellParticipant__name >> nth=0"
        )
        try:
            self.rk("Wait For Elements State", sentinel_selector, "visible", "10s")
            log_info("Table (team names) fully loaded.")
        except Exception as e:
            log_info(f"Could not find team names. Table empty? Error: {e}")
            return []

        def get_text(selector):
            try:
                val = (self.rk("Get Text", selector) or "").strip()
                return " ".join(val.split())
            except Exception:
                return ""

        rows_cnt = int(self.rk("Get Element Count", f"{root} .ui-table__row") or 0)
        log_info(f"Found {rows_cnt} rows in table. Starting loop.")
        data = []
        for r in range(rows_cnt):
            row_selector = f"{root} .ui-table__row >> nth={r}"
            name_sel = f"{row_selector} >> .tableCellParticipant__name"
            team = get_text(name_sel)
            if not team:
                log_info(f"Row {r}: Skipped (no team name found).")
                continue
            cells_selector = f"{row_selector} >> .table__cell"
            matches_sel = f"{cells_selector} >> nth=2"
            points_sel = f"{cells_selector} >> nth=8"
            row_dict = {
                "Team": team,
                "Matches": get_text(matches_sel),
                "Points": get_text(points_sel),
            }
            data.append(row_dict)
            log_info(f"  Scraped: {row_dict}")
        log_info(f"Finished reading table. Scraped {len(data)} rows.")
        return data

    @keyword("Collect Standings For Leagues")
    def collect_standings_for_leagues(self, leagues_input):
        log_info("Starting to collect standings.")
        if not isinstance(leagues_input, list):
            raise ValueError("collect_standings_for_leagues expects a list of leagues.")
        results = []
        for item in leagues_input:
            country = (item or {}).get("country", "")
            league = (item or {}).get("leagueName", "")
            if not league:
                continue
            self.navigate_to_league_page(league)
            table = self.read_standings_table()
            results.append({"country": country, "leagueName": league, "table": table})
        log_info("Finished collecting standings.")
        return results

    @keyword("Save Results Json")
    def save_results_json(self, results, output_path: str):
        log_info(f"Saving results to: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False)