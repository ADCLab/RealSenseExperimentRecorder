"""Main file."""
import json
import csv
import os
import pwd
import uuid
import webbrowser
from datetime import datetime
from threading import Thread
from select import select
from evdev import InputDevice, categorize, ecodes, list_devices
import time
import numpy as np
import pyrealsense2 as rs
from PIL import Image
from pandas import read_csv, DataFrame
from dotenv import load_dotenv
from utils import ExperimentState
from window import Window
from hotkeys import monitor_ctrl_hotkey
import sys
import subprocess

def get_username():
    """Get the username of the user running the script."""
    # Use SUDO_USER if running as sudo, otherwise fallback to the current user ID
    return os.environ.get("SUDO_USER", pwd.getpwuid(os.getuid()).pw_name)

def open_browser_as_user(url, username):
    """Run the browser as the original user using sudo."""
    try:
        # Forward the DISPLAY environment variable
        env = os.environ.copy()
        env["DISPLAY"] = env.get("DISPLAY", ":0")  # Default to :0 if not set

        # Run xdg-open as the original user
        subprocess.run(["sudo", "-u", username, "xdg-open", url], check=True, env=env)
    except Exception as e:
        print(f"Failed to open browser as user {username}: {e}")

def check_bluetooth_device_t01():
        # List all input devices and find the device named "T01"
    devices = [InputDevice(dev) for dev in list_devices()]
    t01_device = None

    for device in devices:
        if device.name == "T01":
            t01_device = device
            t01_present = True
            break

    if not t01_device:
        #print("No device named 'T01' found. Exiting Bluetooth monitoring.")
        t01_present = False
    
    return t01_present, t01_device


def monitor_bluetooth_device_t01(window, myExpState):
    """Continuously monitor the Bluetooth device named 'T01' and update the status in the GUI."""
    try:
        t01_device = None
        last_event_time = 0

        while True:
            # List all input devices and find the device named "T01"
            devices = [InputDevice(dev) for dev in list_devices()]
            t01_present = False

            for device in devices:
                if device.name == "T01":
                    t01_device = device
                    myExpState.t01_present = True
                    t01_present = True
                    break

            # Update the Bluetooth status in the GUI
            window.update_bluetooth_status(t01_present)

            if t01_present:
                # print(f"Monitoring Bluetooth device 'T01': {t01_device.name} ({t01_device.path})\n")

                # Map file descriptor for the "T01" device
                device_map = {t01_device.fd: t01_device}

                try:
                    # Monitor the "T01" device for events
                    while t01_present:
                        # Use `select` to wait for events from the "T01" device
                        r, w, x = select(device_map, [], [], 0.01)  # 0.1-second timeout to recheck for the device

                        if not r:
                            # No events detected, recheck the device
                            break

                        for fd in r:
                            device = device_map[fd]
                            for event in device.read():
                                # Get the time of the event (accurate to microseconds)
                                event_time = event.sec + (event.usec / 1e6)  # Combine seconds and microseconds

                                # Only process events if 0.1 seconds have passed since the last event
                                if event_time - last_event_time >= 0.25:
                                    # Handle events (e.g., stylus touch events)
                                    if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                                        if event.value == 1:  # Stylus touched
                                            print(f"Stylus touched the surface on device {device.path} at {event_time}")
                                            window.mark_date(event_time)  # Trigger mark_date
                                            last_event_time = event_time  # Update last event time

                except OSError:
                    # Handle the case where the device is disconnected
                    print("Device 'T01' disconnected.")
                    myExpState.t01_present = False
                    window.update_bluetooth_status(False)

            else:
                print("No device named 'T01' found.")

            # Wait for 0.1 seconds before rechecking for the "T01" device
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nBluetooth monitoring stopped.")
    except PermissionError:
        print("Permission denied. Try running the script as root (use sudo).")
    except Exception as e:
        print(f"An error occurred: {e}")




def main(myExpState: str):
    """Run the program."""
    # Get the current date for entry
    current_date = datetime.now()
    date_string = current_date.strftime("%m/%d/%Y")
    
    # Wait for the trial numbers to be entered in the GUI
    while myExpState.is_trials_complete is False:
        pass

    trials: list[list[list]] = []
    for times in myExpState.trial_times:
        trial = list()
        set_trial_data(trial, times, date_string)
        trials.append(trial)

    # Create rows
    row1 = []
    row2 = []
    data_rows = []
    set_rows(myExpState, row1, row2, data_rows, trials)

    # Write to the file
    with open(f"data/{myExpState.participantId}/{myExpState.participantId}.csv", "w", newline="") as file:
        writer = csv.writer(file)

        # Header
        writer.writerow(
            [
                f"Trail Label Order: {''.join(myExpState.trial_label_order)}",
            ]
        )
        writer.writerow(row1)
        writer.writerow(row2)

        # Data
        writer.writerows(data_rows)

    myExpState.is_finished_main = True


def set_trial_data(trial: list[list[str]], times: list[float], date_string: str):
    """Set trial data."""
    start_time = None
    piece_num = 1
    
    for current_time in times:
        # Convert epoch time to human-readable time
        human_readable_time = datetime.fromtimestamp(current_time).strftime("%H:%M:%S")
        
        # Insert a Piece line
        if start_time is not None:
            interval = current_time - start_time  # Time difference as a float
            trial.append(
                [
                    f"Piece {piece_num}",
                    date_string,
                    human_readable_time,   # Convert epoch time to "HH:MM:SS"
                    f"{interval:.3f}",     # Interval as a float with 3 decimal places
                ]
            )
            piece_num += 1

        # Insert the Initiation line
        else:
            trial.append(
                ["Initiation", date_string, human_readable_time, ""]
            )

        # Reset the start time for interval comparison
        start_time = current_time



def set_rows(myExpState, row1: list[str], row2: list[str], data_rows: list[list[str]], placing_trials: list[list[list[str]]]):
    """Fill out the rows."""
    for i in range(myExpState.num_trials):
        row1 += [f"Trial {i}", "", "", ""]
        row2 += ["#", "Date", "Time", "Interval"]

    # Fill out the data rows
    counter = 0
    while True:
        data_rows.append([])
        more_rows_needed = False
        # Get the data from the next row in all placing trials
        for trial in placing_trials:
            if counter < len(trial):
                data_rows[counter] += trial[counter]
                more_rows_needed = True
            else:
                data_rows[counter] += ["", "", "", ""]

        counter += 1

        # Check if no new data was input
        if more_rows_needed is False:
            del data_rows[-1]
            break


def getNextID(participantsSet):
    """Generate the next unique participant ID."""
    while (participantId := (uuid.uuid4().hex[:10])) in participantsSet:
        pass
    return participantId


# Run the program
if __name__ == "__main__":
    # Check for the presence of the Bluetooth device "T01"
    t01_present, t01_device = check_bluetooth_device_t01()
    if not t01_present:
        print("Device 'T01' not found. Exiting program.")
        sys.exit(1)

    # Dynamically load the .env file relative to the script/executable
    env_path = os.path.join(os.getcwd(), "experimentSettings.env")
    print(env_path)
    load_dotenv("experimentSettings.env")
    # Load the environment variables
    experimentName = os.getenv("EXPERIMENT_NAME").strip()
    numTrials = int(os.getenv("NUMBER_TRIALS"))
    experimentTag = os.getenv("EXPERIMENT_TAG").strip()
    cameraConfig = os.getenv("CAMERA_CONFIGURATION").strip()
    surveyURL = os.getenv("SURVEY_URL").strip()

    # Load participants files
    participants_file = f'participants_{experimentName}.csv'
    participantsSet = set()
    if os.path.exists(participants_file):
        participants = read_csv(participants_file, index_col=False)
        participantsSet = set(participants['participantID'])
    else:
        with open(participants_file, 'w') as fout:
            fout.write('participantID,tag,startEpochTime,startDateTime\n')
        participants = DataFrame(columns=['participantID', 'tag', 'startEpochTime', 'startDateTime'])

    participantId = getNextID(participantsSet)
    myExpState = ExperimentState(experimentTag, participants_file, numTrials, participantId)

    dataFolder = "data"
    dataPath = os.path.join(dataFolder, myExpState.participantId)
    os.makedirs(dataPath, exist_ok=True)

   # Camera
    try:
        # Set up pipeline
        pipeline = rs.pipeline()
        
        config = rs.config()

        pipeline_wrapper = rs.pipeline_wrapper(pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        
        device = pipeline_profile.get_device()
        adv_mode = rs.rs400_advanced_mode(device)
        with open (cameraConfig, 'r') as file:
            configStr = json.load(file)
        configStr = str(configStr).replace("'", '\"')
        adv_mode.load_json(configStr)
        
        config.enable_stream(rs.stream.color, 848, 480, rs.format.rgb8, 30)
        config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
        config.enable_record_to_file(f"data/{myExpState.participantId}/{myExpState.participantId}.bag")
        
        # Set up alignment
        align_to = rs.stream.color
        align = rs.align(align_to)
        
        def start_camera(): #added for start from window
            pipeline.start(config)
              
        myExpState.start_camera = start_camera
            
        def save_snapshot(identifier: str):
            """Save a picture from the camera."""
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            color_frame = aligned_frames.get_color_frame()

            color_image = np.asanyarray(color_frame.get_data())
            im = Image.fromarray(color_image)
            im.save(f"data/{myExpState.participantId}/{myExpState.participantId}_{identifier}.png")

        myExpState.save_snapshot = save_snapshot

    except Exception as e:
        print(e)
        print('Check 3D camera connection')
        sys.exit(1)


    # GUI
    window = Window(myExpState)
    #webbrowser.open(surveyURL, new=1)
    username = get_username()
    open_browser_as_user(surveyURL, username)
    
    # Start monitoring the Bluetooth device ("T01")
    bluetooth_thread = Thread(target=monitor_bluetooth_device_t01, args=(window,myExpState))
    bluetooth_thread.daemon = True
    bluetooth_thread.start()

    def on_ctrl_release():
        """Mark date on keyboard ctrl_l release."""
        print("Ctrl_L key released")
        window.mark_date(  datetime.now().timestamp()  )  # Trigger mark_date on Ctrl_L release

    # Hook the Ctrl key release via python-evdev
    ctrl_thread = Thread(target=monitor_ctrl_hotkey, args=(on_ctrl_release,))
    ctrl_thread.daemon = True
    ctrl_thread.start()

    # Keyboard
    #def on_release(key):
    #    """Mark date on keyboard ctrl_l release."""
    #    if key == keyboard.Key.ctrl_l:
    #        print("Ctrl_L key released")
    #        window.mark_date()  # Trigger mark_date on Ctrl_L release

    #listener = keyboard.Listener(on_release=on_release)
    #listener.daemon = True
    #listener.start()

    # Main thread
    main_thread = Thread(target=main, args=(myExpState,))
    main_thread.daemon = True
    main_thread.start()

    window.start()
