import sys
import os
import shutil
import threading
from tkinter import *
import tkinter as tk
import zipfile
from configparser import ConfigParser
from datetime import datetime
import argparse
from pystray import MenuItem, Icon
from PIL import Image

global text_output
global win


def insert(data):
    print(data)
    text_output.configure(state="normal")
    text_output.insert(tk.END, data + "\n")
    text_output.configure(state="disabled")
    win.update()
    text_output.yview_moveto(1.0)


def init_settings():
    """
    Load settings from the config.ini file
    """
    config = ConfigParser()
    config.read("resources\\config.ini")

    source = config["locations"]["source"]
    source = source.split(",")
    source = list(filter(None, source))
    destination = config["locations"]["destination"]
    temp = config["locations"]["temp"]
    days_of_week = config["schedule"]["days_of_week"]
    days_of_week = days_of_week.split(" ")
    hour = config["schedule"]["time_hour"]
    half_of_day = config["schedule"]["half_of_day"]
    first_launch = config["behaviour"]["first_launch"]
    sys_tray_on_close = config["behaviour"]["sys_tray_on_close"]
    loaded_settings = {
        "source": source,
        "destination": destination,
        "temp": temp,
        "days_of_week": days_of_week,
        "first_launch": first_launch,
        "sys_tray_on_close": sys_tray_on_close,
        "hour": hour,
        "half_of_day": half_of_day,
    }
    return loaded_settings


def zipdir(paths, zip_handler):
    for path in paths:
        insert(path)
        for root, dirs, files in os.walk(path):
            for file in files:
                insert(os.path.join(root, file))
                zip_handler.write(os.path.join(root, file))


def start_backup(settings):
    zipf = zipfile.ZipFile(settings["temp"], "w", zipfile.ZIP_DEFLATED)
    zipdir(settings["source"], zipf)
    zipf.close()
    insert("Finished compressing files")
    insert("Copying to final destination")
    current_time = datetime.now()
    current_time = current_time.strftime("%Y-%m-%d")
    shutil.move(settings["temp"], settings["destination"] + "\\" + current_time + ".zip")
    insert("Backup complete!")


def wait_for_time(settings):
    while True:
        current_time = datetime.now()
        current_time = current_time.strftime("%w,%I,%p").split(",")

        for item1 in settings["days_of_week"]:
            if int(current_time[0]) == int(item1):
                if int(current_time[1]) == int(settings["hour"]):
                    if str(current_time[2]) == str((settings["half_of_day"])):
                        start_backup(settings)


def gui_config(settings):
    """
    Open GUI configuration window
    """

    def save(box1):
        parser = ConfigParser()
        parser.read("resources/config.ini")
        parser.set(
            section="locations",
            option="source",
            value=str(source_dirs.get("1.0", "end").strip("\n")),
        )
        days = ""
        parser.set(
            section="behaviour", option="sys_tray_on_close", value=str(box1.get())
        )
        for new in list(days_select.curselection()):
            days = days + str(new) + " "
        parser.set(section="schedule", option="days_of_week", value=str(days))
        parser.set(section="schedule", option="time_hour", value=hour_var.get())
        parser.set(section="schedule", option="half_of_day", value=am_pm_var.get())
        with open("resources/config.ini", "w") as f:
            parser.write(f)

    window = Toplevel()
    window.title("Configure - Backup 4 Dad")

    days_label = Label(window, text="Days to run backup on")

    days_select = Listbox(window, width=40, height=10, selectmode=MULTIPLE)
    days_select.insert(0, "Sunday")
    days_select.insert(1, "Monday")
    days_select.insert(2, "Tuesday")
    days_select.insert(3, "Wednesday")
    days_select.insert(4, "Thursday")
    days_select.insert(5, "Friday")
    days_select.insert(6, "Saturday")

    locations_label = Label(window, text="Backup Locations")

    source_dirs = Text(window)
    for day in settings["days_of_week"]:
        days_select.select_set(day)

    for i in settings["source"]:
        source_dirs.insert("1.0", i.strip(",\n") + ",\n")
    box = IntVar()
    systray_checkbox = Checkbutton(
        window,
        text="Minimize to system tray on program close",
        variable=box,
        onvalue="1",
        offvalue="0",
    )
    hour_var = StringVar()
    hour_var.set(settings["hour"])
    am_pm_var = StringVar()
    am_pm_var.set(settings["half_of_day"])
    hours = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
    hour_dropdown = OptionMenu(window, hour_var, *hours)
    am_pm_dropdown = OptionMenu(window, am_pm_var, "AM", "PM")

    if settings["sys_tray_on_close"] == "1":
        systray_checkbox.select()

    save_button = Button(window, text="Save and close", command=lambda: save(box))

    days_label.grid(row=0, column=0)
    locations_label.grid(row=0, column=1)
    days_select.grid(row=1, column=0)
    source_dirs.grid(row=1, column=1, rowspan=5)
    systray_checkbox.grid(row=2, column=0)
    hour_dropdown.grid(row=3, column=0)
    am_pm_dropdown.grid(row=4, column=0)
    save_button.grid(row=5, column=0)


def time_thread(settings):
    thread = threading.Thread(target=wait_for_time, args=(settings,), daemon=True)
    thread.start()


def main():
    settings = init_settings()
    win = Tk()
    win.title("Backup 4 Dad")
    win.iconbitmap("resources\\backup4dad.ico")

    # Create text widget and specify size.
    text_output_box = Text(win)
    text_output_box.configure(state="disabled")

    # Create label
    head_label = Label(win, text="Backup")
    head_label.config(font=("Courier", 14))

    # Create button for next text.
    run_button = Button(win, text="run", command=start_backup)

    # Create an Exit button.
    exit_button = Button(win, text="Exit", command=win.destroy)

    config_button = Button(win, text="Config", command=lambda: gui_config(settings))

    head_label.grid(row=0, column=0, columnspan=3)
    text_output_box.grid(row=1, column=0, columnspan=3)
    run_button.grid(row=2, column=0)
    exit_button.grid(row=2, column=1)
    config_button.grid(row=2, column=2)

    # Define a function for quit the window
    def quit_window(icon):
        icon.stop()
        win.destroy()

    # Define a function to show the window again
    def show_window(icon):
        icon.stop()
        win.after(0, win.deiconify())

    # Hide the window and show on the system taskbar
    def hide_window():
        win.withdraw()
        image = Image.open("resources/backup4dad.ico")
        menu = (MenuItem("Quit", quit_window), MenuItem("Show", show_window))
        icon = Icon("name", image, "Backup 4 Dad", menu)
        icon.run()

    if settings["sys_tray_on_close"] == "1":
        win.protocol("WM_DELETE_WINDOW", hide_window)
    parse = argparse.ArgumentParser()
    parse.add_argument(
        "--nogui", help="Launch without opening main GUI", action="store_true"
    )
    args = parse.parse_args()
    if args.nogui:
        hide_window()

    time_thread(settings)

    win.mainloop()


# If this program was run (instead of imported), run the program:
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()  # When Ctrl-C is pressed, end the program.
