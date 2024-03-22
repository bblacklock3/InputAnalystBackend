from datetime import date, datetime, timedelta
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List, Optional

from models import ClickCount, KeypressCount, MouseInput, KeyboardInput, RecentData
from config import DATABASE, MOUSE_COLLECTION, KEYBOARD_COLLECTION

from routes.pipelines import click_match, total_click_count, individual_click_count


def today():
    return datetime.now().strftime("%Y-%m-%d")


def clamp_date(date):
    if (datetime.now() - date).days < 0:
        return datetime.now()
    else:
        return date


def process_dates(start_date, end_date):
    #print("1 Dates: ", start_date, end_date)
    if end_date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.fromisoformat(end_date)
    if start_date is None:
        start_date = datetime.combine(datetime.now().date(),
                                      datetime.min.time())
    else:
        start_date = datetime.fromisoformat(start_date)
    start_date = clamp_date(start_date)
    end_date = clamp_date(end_date)
    delta = end_date - start_date
    if delta.days < 0:
        start_date, end_date = end_date, start_date
    #print("2 Dates: ", start_date, end_date)
    return start_date, end_date


def get_date_range(start_date, end_date):
    start_date, end_date = process_dates(start_date, end_date)
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


@router.get("/mouse/today",
            response_description="Get the latest mouse data from the database",
            response_model=ClickCount)
def get_mouse_today(request: Request):
    start_date = datetime.combine(datetime.now().date(), datetime.min.time())
    end_date = datetime.now()
    pipeline = [click_match(start_date, end_date), individual_click_count]
    default = {"total": 0, "left": 0, "right": 0, "middle": 0}
    clicks = next(request.app.db[MOUSE_COLLECTION].aggregate(pipeline),
                  default)
    if clicks["total"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No mouse data found within the given dates")
    return clicks


@router.get("/mouse/{seconds}",
            response_description="Get the latest mouse data from the database",
            response_model=ClickCount)
def get_mouse_data(request: Request, seconds: int = 60):
    end_date = datetime.now()
    start_date = end_date - timedelta(seconds=seconds)
    pipeline = [click_match(start_date, end_date), individual_click_count]
    default = {"total": 0, "left": 0, "right": 0, "middle": 0}
    clicks = next(request.app.db[MOUSE_COLLECTION].aggregate(pipeline),
                  default)
    if clicks["total"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No mouse data found within the given dates")
    return clicks


@router.get("/keyboard/today",
            response_description="Get the latest mouse data from the database",
            response_model=KeypressCount)
def get_keyboard_data(request: Request):
    end_date = datetime.now()
    start_date = datetime.combine(datetime.now().date(), datetime.min.time())
    pipeline = [{
        "$match": {
            "timestamp": {
                "$gt": start_date,
                "$lt": end_date
            }
        },
    }, {
        "$group": {
            "_id": "null",
            "total": {
                "$sum": 1
            }
        }
    }]
    keypresses = next(request.app.db["keyboard"].aggregate(pipeline),
                      {"total": 0})
    if keypresses["total"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No keyboard data found within the given dates")
    return keypresses


@router.get("/keyboard/{seconds}",
            response_description="Get the latest mouse data from the database",
            response_model=KeypressCount)
def get_keyboard_data(request: Request, seconds: int = 60):
    end_date = datetime.now()
    start_date = end_date - timedelta(seconds=seconds)
    pipeline = [{
        "$match": {
            "timestamp": {
                "$gt": start_date,
                "$lt": end_date
            }
        },
    }, {
        "$group": {
            "_id": "null",
            "total": {
                "$sum": 1
            }
        }
    }]
    keypresses = next(request.app.db["keyboard"].aggregate(pipeline),
                      {"total": 0})
    if keypresses["total"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No keyboard data found within the given dates")
    return keypresses


@router.get("/recent",
            response_description=
            "Get the latest mouse and keyboard data from the database",
            response_model=RecentData)
def get_recent_data(request: Request):
    end_date = datetime.now()
    start_date_list = [
        end_date - timedelta(minutes=1), end_date - timedelta(minutes=5),
        end_date - timedelta(minutes=15), end_date - timedelta(minutes=60),
        datetime.combine(end_date.date(), datetime.min.time())
    ]
    clicks = []
    keypresses = []
    for i in range(len(start_date_list)):
        start_date = start_date_list[i]
        mouse_pipeline = [click_match(start_date, end_date), total_click_count]
        keyboard_pipeline = [{
            "$match": {
                "timestamp": {
                    "$gt": start_date,
                    "$lt": end_date
                }
            },
        }, {
            "$group": {
                "_id": "null",
                "total": {
                    "$sum": 1
                }
            }
        }]
        mouse_data = next(
            request.app.db[MOUSE_COLLECTION].aggregate(mouse_pipeline),
            {"total": 0})
        keyboard_data = next(
            request.app.db[KEYBOARD_COLLECTION].aggregate(keyboard_pipeline),
            {"total": 0})
        clicks.append(mouse_data["total"])
        keypresses.append(keyboard_data["total"])
    recent_data = RecentData(clicks=clicks, keypresses=keypresses)
    return recent_data
