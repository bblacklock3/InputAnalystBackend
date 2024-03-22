from datetime import timedelta
import time
from pymongo import MongoClient
from datetime import datetime
import numpy as np
import line_profiler

HOSTNAME = "172.27.149.188"
# HOSTNAME = "localhost"
PORT = 27017
DATABASE = "InputAnalyst"
MOCK_DATABASE = "MockInputAnalyst"
KEYBOARD_COLLECTION = "keyboard"
MOUSE_COLLECTION = "mouse"
APPLICATION_COLLECTION = "application"
ANALYSIS_COLLECTION = "analysis"
EARLIEST_DATE = datetime(2023, 12, 30, 0, 0, 0, 0)

client = MongoClient(HOSTNAME, PORT)
db = client[DATABASE]
keyboard_coll = db[KEYBOARD_COLLECTION]
mouse_coll = db[MOUSE_COLLECTION]
app_coll = db[APPLICATION_COLLECTION]


def get_mouse(start_date, end_date):
    data = db[MOUSE_COLLECTION].find({
        "timestamp": {
            "$gte": start_date,
            "$lt": end_date
        },
        "$or": [{
            "left_click": True
        }, {
            "right_click": True
        }, {
            "middle_click": True
        }]
    })
    return list(data)


def get_keyboard(start_date, end_date):
    data = db[KEYBOARD_COLLECTION].find(
        {"timestamp": {
            "$gte": start_date,
            "$lt": end_date
        }})
    return list(data)


def arrayRange(start, stop, step):
    return [
        start + index * step
        for index in range(int((stop - start) / step) + 1)
    ]


def calculate_windows(timestamp_list, time_list, window_sizes, inactive_limit):
    sorted_time_list = np.array(timestamp_list + time_list)
    sorted_events = np.array([1] * len(timestamp_list) + [0] * len(time_list))
    sort_index = np.argsort(sorted_time_list)
    sorted_time_list = sorted_time_list[sort_index]
    sorted_events = sorted_events[sort_index]
    zero_flag_index = np.where(sorted_events == 0)[0]
    #print(zero_flag_index)
    start_time = time.time()
    output_data = []
    for w in range(len(window_sizes)):
        window_data = []
        for i in range(len(zero_flag_index)):
            _start_index = max(0, i - window_sizes[w])
            _end_index = min(len(zero_flag_index), i)
            start_event = max(0, zero_flag_index[_start_index])
            end_event = zero_flag_index[_end_index]
            count = np.sum(sorted_events[start_event:end_event])
            window_data.append(count)
        output_data.append(window_data)
    active_data = []
    for i in range(len(zero_flag_index)):
        _start_index = max(0, i - inactive_limit)
        _end_index = min(len(zero_flag_index), i)
        start_event = max(0, zero_flag_index[_start_index])
        end_event = zero_flag_index[_end_index]
        count = np.sum(sorted_events[start_event:end_event])
        active_data.append(count)
    return [output_data, active_data]


def calculate_active(mouse_active, keyboard_active):
    mouse_active = np.array(mouse_active)
    keyboard_active = np.array(keyboard_active)
    mouse_active_total = len(np.where(mouse_active > 0)[0])
    keyboard_active_total = len(np.where(keyboard_active > 0)[0])
    active_total = len(np.where((mouse_active + keyboard_active) > 0)[0])
    return [mouse_active_total, keyboard_active_total, active_total]


def calculate_stats(window_data):
    stats = []
    for window in window_data:
        window = np.array(window)
        active_index = np.where(window > 0)[0]
        active_window = window[active_index]
        max_value = np.max(active_window)
        mean_value = np.mean(active_window).round(0)
        std_value = np.std(active_window).round(0)
        sum_value = np.sum(active_window)
        active_time = len(active_window)
        percent_above_mean = len(
            np.where(active_window > mean_value)[0]) / len(active_window)
        percent_above_mean = np.round(100 * percent_above_mean, 2)
        stats.append({
            "max": max_value,
            "mean": mean_value,
            "std": std_value,
            "sum": sum_value,
            "active_time": active_time,
        })
    return stats


def test_calculate_windows():
    #start_date = datetime.combine(datetime.now().date(), datetime.min.time())
    end_date = datetime.now()
    start_date = end_date - timedelta(minutes=10000)
    time_list = arrayRange(start_date, end_date, timedelta(minutes=1))
    mouse_data = get_mouse(start_date, end_date)
    mouse_timestamp_list = [click['timestamp'] for click in mouse_data]
    keyboard_data = get_keyboard(start_date, end_date)
    keyboard_timestamp_list = [
        keypress['timestamp'] for keypress in keyboard_data
    ]
    window_list = [1, 5, 15, 60, 1440]
    inactive_limit = 10
    mouse_windows, mouse_active = calculate_windows(mouse_timestamp_list,
                                                    time_list, window_list,
                                                    inactive_limit)
    keyboard_windows, keyboard_active = calculate_windows(
        keyboard_timestamp_list, time_list, window_list, inactive_limit)
    #print(mouse_windows, mouse_active)
    #print(keyboard_windows, keyboard_active)
    #print(mouse_active, keyboard_active)
    #print(mouse_windows[1], keyboard_windows[1])
    active_totals = calculate_active(mouse_active, keyboard_active)
    print(active_totals)
    mouse_stats = calculate_stats(mouse_windows)
    keyboard_stats = calculate_stats(keyboard_windows)
    print(mouse_stats)
    print(keyboard_stats)
    #return out


def run_lp():
    lp = line_profiler.LineProfiler(test_calculate_windows, calculate_windows)
    lp.run("test_calculate_windows()")
    lp.print_stats()


if __name__ == "__main__":
    test_calculate_windows()
