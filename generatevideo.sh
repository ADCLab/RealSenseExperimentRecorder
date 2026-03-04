#!/bin/bash

mv *.log logs/

id_pattern="[0-9a-z]{10}"

if [[ -z "${DATA_FOLDER_RAW:-}" ]]; then
    echo "DATA_FOLDER_RAW is not set; please export it or source the appropriate env file."
    exit 1
fi

if [[ -z "${DATA_FOLDER_PROCESSED:-}" ]]; then
    echo "DATA_FOLDER_PROCESSED is not set; please export it or source the appropriate env file."
    exit 1
fi

if [[ -z "${EXPERIMENT_NAME:-}" || -z "${EXPERIMENT_TAG:-}" ]]; then
    echo "EXPERIMENT_NAME and/or EXPERIMENT_TAG are not set; please export them."
    exit 1
fi

if [[ -z "${BASE_FOLDER:-}" ]]; then
    echo "BASE_FOLDER is not set; please export it or source the appropriate env file."
    exit 1
fi

data_dir_in="${DATA_FOLDER_RAW}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}"
data_dir_out="${DATA_FOLDER_PROCESSED}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}"
mp4_dir="${data_dir_out}/mp4"

if [[ ! -d "$data_dir_in" ]]; then
    echo "Input data directory '${data_dir_in}' not found; ensure recordings exist at this location."
    exit 1
fi

mkdir -p "$mp4_dir"

participants_file="${BASE_FOLDER}/${EXPERIMENT_NAME}_${EXPERIMENT_TAG}/participants.txt"
if [[ ! -f "$participants_file" ]]; then
    echo "participants.txt not found at '${participants_file}'; cannot determine valid participant IDs."
    exit 1
fi

mapfile -t participant_folders < <(sed 's/\r$//' "$participants_file" | egrep -x "${id_pattern}")
total_participants=${#participant_folders[@]}

if [[ $total_participants -eq 0 ]]; then
    echo "No participant IDs matching pattern '${id_pattern}' were found in ${participants_file}."
    exit 0
fi

for idx in "${!participant_folders[@]}"; do
    folder="${participant_folders[$idx]}"
    progress_num=$((idx + 1))
    printf "[%d/%d] Processing participant %s\n" "$progress_num" "$total_participants" "$folder"

    participantId=$folder
    participant_in_dir="${data_dir_in}/${folder}"
    if [[ ! -d "$participant_in_dir" ]]; then
        echo "Skipping ${participantId}: folder not found at ${participant_in_dir}."
        continue
    fi

    bagfile="${participant_in_dir}/${participantId}.bag"
    video="${mp4_dir}/${participantId}.mp4"
    
    # Convert if no cooresponding mp4
    if [[ ! -f $video ]]; then

        echo "Converting ${bagfile}"

        TMPDIR=$(mktemp -d)

        rs-convert -c -i "$bagfile" -p $TMPDIR/
        ffmpeg -loglevel quiet -r 30 -pattern_type glob -i "${TMPDIR}/*.png" "${mp4_dir}/${participantId}.mp4"

        rm -rf $TMPDIR
      	# rm $bagfile
    fi

done
