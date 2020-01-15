#!/bin/bash

export HDF5_USE_FILE_LOCKING=FALSE
export PYTHONPATH=/users/bp000188/source/ndstructs/

set -u; set -x
    JOB_ID=${PWD##*/} #FIXME: try to get from unicore
    OUT_FILE_NAME="./out_${JOB_ID}.n5"

    tar -xvf raw_data.n5.tar --strip-components=2 #FIXME: Handle arbitrary files

    srun $HPC_PYTHON_EXECUTABLE -u $HPC_ILASTIK_PATH \
         --headless \
        --project $ILASTIK_PROJECT_FILE \
        --distributed --distributed_block_size=$ILASTIK_BLOCK_SIZE \
        --output_filename_format $OUT_FILE_NAME \
        --export-dtype $ILASTIK_EXPORT_DTYPE \
        --raw_data *.n5/data #FIXME: allow for non /n5 inputs
    ILASTIK_RESULT="$?"

    if [ $ILASTIK_RESULT = 0 ]; then
        srun --ntasks 1 $HPC_PYTHON_EXECUTABLE -u upload_dir.py -n 10  ${OUT_FILE_NAME} n5test
        UPLOAD_RESULT="$?"
    fi

    if [ $ILASTIK_RESULT = 0 -a $UPLOAD_RESULT = 0 ]; then
        RESULT_STRING="done"
    else
        RESULT_STRING="failed"
    fi

    RESULT_PAYLOAD=$(echo "{'status':'${RESULT_STRING}', 'result': '${OUT_FILE_NAME}', 'id': '${JOB_ID}'}" | tr "'" '"')
    curl -v \
        --header "Content-Type: application/json" \
        --request PUT \
        --data  "$RESULT_PAYLOAD"\
        ${ILASTIK_JOB_RESULT_ENDPOINT}/${JOB_ID}/

set +u; set +x

exit $ILASTIK_RESULT
