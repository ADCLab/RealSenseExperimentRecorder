# RealSenseExperimentRecorder

RealSenseExperimentRecorder streamlines data collection for sorting-and-placing experiments that rely on Intel RealSense cameras, a Bluetooth stylus (T01), and a Tkinter operator console. The app guides operators through each trial, records timestamps, captures color/depth data, and packages everything into a distributable PyInstaller binary.

## Features
- **Experiment tracking GUI** – Operators start/stop trials, monitor progress, and review Bluetooth connection status from a single window.
- **RealSense capture pipeline** – Each participant run generates `.bag` recordings plus per-trial PNG snapshots inside the configured data directory.
- **Bluetooth stylus monitoring** – When `REQUIRE_BLUETOOTH` is enabled, the app continuously watches for the T01 device and flags disconnections in the UI.
- **Time limits & auto-shutdown** – A configurable `TIME_LIMIT` (minutes) automatically ends the session, saves data, and closes the camera safely.
- **Bug logging** – Runtime issues are appended to `DATA_FOLDER/<EXPERIMENT_NAME>_<TAG>/bug.log`, including long file-write waits or camera shutdown errors.

## Getting Started
1. **Clone** this repository and `cd` into `RealSenseExperimentRecorder`.
2. **Create a virtual environment** (Py3.12+) and install requirements:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   > Building `evdev` requires system headers: install `python3.X-dev` and a C compiler (`build-essential` on Debian/Ubuntu).
   > Tkinter also depends on system Tcl/Tk libs. Install them once per machine:
   > ```bash
   > sudo apt-get install python3-tk tk-dev libtk8.6 libtcl8.6
   > ```
3. **Populate settings** under `settings/env/`. Each `.env` file should define at minimum:
   ```ini
   EXPERIMENT_NAME="SortAndPlaceExpert"
   EXPERIMENT_TAG=testing
   NUMBER_TRIALS=10
   TIME_LIMIT=45
   REQUIRE_BLUETOOTH=true
   SURVEY_URL="https://example.com"
   CAMERA_CONFIGURATION="calibration_20260204_v1.json"
   BASE_FOLDER="/data/superviseit_studies/"
   DATA_FOLDER="/data/testing/superviseit_studies/"
   IMAGE_ASSET="src/TheTab_KGrgb_72ppi.png"
   ```

### Keyboard Permissions (Linux)
The Ctrl hotkey listener now uses `python-evdev`, which reads from `/dev/input/event*`. Add your user to the `input` group (once per machine) and re-login before running the recorder without `sudo`:

```bash
sudo usermod -aG input "$USER"
# log out/in or reboot so the new group membership is applied
```

## Building the Executable
Use `build.sh`, passing the desired env filename (or path). The script resolves the camera configuration automatically.
```bash
./build.sh settings/env/ExpertSortPlaceExperiment.env
```
The build process:
- Installs/updates dependencies inside `.venv`.
- Runs PyInstaller on `src/main_app.py`.
- Copies the chosen env file and camera JSON into `${BASE_FOLDER}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}` alongside the executable.

## Runtime Behavior
- Participant data, RealSense recordings, snapshots, CSVs, and `bug.log` live under `${DATA_FOLDER}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}/${PARTICIPANT_ID}`.
- Closing the GUI (manual exit, trials complete, or time-limit expiration) always waits for the writer thread to finish and stops the camera before quitting.
- Bluetooth/UI operations in background threads route updates through `window.after(...)` to keep Tkinter thread-safe.

## Troubleshooting
- **PyInstaller not found / dependency build fails** – Ensure the virtual environment is active and system packages for compiling (`python3.X-dev`, `build-essential`, `libudev-dev`) are installed.
- **T01 stylus missing** – Set `REQUIRE_BLUETOOTH=false` in the env file for runs where Bluetooth hardware is unavailable.
- **Logs** – Review `bug.log` inside the experiment’s data folder for errors such as prolonged CSV writes or RealSense shutdown issues.
