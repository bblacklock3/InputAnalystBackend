import datetime

HOSTNAME = "172.27.149.188"
# HOSTNAME = "localhost"
PORT = 27017
DATABASE = "InputAnalyst"
MOCK_DATABASE = "MockInputAnalyst"
KEYBOARD_COLLECTION = "keyboard"
MOUSE_COLLECTION = "mouse"
APPLICATION_COLLECTION = "application"
ANALYSIS_COLLECTION = "analysis"
EARLIEST_DATE = datetime.datetime(2023, 12, 30, 0, 0, 0, 0)
WINDOW_SIZES = [5, 10, 15, 30, 60]
INACTIVE_LIMIT = 2
