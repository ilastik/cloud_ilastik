#!/bin/bash

export HDF5_USE_FILE_LOCKING=FALSE
export PYTHONPATH=/users/bp000188/source/ndstructs/

set -u; set -x
    JOB_ID=${PWD##*/} #FIXME: try to get from unicore
    OUT_FILE_NAME="out_${JOB_ID}.n5"
    BUCKET_NAME='n5test'

    tar -xvf raw_data.n5.tar --strip-components=2 #FIXME: Handle arbitrary files

    srun $HPC_PYTHON_EXECUTABLE -u $HPC_ILASTIK_PATH \
        --headless \
        --export_dtype "$ILASTIK_EXPORT_DTYPE" \
        --project "$ILASTIK_PROJECT_FILE" \
        --distributed --distributed_block_size="$ILASTIK_BLOCK_SIZE" \
        --pipeline_result_drange "${ILASTIK_PIPELINE_RESULT_DRANGE}" \
        --export_drange "${ILASTIK_EXPORT_DRANGE}" \
        --output_filename_format "$OUT_FILE_NAME" \
        --raw_data *.n5/data #FIXME: allow for non /n5 inputs
    ILASTIK_RESULT="$?"

    if [ $ILASTIK_RESULT = 0 ]; then
        srun --ntasks 1 $HPC_PYTHON_EXECUTABLE -u upload_dir.py -n 10 "${OUT_FILE_NAME}" "${BUCKET_NAME}"
        UPLOAD_RESULT="$?"
    fi

    if [ $ILASTIK_RESULT = 0 -a $UPLOAD_RESULT = 0 ]; then
        RESULT_STRING="done"
    else
        RESULT_STRING="failed"
    fi

    srun --ntasks 1 "${HPC_PYTHON_EXECUTABLE}" -u update_status.py \
      "${ILASTIK_JOB_RESULT_ENDPOINT}" "${JOB_ID}" "${RESULT_STRING}" \
      --output "${OUT_FILE_NAME}" --bucket "${BUCKET_NAME}"

set +u; set +x

exit $ILASTIK_RESULT
