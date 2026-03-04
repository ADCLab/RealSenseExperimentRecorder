#!/bin/bash

# Check if the experimentSettings.env file name is provided as an argument
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <experimentSettings.env filename or path>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${SCRIPT_DIR}/settings/env"
REQUESTED_ENV="$1"

# Helper to copy assets into the final distribution folder
copy_asset_to_dist() {
    local source_path="$1"
    local destination_path="$2"

    if [[ ! -f "$source_path" ]]; then
        echo "Asset '$source_path' is missing; cannot copy to distribution folder."
        exit 1
    fi

    cp "$source_path" "$destination_path"
}

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

# Name for the generated executable
EXECUTABLE_NAME="puzzleExperimentRecorder"

# Generate the executable
TMPDIR_DIST=$(mktemp -d)
TMPDIR_BUILD=$(mktemp -d)

pyinstaller \
    -F \
    -w \
    --clean \
    --hidden-import=tkinter \
    --name "${EXECUTABLE_NAME}" \
    --add-data "${IMAGE_ASSET}:./src" \
    --add-data "${ENV_FILE}:./experimentSettings.env" \
    --add-data "${CAMERA_CONFIGURATION}:./${CAMERA_CONFIGURATION}" \
    src/main_app.py \
    --distpath "${TMPDIR_DIST}" \
    --workpath "${TMPDIR_BUILD}"

# Move the generated executable to the dynamically named folder
OUTPUT_EXECUTABLE="${TMPDIR_DIST}/${EXECUTABLE_NAME}"
if [[ -f "$OUTPUT_EXECUTABLE" ]]; then
    # Move the executable to the dynamically named DIST_EXPERIMENT_FOLDER
    mv "$OUTPUT_EXECUTABLE" "${DIST_EXPERIMENT_FOLDER}/"
    echo "Executable successfully moved to ${DIST_EXPERIMENT_FOLDER}/"

    # Copy the .env file to the DIST_EXPERIMENT_FOLDER manually (if not already included)
    copy_asset_to_dist "$ENV_FILE" "${DIST_EXPERIMENT_FOLDER}/experimentSettings.env"
    echo ".env file successfully copied to ${DIST_EXPERIMENT_FOLDER}/"

    # Copy the camera configuration file to the DIST_EXPERIMENT_FOLDER
    copy_asset_to_dist "$CAMERA_CONFIGURATION" "${DIST_EXPERIMENT_FOLDER}/$(basename "$CAMERA_CONFIGURATION")"
    echo "Camera configuration file successfully copied to ${DIST_EXPERIMENT_FOLDER}/"

    # Copy puzzle icon asset to the distribution folder
    PUZZLE_ICON="${SCRIPT_DIR}/src/puzzle.png"
    if [[ -f "$PUZZLE_ICON" ]]; then
        copy_asset_to_dist "$PUZZLE_ICON" "${DIST_EXPERIMENT_FOLDER}/puzzle.png"
        echo "puzzle.png copied to ${DIST_EXPERIMENT_FOLDER}/"
    else
        echo "Warning: puzzle.png not found at ${PUZZLE_ICON}."
    fi

    # Create an askpass helper script for GUI password prompts
    ASKPASS_SCRIPT="${DIST_EXPERIMENT_FOLDER}/askpass.sh"
    cat > "$ASKPASS_SCRIPT" <<'EOF'
#!/bin/bash
zenity --password --title="Authentication"
EOF
    chmod +x "$ASKPASS_SCRIPT"
    echo "askpass.sh created at ${ASKPASS_SCRIPT}"

    # Create a helper script to launch the executable with askpass configured
    RUN_SCRIPT="${DIST_EXPERIMENT_FOLDER}/run_puzzleExperimentRecorder.sh"
    cat > "$RUN_SCRIPT" <<EOF
#!/bin/bash
export SUDO_ASKPASS="${DIST_EXPERIMENT_FOLDER}/askpass.sh"
sudo -A ./${EXECUTABLE_NAME}
EOF
    chmod +x "$RUN_SCRIPT"
    echo "run_puzzleExperimentRecorder.sh created at ${RUN_SCRIPT}"

    # Resolve the executable and icon paths for the desktop shortcut
    EXECUTABLE_PATH="${DIST_EXPERIMENT_FOLDER}/${EXECUTABLE_NAME}"
    ICON_SOURCE="$IMAGE_ASSET"
    if [[ ! -f "$ICON_SOURCE" && -f "${SCRIPT_DIR}/${IMAGE_ASSET}" ]]; then
        ICON_SOURCE="${SCRIPT_DIR}/${IMAGE_ASSET}"
    fi

    # Create desktop shortcut directly on the Desktop
    DESKTOP_FOLDER="$HOME/Desktop"
    if [[ -d "$DESKTOP_FOLDER" ]]; then
        DESKTOP_SHORTCUT="${DESKTOP_FOLDER}/run_puzzleExperimentRecorder.desktop"
        cat > "$DESKTOP_SHORTCUT" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=run_puzzleExperimentRecorder
Exec=gnome-terminal -- bash -c 'cd "${DIST_EXPERIMENT_FOLDER}" && ./run_puzzleExperimentRecorder.sh'
Icon=${DIST_EXPERIMENT_FOLDER}/${ICON_SOURCE}
Terminal=true
Path=${DIST_EXPERIMENT_FOLDER}
EOF
        chmod +x "$DESKTOP_SHORTCUT"
        if command -v gio >/dev/null 2>&1; then
            gio set "$DESKTOP_SHORTCUT" metadata::trusted true || \
                echo "Warning: Failed to set metadata::trusted on ${DESKTOP_SHORTCUT}"
        else
            echo "Warning: 'gio' not found; cannot set metadata::trusted on Desktop shortcut."
        fi
        echo "Desktop shortcut created at $DESKTOP_SHORTCUT"
    else
        echo "Warning: Desktop folder '$DESKTOP_FOLDER' not found; skipping desktop shortcut creation."
    fi
else
    echo "Build failed: Executable not found in ${TMPDIR_DIST}/"
    exit 1
fi

# Clean up temporary directories
rm -rf $TMPDIR_DIST $TMPDIR_BUILD

echo "Build process completed successfully!"
