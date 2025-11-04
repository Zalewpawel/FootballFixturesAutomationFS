from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

try:
    BUILT_IN = BuiltIn()
except RobotNotRunningError:
    BUILT_IN = None


def log_info(message: str):
    if BUILT_IN:
        BUILT_IN.log_to_console(message)
    else:
        print(message)
