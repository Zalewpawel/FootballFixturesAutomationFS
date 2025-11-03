from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.Collections import Collections
from robot.libraries.BuiltIn import RobotNotRunningError

try:
    BUILT_IN = BuiltIn()
    COL = Collections()
except RobotNotRunningError:
    BUILT_IN = None
    COL = None

def log_info(message: str):
    if BUILT_IN:
        BUILT_IN.log_to_console(message)
    else:
        print(message)