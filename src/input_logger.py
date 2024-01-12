#!/usr/bin/env python3
from asyncio import futures
import time
from pymongo import MongoClient
from config import HOSTNAME, PORT, DATABASE, KEYBOARD_COLLECTION, MOUSE_COLLECTION, APPLICATION_COLLECTION
from pynput import mouse, keyboard
from datetime import datetime
from models import MouseInput, KeyboardInput, ApplicationData
from pywinauto import Desktop
import win32gui
from concurrent.futures import ThreadPoolExecutor

client = MongoClient(HOSTNAME, PORT)
db = client[DATABASE]
keyboard_coll = db[KEYBOARD_COLLECTION]
mouse_coll = db[MOUSE_COLLECTION]
app_coll = db[APPLICATION_COLLECTION]

test_mouse_input = MouseInput(timestamp=datetime.now(),
                              x=0,
                              y=0,
                              right_click=False,
                              left_click=False,
                              scroll=0)
test_keyboard_input = KeyboardInput(timestamp=datetime.now(), key_value="a")
prev_input_time = time.time()
prev_mouse_move_time = time.time()

desktop = Desktop(backend="uia")

executor = ThreadPoolExecutor(max_workers=2)


def close_executor():
    executor.shutdown(wait=True, cancel_futures=True)


def insert_data(collection, data):
    collection.insert_one(data.model_dump())


def insert_app_data():
    focused_app = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    visible_apps = list(map(lambda app: app.window_text(), desktop.windows()))
    app_data = ApplicationData(timestamp=datetime.now(),
                               focused_app=focused_app,
                               visible_apps=visible_apps)
    app_coll.insert_one(app_data.model_dump())


def on_move(x, y):
    global prev_mouse_move_time
    if (time.time() - prev_mouse_move_time) < 0.1: return
    prev_mouse_move_time = time.time()
    mouse_input = MouseInput(timestamp=datetime.now(),
                             x=x,
                             y=y,
                             right_click=False,
                             left_click=False,
                             scroll=0)
    executor.submit(insert_data, mouse_coll, mouse_input)


def on_click(x, y, button, pressed):
    global prev_input_time
    if (time.time() - prev_input_time) < 0.01: return
    prev_input_time = time.time()
    right_click = button == mouse.Button.right and pressed
    left_click = button == mouse.Button.left and pressed
    mouse_input = MouseInput(timestamp=datetime.now(),
                             x=x,
                             y=y,
                             right_click=right_click,
                             left_click=left_click,
                             scroll=0)
    executor.submit(insert_data, mouse_coll, mouse_input)
    executor.submit(insert_app_data)


def on_scroll(x, y, dx, dy):
    global prev_input_time
    if (time.time() - prev_input_time) < 0.01: return
    prev_input_time = time.time()
    mouse_input = MouseInput(timestamp=datetime.now(),
                             x=x,
                             y=y,
                             right_click=False,
                             left_click=False,
                             scroll=dy)
    executor.submit(insert_data, mouse_coll, mouse_input)


def on_release(key):
    global prev_input_time
    if (time.time() - prev_input_time) < 0.01: return
    prev_input_time = time.time()
    keyboard_input = KeyboardInput(timestamp=datetime.now(),
                                   key_value=format(key))
    executor.submit(insert_data, keyboard_coll, keyboard_input)


def create_input_listeners():
    mouse_listener = mouse.Listener(on_move=on_move,
                                    on_click=on_click,
                                    on_scroll=on_scroll)
    keyboard_listener = keyboard.Listener(on_release=on_release)
    mouse_listener.start()
    keyboard_listener.start()
    return list([mouse_listener, keyboard_listener])


def stop_input_listeners(listeners):
    for listener in listeners:
        listener.stop()
