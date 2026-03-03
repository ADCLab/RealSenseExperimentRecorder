#!/bin/bash

# Check if the path to experimentSettings.env is provided as an argument
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path_to_experimentSettings.env>"
    exit 1
fi

ENV_FILE="$1"

# Load environment variables from the specified .env file
if [[ -f "$ENV_FILE" ]]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "Environment file '$ENV_FILE' not found!"
    exit 1
fi

# Ensure required environment variables are set
if [[ -z "$BASE_FOLDER" || -z "$EXPERIMENT_NAME" || -z "$EXPERIMENT_TAG" || -z "$IMAGE_ASSET" || -z "$DIST_FOLDER" ]]; then
    echo "One or more required environment variables are missing in $ENV_FILE."
    exit 1
fi

# Create a dynamically named distribution folder within BASE_FOLDER
DIST_EXPERIMENT_FOLDER="${BASE_FOLDER}/${DIST_FOLDER}_${EXPERIMENT_NAME}_${EXPERIMENT_TAG}"
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
    src/main_bt_button.py \
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

    # Create a desktop shortcut for the executable
    DESKTOP_SHORTCUT="$HOME/Desktop/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}.desktop"
    echo "[Desktop Entry]" > "$DESKTOP_SHORTCUT"
    echo "Version=1.0" >> "$DESKTOP_SHORTCUT"
    echo "Type=Application" >> "$DESKTOP_SHORTCUT"
    echo "Name=${EXPERIMENT_NAME}_${EXPERIMENT_TAG}" >> "$DESKTOP_SHORTCUT"
    echo "Exec=${DIST_EXPERIMENT_FOLDER}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}" >> "$DESKTOP_SHORTCUT"
    echo "Icon=${IMAGE_ASSET}" >> "$DESKTOP_SHORTCUT"
    echo "Terminal=true" >> "$DESKTOP_SHORTCUT" # Set Terminal to true
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
