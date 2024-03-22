#!/usr/bin/env python3
from asyncio import futures
import cProfile
import time
from pymongo import MongoClient
from config import HOSTNAME, PORT, MOCK_DATABASE, KEYBOARD_COLLECTION, MOUSE_COLLECTION, APPLICATION_COLLECTION
from pynput import mouse, keyboard
from datetime import datetime
from models import MouseInput, KeyboardInput, ApplicationData
from pywinauto import Desktop
import win32gui
from concurrent.futures import ThreadPoolExecutor
from line_profiler import LineProfiler
import pyautogui

client = MongoClient(HOSTNAME, PORT)
db = client[MOCK_DATABASE]
keyboard_coll = db[KEYBOARD_COLLECTION]
mouse_coll = db[MOUSE_COLLECTION]
app_coll = db[APPLICATION_COLLECTION]

desktop = Desktop(backend="uia")

executor = ThreadPoolExecutor(max_workers=100)


def close_executor():
    executor.shutdown(wait=True, cancel_futures=True)


def insert_data(collection, data):
    start_time = time.time()
    #print("Inserting data")
    collection.insert_one(data.model_dump())
    #print("Data inserted in ", time.time() - start_time, " seconds")


def insert_app_data():
    global prev_apps, prev_focused
    start_time = time.time()
    #print("Starting insert app data")
    focused_app = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    pyauto_apps = pyautogui.getAllTitles()
    #print("Time to get app data: ", time.time() - start_time)
    #print(type(pyauto_apps))
    open_apps = []
    for title in pyauto_apps:
        #print("Content: ", title, " Type: ", type(title), " Length: ", len(title))
        if len(title) > 0:
            open_apps.append(title)
    #print("Open apps: ", open_apps, " Prev apps: ", prev_apps)
    print("Same apps: ", open_apps == prev_apps, " Same focused: ",
          focused_app == prev_focused)
    if open_apps == prev_apps and focused_app == prev_focused: return

    app_data = ApplicationData(timestamp=datetime.now(),
                               focused_app=focused_app,
                               visible_apps=open_apps)
    #print("Time to create app data: ", time.time() - start_time)
    app_dump = app_data.model_dump()
    app_coll.insert_one(app_dump)
    prev_apps = open_apps
    prev_focused = focused_app
    #print("Time to insert app data: ", time.time() - start_time)


def on_move(x, y):
    global prev_mouse_move_time
    if time.time() - prev_mouse_move_time < 0.1:
        return
    prev_mouse_move_time = time.time()
    mouse_input = MouseInput(timestamp=datetime.now(),
                             x=x,
                             y=y,
                             right_click=False,
                             left_click=False,
                             middle_click=False,
                             scroll=0)
    executor.submit(insert_data, mouse_coll, mouse_input)


def on_click(x, y, button, pressed):
    if not pressed: return
    right_click = button == mouse.Button.right
    left_click = button == mouse.Button.left
    middle_click = button == mouse.Button.middle
    mouse_input = MouseInput(timestamp=datetime.now(),
                             x=x,
                             y=y,
                             right_click=right_click,
                             left_click=left_click,
                             middle_click=middle_click,
                             scroll=0)
    executor.submit(insert_data, mouse_coll, mouse_input)
    executor.submit(insert_app_data)


def on_scroll(x, y, dx, dy):
    mouse_input = MouseInput(timestamp=datetime.now(),
                             x=x,
                             y=y,
                             right_click=False,
                             left_click=False,
                             middle_click=False,
                             scroll=0)
    executor.submit(insert_data, mouse_coll, mouse_input)


def on_release(key):
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


def test_events():
    for i in range(1000):
        insert_app_data()
        on_move(10, 10)
        on_click(10, 10, mouse.Button.left, True)
        on_scroll(10, 10, 0, 1)
        on_release(keyboard.Key.space)


def test_listeners():
    global prev_input_time, prev_mouse_move_time, prev_apps, prev_focused
    prev_input_time = time.time()
    prev_mouse_move_time = time.time()
    prev_apps = []
    prev_focused = ""

    listeners = create_input_listeners()
    start_time = time.time()
    while time.time() - start_time < 10:
        time.sleep(1)
    stop_input_listeners(listeners)


def run_line_profiler():
    lp = LineProfiler(create_input_listeners, stop_input_listeners, on_move,
                      on_click, on_scroll, on_release, insert_data,
                      insert_app_data)
    lp.run('test_listeners()')
    lp.print_stats()


if __name__ == "__main__":
    test_listeners()
