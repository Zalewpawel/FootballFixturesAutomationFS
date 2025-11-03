import json
import os
from robot import run as robot_run

INPUT_PATH = "input.json"
OUTPUT_PATH = "results.json"
rc = robot_run(
    "Flashscore.robot",
    variable=[f"INPUT_PATH:{INPUT_PATH}", f"OUTPUT_PATH:{OUTPUT_PATH}"]
)
if rc != 0:
    raise SystemExit(f"Robot zwrócił kod {rc}")

with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
    results = json.load(f)
print(f"Pobrano lig: {len(results)}")
if results:
    print(results[0]["leagueName"])
    print(results[0]["table"][:2])
