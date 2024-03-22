from datetime import date, datetime, timedelta
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List, Optional

from models import DailySummary, WindowData, Stats
from config import DATABASE, MOUSE_COLLECTION, KEYBOARD_COLLECTION, ANALYSIS_COLLECTION, EARLIEST_DATE, WINDOW_SIZES, INACTIVE_LIMIT
from routes.pipelines import click_match, total_click_count, individual_click_count
import numpy as np
import threading

lock = threading.Lock()


def today():
    return datetime.now().strftime("%Y-%m-%d")


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


def date_offset(start_offset, end_offset):
    if start_offset is None:
        start_date = datetime.now()
    else:
        start_date = datetime.combine(
            datetime.now().date() - timedelta(days=start_offset),
            datetime.min.time())
    if end_offset is None:
        end_date = datetime.now()
    else:
        end_date = datetime.combine(
            datetime.now().date() - timedelta(days=end_offset),
            datetime.min.time())
    return start_date, end_date


def get_date_range(start_date, end_date):
    start_list = [
        start_date + timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]
    end_list = [
        start_date + timedelta(days=i + 1)
        for i in range((end_date - start_date).days + 1)
    ]
    return start_list, end_list


router = APIRouter()


@router.get("/unprocessed/",
            response_description="Gets the data status of each date")
def get_data_status(request: Request,
                    start_offset: int | None = None,
                    end_offset: int | None = None):
    if start_offset is None and end_offset is None:
        start_offset = (datetime.now().date() - EARLIEST_DATE.date()).days
        end_offset = 0
    start_date, end_date = date_offset(start_offset, end_offset)
    start_list, end_list = get_date_range(start_date, end_date)
    data_status = []
    for i in range(len(start_list)):
        start_date = start_list[i]
        end_date = end_list[i]
        date_criteria = {"timestamp": {"$gt": start_date, "$lt": end_date}}
        date_str = start_date.date().strftime("%Y-%m-%d")
        exists = request.app.db[MOUSE_COLLECTION].find_one(date_criteria)
        status = "None"
        summary = "None"
        if exists is not None:
            processed = request.app.db[ANALYSIS_COLLECTION].find_one(
                {"date": date_str})
            if processed is not None:
                status = "Processed"
            else:
                status = "Unprocessed"
        data_status.insert(0, {
            "date": date_str,
            "status": status,
            "summary": summary
        })
    return data_status


@router.post(
    "/process/all",
    response_description="Processes the data for the given date range")
def process_data(request: Request):
    start_date, end_date = date_offset(
        (datetime.now().date() - EARLIEST_DATE.date()).days, 0)
    start_list, end_list = get_date_range(start_date, end_date)
    for i in range(len(start_list)):
        start_date = start_list[i]
        end_date = end_list[i]
        date_criteria = {"timestamp": {"$gt": start_date, "$lt": end_date}}
        date_str = start_date.date().strftime("%Y-%m-%d")
        exists = request.app.db[MOUSE_COLLECTION].find_one(date_criteria)
        if exists is not None:
            processed = request.app.db[ANALYSIS_COLLECTION].find_one(
                {"date": date_str})
            if processed is None or processed['complete'] is False:
                mouse_data = list(request.app.db[MOUSE_COLLECTION].find({
                    "$and": [
                        date_criteria, {
                            "$or": [{
                                "left_click": True
                            }, {
                                "right_click": True
                            }, {
                                "middle_click": True
                            }]
                        }
                    ]
                }).sort("timestamp", 1))
                keyboard_data = list(request.app.db[KEYBOARD_COLLECTION].find(
                    date_criteria).sort("timestamp", 1))
                end_date = end_date
                start_date = start_date
                time_list = arrayRange(start_date, end_date,
                                       timedelta(minutes=1))
                mouse_timestamp_list = [
                    click['timestamp'] for click in mouse_data
                ]
                keyboard_timestamp_list = [
                    keypress['timestamp'] for keypress in keyboard_data
                ]
                mouse_windows, mouse_active = calculate_windows(
                    mouse_timestamp_list, time_list, WINDOW_SIZES,
                    INACTIVE_LIMIT)
                keyboard_windows, keyboard_active = calculate_windows(
                    keyboard_timestamp_list, time_list, WINDOW_SIZES,
                    INACTIVE_LIMIT)
                active_totals = calculate_active(mouse_active, keyboard_active)
                mouse_stats = calculate_stats(mouse_windows)
                keyboard_stats = calculate_stats(keyboard_windows)
                complete = not (datetime.now().date() == start_date.date())
                daily_summary = DailySummary(
                    date=date_str,
                    complete=complete,
                    window_sizes=WINDOW_SIZES,
                    inactive_limit=INACTIVE_LIMIT,
                    mouse_active=active_totals[0],
                    keyboard_active=active_totals[1],
                    total_active=active_totals[2],
                    time_data=time_list,
                    window_data=[
                        WindowData(
                            size=WINDOW_SIZES[w],
                            mouse_stats=mouse_stats[w],
                            mouse_data=mouse_windows[w],
                            keyboard_stats=keyboard_stats[w],
                            keyboard_data=keyboard_windows[w],
                        ) for w in range(len(WINDOW_SIZES))
                    ],
                )
                if processed is not None:
                    request.app.db[ANALYSIS_COLLECTION].update_one(
                        {"date": date_str},
                        {"$set": daily_summary.model_dump()})
                else:
                    request.app.db[ANALYSIS_COLLECTION].insert_one(
                        daily_summary.model_dump())
        else:
            processed = request.app.db[ANALYSIS_COLLECTION].find_one(
                {"date": date_str})
            if processed is None or processed['complete'] is False:
                daily_summary = DailySummary(
                    date=date_str,
                    complete=True,
                    window_sizes=WINDOW_SIZES,
                    inactive_limit=0,
                    mouse_active=0,
                    keyboard_active=0,
                    total_active=0,
                    time_data=[],
                    window_data=[],
                )
                request.app.db[ANALYSIS_COLLECTION].insert_one(
                    daily_summary.model_dump())
    return {"status": f"Data processed from {start_date} to {end_date}"}
