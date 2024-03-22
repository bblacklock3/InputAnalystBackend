import os
import tkinter as tk
from tkinter import ttk
import sv_ttk
from PIL import ImageTk, Image
from config import DATABASE
from db_info import connected, get_collection_names, get_db_size, get_collection_stats
from input_logger import create_input_listeners, stop_input_listeners, close_executor


def setSizeSmall():
    root.minsize(750, 50)
    root.maxsize(750, 50)


def setSizeLarge():
    root.minsize(750, 350)
    root.maxsize(750, 350)


def handleClose():
    global listeners_running
    if not listeners_running:
        close_executor()
        root.destroy()


def handleToggleListeners():
    global listeners, listeners_running
    if not listeners_running:
        listeners = create_input_listeners()
        listeners_running = True
        statusLight(listener_light, True)
    else:
        stop_input_listeners(listeners)
        listeners_running = False
        statusLight(listener_light, False)


def statusLight(widget, status):
    global root
    stgImg = green_light if status else red_light
    widget.configure(image=stgImg)
    widget.image = stgImg
    root.update_idletasks()


def toggle_db_table():
    global db_table_visible, tree
    if not db_table_visible:
        db_table_visible = True
        tree = ttk.Treeview(main, column=("c1", "c2", "c3"), show='headings')
        tree.column("#1", anchor=tk.W)
        tree.heading("#1", text="Collection Name")
        tree.column("#2", anchor=tk.W)
        tree.heading("#2", text="Document Count")
        tree.column("#3", anchor=tk.W)
        tree.heading("#3", text="Storage Size")
        tree.grid(column=0, row=1, sticky=tk.W, padx=10, pady=10)
        for coll in get_collection_names():
            stats = get_collection_stats(coll)
            tree.insert("",
                        tk.END,
                        values=(coll, stats['count'], stats['size']))
        setSizeLarge()
    else:
        db_table_visible = False
        tree.destroy()
        setSizeSmall()


listeners_running = False
db_table_visible = False

base_dir = os.path.dirname(__file__)

root = tk.Tk()
green_light = ImageTk.PhotoImage(
    Image.open(os.path.join(base_dir, "assets/green_circle.png")))
red_light = ImageTk.PhotoImage(
    Image.open(os.path.join(base_dir, "assets/red_circle.png")))

root.title("Input Analyst")
main = ttk.Frame(root, padding=10)
main.grid()
top_bar = tk.Frame(main)
top_bar.grid()
setSizeSmall()

if not connected():
    ttk.Label(top_bar, image=red_light, padding=10).grid(column=0, row=0)
    ttk.Label(top_bar, text="MongoDB is not running").grid(column=1, row=0)
    sv_ttk.set_theme("dark")
    root.mainloop()

else:
    db_message = tk.StringVar()
    db_message.set("MongoDB: {0}   Size: {1} (MB)    ".format(
        DATABASE, get_db_size()))

    mongo_light = green_light if connected() else red_light
    ttk.Label(top_bar, image=green_light, padding=10).grid(column=0, row=0)
    ttk.Label(top_bar, textvariable=db_message).grid(column=1, row=0)
    ttk.Button(top_bar,
               text="Show DB Table",
               padding=2,
               command=toggle_db_table).grid(column=2, row=0)
    ttk.Label(top_bar, text="    Input Listener Status: ").grid(column=3,
                                                                row=0)
    listener_light = ttk.Label(top_bar, image=red_light, padding=10)
    listener_light.grid(column=4, row=0)
    ttk.Button(top_bar,
               text="Play / Pause",
               padding=2,
               command=handleToggleListeners).grid(column=5, row=0)

    sv_ttk.set_theme("dark")

    root.protocol("WM_DELETE_WINDOW", handleClose)
    root.mainloop()
