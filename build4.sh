#!/bin/bash

# Check if the experimentSettings.env file name is provided as an argument
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <experimentSettings.env filename or path>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${SCRIPT_DIR}/settings/env"
REQUESTED_ENV="$1"

# Allow passing an absolute/relative path for compatibility; otherwise, look in settings/env
if [[ -f "$REQUESTED_ENV" ]]; then
    ENV_FILE="$REQUESTED_ENV"
else
    ENV_FILE="${ENV_DIR}/$(basename "$REQUESTED_ENV")"
fi

# Load environment variables from the specified .env file
if [[ -f "$ENV_FILE" ]]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "Environment file '$ENV_FILE' not found!"
    exit 1
fi

CAMERA_DIR="${SCRIPT_DIR}/settings/camera"

# Resolve the camera configuration path from the value provided within the env file
if [[ -z "$CAMERA_CONFIGURATION" ]]; then
    echo "CAMERA_CONFIGURATION is not defined in $ENV_FILE."
    exit 1
fi

if [[ -f "$CAMERA_CONFIGURATION" ]]; then
    RESOLVED_CAMERA="$CAMERA_CONFIGURATION"
else
    RESOLVED_CAMERA="${CAMERA_DIR}/$(basename "$CAMERA_CONFIGURATION")"
fi

if [[ ! -f "$RESOLVED_CAMERA" ]]; then
    echo "Camera configuration file '$RESOLVED_CAMERA' not found!"
    exit 1
fi

CAMERA_CONFIGURATION="$RESOLVED_CAMERA"
export CAMERA_CONFIGURATION

# Ensure required environment variables are set
if [[ -z "$BASE_FOLDER" || -z "$EXPERIMENT_NAME" || -z "$EXPERIMENT_TAG" || -z "$IMAGE_ASSET" ]]; then
    echo "One or more required environment variables are missing in $ENV_FILE."
    exit 1
fi

# Create a dynamically named distribution folder within BASE_FOLDER
DIST_EXPERIMENT_FOLDER="${BASE_FOLDER}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}"
if [[ ! -d "$DIST_EXPERIMENT_FOLDER" ]]; then
    mkdir -p "$DIST_EXPERIMENT_FOLDER"
fi

# Set up the virtual environment
if [[ ! -d ./.venv/ ]]; then
    python3 -m venv .venv
fi

# Activate the virtual environment
source ./.venv/bin/activate

# Install or update dependencies
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Generate the executable
TMPDIR_DIST=$(mktemp -d)
TMPDIR_BUILD=$(mktemp -d)

pyinstaller \
    -F \
    -w \
    --clean \
    --hidden-import=tkinter \
    --name "${EXPERIMENT_NAME}_${EXPERIMENT_TAG}" \
    --add-data "${IMAGE_ASSET}:./src" \
    --add-data "${ENV_FILE}:./experimentSettings.env" \
    --add-data "${CAMERA_CONFIGURATION}:./${CAMERA_CONFIGURATION}" \
    src/main_bt_button_v2.py \
    --distpath "${TMPDIR_DIST}" \
    --workpath "${TMPDIR_BUILD}"

# Move the generated executable to the dynamically named folder
OUTPUT_EXECUTABLE="${TMPDIR_DIST}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}"
if [[ -f "$OUTPUT_EXECUTABLE" ]]; then
    # Move the executable to the dynamically named DIST_EXPERIMENT_FOLDER
    mv "$OUTPUT_EXECUTABLE" "${DIST_EXPERIMENT_FOLDER}/"
    echo "Executable successfully moved to ${DIST_EXPERIMENT_FOLDER}/"

    # Copy the .env file to the DIST_EXPERIMENT_FOLDER manually (if not already included)
    cp "$ENV_FILE" "${DIST_EXPERIMENT_FOLDER}/experimentSettings.env"
    echo ".env file successfully copied to ${DIST_EXPERIMENT_FOLDER}/"

    # Copy the camera configuration file to the DIST_EXPERIMENT_FOLDER
    cp "$CAMERA_CONFIGURATION" "${DIST_EXPERIMENT_FOLDER}/"
    echo "Camera configuration file successfully copied to ${DIST_EXPERIMENT_FOLDER}/"

    # Create a desktop shortcut for the executable in ~/.local/share/applications
    SHORTCUT_DIR="$HOME/.local/share/applications"
    mkdir -p "$SHORTCUT_DIR"
    DESKTOP_SHORTCUT="${SHORTCUT_DIR}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}.desktop"
    echo "[Desktop Entry]" > "$DESKTOP_SHORTCUT"
    echo "Version=1.0" >> "$DESKTOP_SHORTCUT"
    echo "Type=Application" >> "$DESKTOP_SHORTCUT"
    echo "Name=${EXPERIMENT_NAME}_${EXPERIMENT_TAG}" >> "$DESKTOP_SHORTCUT"
    echo "Exec=gnome-terminal -- bash -c '/data/sync/superviseit_studies/sorting_experiments/dist_FOW_Sorting_Experiment_phase_1/run_puzzle_experiment.sh'" >> "$DESKTOP_SHORTCUT"
    echo "Icon=/data/sync/superviseit_studies/sorting_experiments/src/puzzle.png" >> "$DESKTOP_SHORTCUT"
    echo "Terminal=false" >> "$DESKTOP_SHORTCUT" # Set Terminal to true for sudo password prompt
    echo "Path=${DIST_EXPERIMENT_FOLDER}" >> "$DESKTOP_SHORTCUT" # Set working directory
    chmod +x "$DESKTOP_SHORTCUT"
    echo "Desktop shortcut created at $DESKTOP_SHORTCUT"
else
    echo "Build failed: Executable not found in ${TMPDIR_DIST}/"
    exit 1
fi

# Clean up temporary directories
rm -rf $TMPDIR_DIST $TMPDIR_BUILD

echo "Build process completed successfully!"
