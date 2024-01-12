from datetime import date, datetime, timedelta
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List, Optional

from models import ClickCount, KeypressCount, MouseInput, KeyboardInput


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


router = APIRouter()


@router.get("/mouse-data/",
            response_description="Get the latest mouse data from the database",
            response_model=List[MouseInput])
def get_mouse_data(request: Request,
                   start_date: Optional[datetime] = Query(None, ),
                   end_date: str | None = None):
    start_date, end_date = process_dates(start_date, end_date)
    mouse_data = list(request.app.db["mouse"].find({
        "timestamp": {
            "$gt": start_date,
            "$lt": end_date
        }
    }).sort("timestamp", -1))
    if not mouse_data:
        raise HTTPException(
            status_code=404,
            detail="No mouse data found within the given dates")
    return mouse_data


@router.get("/mouse-data/clicks/",
            response_description="Get the latest mouse data from the database",
            response_model=ClickCount)
def get_mouse_data(request: Request,
                   start_date: str | None = None,
                   end_date: str | None = None):
    start_date, end_date = process_dates(start_date, end_date)
    pipeline = [{
        "$match": {
            "timestamp": {
                "$gt": start_date,
                "$lt": end_date
            },
            "$or": [{
                "left_click": True
            }, {
                "right_click": True
            }]
        },
    }, {
        "$group": {
            "_id": "null",
            "left_click": {
                "$sum": {
                    "$cond": [{
                        "$eq": ["$left_click", True]
                    }, 1, 0]
                }
            },
            "right_click": {
                "$sum": {
                    "$cond": [{
                        "$eq": ["$right_click", True]
                    }, 1, 0]
                }
            }
        }
    }]
    try:
        clicks = request.app.db["mouse"].aggregate(pipeline).next()
    except StopIteration:
        clicks = {"left_click": 0, "right_click": 0}
    return clicks


@router.get("/keyboard-data/",
            response_description="Get the latest mouse data from the database",
            response_model=List[KeyboardInput])
def get_keyboard_data(request: Request,
                      start_date: str | None = None,
                      end_date: str | None = None):
    start_date, end_date = process_dates(start_date, end_date)
    keyboard_data = list(request.app.db["keyboard"].find({
        "timestamp": {
            "$gt": start_date,
            "$lt": end_date
        }
    }).sort("timestamp", -1))
    if not keyboard_data:
        raise HTTPException(
            status_code=404,
            detail="No keyboard data found within the given dates")
    return keyboard_data


@router.get("/keyboard-data/keypresses/",
            response_description="Get the latest mouse data from the database",
            response_model=KeypressCount)
def get_keyboard_data(request: Request,
                      start_date: str | None = None,
                      end_date: str | None = None):
    start_date, end_date = process_dates(start_date, end_date)
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
    }, {
        "$project": {
            "_id": 0,
            "total": 1
        }
    }]
    try:
        keypresses = request.app.db["keyboard"].aggregate(pipeline).next()
    except StopIteration:
        keypresses = {"total": 0}
    return keypresses
