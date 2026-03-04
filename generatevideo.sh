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

        # determine frame rate.  first, look for any metadata file that might
        # explicitly record it; rs-convert occasionally writes JSON or text
        # alongside the images.  if that fails we fall back to inspecting
        # timestamps embedded in the filenames, and lastly to the old default.
        fps=30

        # metadata search – any json containing a plausible key
        if meta=$(find "$TMPDIR" -maxdepth 1 -type f -name '*meta*.json' | head -n1); then
            if [[ -n "$meta" ]] && command -v jq &>/dev/null; then
                # try a few common field names; jq will silently error if not present
                for key in fps frame_rate frameRate rate; do
                    val=$(jq -r ".${key}?" "$meta" 2>/dev/null)
                    if [[ $val =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                        fps=$val
                        echo "metadata fps=$fps (from $meta, field $key)"
                        break
                    fi
                done
            fi
        fi

        # if we still haven't changed from the default, try the filename timestamps
        if [[ $fps == 30 ]]; then
            if ls "$TMPDIR"/*.png &> /dev/null; then
                mapfile -t stamps < <(ls "$TMPDIR"/*.png | xargs -n1 basename | \
                    grep -o -E '[0-9]+\.?[0-9]*' | sort -n)
                if [[ ${#stamps[@]} -gt 1 ]]; then
                    total=0
                    prev=${stamps[0]}
                    for ts in "${stamps[@]:1}"; do
                        delta=$(awk -v a="$ts" -v b="$prev" 'BEGIN{print a-b}')
                        total=$(awk -v t="$total" -v d="$delta" 'BEGIN{print t+d}')
                        prev=$ts
                    done
                    avg=$(awk -v t="$total" -v n="${#stamps[@]}" 'BEGIN{print t/(n-1)}')
                    if (( $(awk -v a="$avg" 'BEGIN{print (a>0)}') )); then
                        fps=$(awk -v a="$avg" 'BEGIN{printf "%.2f", 1/a}')
                    fi
                fi
            fi
        fi

        echo "using fps=$fps for ${participantId}"
        ffmpeg -loglevel quiet -framerate "$fps" -pattern_type glob -i "${TMPDIR}/*.png" "${mp4_dir}/${participantId}.mp4"

        rm -rf $TMPDIR
      	# rm $bagfile
    fi

done
