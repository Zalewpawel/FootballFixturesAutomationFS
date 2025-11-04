Football Fixtures Automation

This project automates fetching football league standings from Flashscore and current weather data from Open-Meteo. It reads a list of leagues from input.json, scrapes the data using Robot Framework, queries the weather API, and saves the combined results into timestamped folders containing an .xlsx report and a .json weather log.


🛠️ Tech Stack

Python

Robot Framework

BrowserLibrary (Playwright)

Pandas & Openpyxl

Open-Meteo API

Ruff (Linting/Formatting)


🚀 How to Run

1. Configuration

Clone the repo: git clone https://github.com/Zalewpawel/FootballFixturesAutomationFS.git 
cd FootballFixturesAutomationFS

Edit Config/input.json to list the leagues you want to process.


2. Installation & Execution

Run the following commands in your terminal:


pip install -r requirements.txt

rfbrowser init

python Main.py

3. Output

All results will be saved in the Data/ directory. Each league will have its own timestamped folder containing the final .xlsx report and the meteo.json log.
