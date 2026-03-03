#!/bin/bash

mv *.log logs/

id_pattern="[0-9a-z]{10}"
data_dir="dist_FOW_Sorting_Experiment_phase_1/data-bag"

for folder in $(ls $data_dir | egrep -x "${id_pattern}"); do

	participantId=$folder
	bagfile="${data_dir}/${folder}/${participantId}.bag"
	video="${data_dir}/${folder}/${participantId}.mp4"
    
    # Convert if no cooresponding mp4
    if [[ ! -f $video ]]; then

        echo "Converting ${bagfile}"

        TMPDIR=$(mktemp -d)

        rs-convert -c -i "$bagfile" -p $TMPDIR/
        ffmpeg -loglevel quiet -r 30 -pattern_type glob -i "${TMPDIR}/*.png" "${data_dir}/${folder}/${participantId}.mp4"

        rm -rf $TMPDIR
      	# rm $bagfile
    fi

done

