"""Main file."""
import json
import csv
import os
import pwd
import uuid
#import webbrowser
from datetime import datetime
from threading import Thread
from select import select
from evdev import InputDevice, categorize, ecodes, list_devices
import time
import numpy as np
import pyrealsense2 as rs
from PIL import Image
#from pynput import keyboard
from pandas import read_csv, DataFrame
from dotenv import load_dotenv
from utils import ExperimentState
from window import Window
import keyboard
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
    """Check if the Bluetooth device 'T01' is present."""
    devices = [InputDevice(dev) for dev in list_devices()]
    t01_device = None

    for device in devices:
        if device.name == "T01":
            t01_device = device
            return True, t01_device

    return False, None



def monitor_bluetooth_connection(window, myExpState):
    """Continuously monitor the Bluetooth device 'T01' and update the connection status."""
    try:
        while True:
            # Check if "T01" is present
            t01_present, t01_device = check_bluetooth_device_t01()
            myExpState.t01_present = t01_present

            # Update the Bluetooth status in the GUI
            window.update_bluetooth_status(t01_present)

            # If the device is not present, wait and retry
            if not t01_present:
                print("Device 'T01' not found.")
                time.sleep(1)  # Wait 1 second before rechecking
                continue

            # If the device is present, pass the device to the event handler
            print(f"Device 'T01' connected: {t01_device.path}")
            handle_bluetooth_events(t01_device, window, myExpState)

    except KeyboardInterrupt:
        print("\nBluetooth monitoring stopped.")
    except Exception as e:
        print(f"An error occurred in connection monitoring: {e}")


def handle_bluetooth_events(t01_device, window, myExpState):
    """Handle events from the Bluetooth device 'T01'."""
    try:
        # Map file descriptor for the "T01" device
        device_map = {t01_device.fd: t01_device}
        last_event_time = 0

        while myExpState.t01_present:
            # Wait for events from the "T01" device
            r, w, x = select(device_map, [], [])  # 0.1-second timeout

            if not r:
                continue  # No events detected

            for fd in r:
                device = device_map[fd]
                for event in device.read():
                    # Get the event timestamp
                    event_time = event.sec + (event.usec / 1e6)

                    # Process events only if enough time has passed since the last event
                    if event_time - last_event_time >= 0.25:
                        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                            if event.value == 1:  # Stylus touched
                                print(f"Stylus touched at {event_time}")
                                window.mark_date(event_time)  # Mark the event in the GUI
                                last_event_time = event_time

    except OSError:
        # Handle the case where the device is disconnected
        print("Device 'T01' disconnected.")
        myExpState.t01_present = False
        window.update_bluetooth_status(False)
    except Exception as e:
        print(f"An error occurred in event handling: {e}")



def main(myExpState: str):
    """Run the program."""
    # Get the current date for entry
    current_date = datetime.now()
    date_string = current_date.strftime("%m/%d/%Y")
    
    # Wait for the trial numbers to be entered in the GUI
    while myExpState.is_trials_complete is False:
        time.sleep(0.05)

    trials: list[list[list]] = []
    for times in myExpState.trial_times:
        trial = list()
        set_trial_data(trial, times)
        trials.append(trial)

    # Create rows
    row1 = []
    row2 = []
    data_rows = []
    set_rows(myExpState, row1, row2, data_rows, trials)

    # Write to the file
    output_csv = os.path.join(myExpState.data_path, f"{myExpState.participantId}.csv")
    with open(output_csv, "w", newline="") as file:
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


def set_trial_data(trial: list[list[str]], times: list[float]):
    """
    Populate trial data with initiation and piece information.

    Args:
        trial (list[list[str]]): A list to store trial data as rows.
        times (list[float]): A list of timestamps (epoch times) for the trial.
    """
    if not times:
        # Handle edge case where `times` is empty
        print("Warning: No timestamps provided for trial.")
        return

    # Initialization: Add the Initiation row
    start_time = times[0]  # The first timestamp is the initiation time
    human_readable_datetime = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
    trial.append(
        ["Initiation", human_readable_datetime, f"{start_time:.3f}", ""]  # Interval is empty for Initiation
    )

    # Process subsequent timestamps for each "Piece"
    for piece_num, current_time in enumerate(times[1:], start=1):
        # Calculate the interval since the last timestamp
        interval = current_time - start_time
        human_readable_datetime = datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")

        # Append the piece information
        trial.append(
            [
                f"Piece {piece_num}",                     # Description
                human_readable_datetime,                  # Human-readable datetime
                f"{current_time:.3f}",                    # Epoch time
                f"{interval:.3f}"                         # Interval in seconds (formatted to 3 decimal places)
            ]
        )

        # Update the start time for the next interval
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
    dataFolderRoot = os.getenv("DATA_FOLDER", "data").strip()
    timeLimitMinutes = os.getenv("TIME_LIMIT", "0").strip()
    try:
        time_limit_seconds = max(0, float(timeLimitMinutes) * 60)
    except ValueError:
        print(f"Invalid TIME_LIMIT '{timeLimitMinutes}', defaulting to 0.")
        time_limit_seconds = 0
    requireBluetooth = os.getenv("REQUIRE_BLUETOOTH", "true").strip().lower() in ("1", "true", "yes", "y")

    # Check for the presence of the Bluetooth device "T01" only if required
    if requireBluetooth:
        t01_present, t01_device = check_bluetooth_device_t01()
        if not t01_present:
            print("Device 'T01' not found. Exiting program.")
            sys.exit(1)

    experiment_data_root = os.path.join(dataFolderRoot, f"{experimentName}_{experimentTag}")
    os.makedirs(experiment_data_root, exist_ok=True)

    # Load participants files
    participants_file = os.path.join(experiment_data_root, f'participants_{experimentName}.csv')
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
    myExpState.require_bluetooth = requireBluetooth
    myExpState.time_limit_seconds = time_limit_seconds
    myExpState.data_root = experiment_data_root

    dataPath = os.path.join(experiment_data_root, myExpState.participantId)
    os.makedirs(dataPath, exist_ok=True)
    myExpState.data_path = dataPath

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
        bag_path = os.path.join(myExpState.data_path, f"{myExpState.participantId}.bag")
        config.enable_record_to_file(bag_path)
        
        # Set up alignment
        align_to = rs.stream.color
        align = rs.align(align_to)
        
        def start_camera(): #added for start from window
            pipeline.start(config)
              
        myExpState.start_camera = start_camera
        
        def stop_camera():
            """Stop the RealSense pipeline if running."""
            try:
                pipeline.stop()
            except Exception:
                pass
              
        myExpState.stop_camera = stop_camera
            
        def save_snapshot(identifier: str):
            """Save a picture from the camera."""
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            color_frame = aligned_frames.get_color_frame()

            color_image = np.asanyarray(color_frame.get_data())
            im = Image.fromarray(color_image)
            snapshot_path = os.path.join(myExpState.data_path, f"{myExpState.participantId}_{identifier}.png")
            im.save(snapshot_path)

        myExpState.save_snapshot = save_snapshot

    except Exception as e:
        print(e)
        print('Check 3D camera connection')
        sys.exit(1)


    # GUI
    window = Window(myExpState)
    #webbrowser.open(surveyURL, new=1)
    #username = get_username()
    #open_browser_as_user(surveyURL, username)

    # Start monitoring the Bluetooth connection only if required
    if requireBluetooth:
        bluetooth_thread = Thread(target=monitor_bluetooth_connection, args=(window, myExpState))
        bluetooth_thread.daemon = True
        bluetooth_thread.start()
    else:
        window.update_bluetooth_status(None)

    def on_ctrl_release():
        """Mark date on keyboard ctrl_l release."""
        print("Ctrl_L key released")
        window.mark_date(  datetime.now().timestamp()  )  # Trigger mark_date on Ctrl_L release

    # Hook the Ctrl key release
    keyboard.on_release_key('ctrl', lambda e: on_ctrl_release())

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
