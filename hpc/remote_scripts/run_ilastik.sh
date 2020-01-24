#!/bin/bash

export HDF5_USE_FILE_LOCKING=FALSE
export PYTHONPATH=/users/bp000188/source/ndstructs/

set -e
set -u
set -x

JOB_ID=${PWD##*/} #FIXME: try to get from unicore
OUT_FILE_NAME="out_${JOB_ID}.n5"
BUCKET_NAME='n5test'

srun --ntasks 1 tar -xvf raw_data.n5.tar --strip-components=2 #FIXME: Handle arbitrary files

srun $HPC_PYTHON_EXECUTABLE -u $HPC_ILASTIK_PATH \
    --headless \
    --project "$ILASTIK_PROJECT_FILE" \
    --distributed --distributed_block_size="$ILASTIK_BLOCK_SIZE" \
    --output_filename_format "$OUT_FILE_NAME" \
    --raw_data *.n5/data #FIXME: allow for non /n5 inputs

srun --ntasks 1 $HPC_PYTHON_EXECUTABLE -u upload_dir.py -n 10 "${OUT_FILE_NAME}" "${BUCKET_NAME}"

srun --ntasks 1 "${HPC_PYTHON_EXECUTABLE}" -u update_status.py \
  "${ILASTIK_JOB_RESULT_ENDPOINT}" "${JOB_ID}" \
  --output "${OUT_FILE_NAME}" --bucket "${BUCKET_NAME}"
