#!/bin/bash

set -e
set -u
set -x

#--- Script params -----
# These combined with "set -u" check that all params are set
ILASTIK_RAW_DATA="${ILASTIK_RAW_DATA}"

ILASTIK_PROJECT_FILE="${ILASTIK_PROJECT_FILE}"
ILASTIK_JOB_RESULT_ENDPOINT="${ILASTIK_JOB_RESULT_ENDPOINT}"
ILASTIK_BLOCK_SIZE="${ILASTIK_BLOCK_SIZE:-1024}"
#ILASTIK_EXPORT_DTYPE="${ILASTIK_EXPORT_DTYPE}"
#ILASTIK_PIPELINE_RESULT_DRANGE="${ILASTIK_PIPELINE_RESULT_DRANGE}"
#ILASTIK_EXPORT_DRANGE="${ILASTIK_EXPORT_DRANGE}"

HPC_PYTHON_EXECUTABLE="${HPC_PYTHON_EXECUTABLE}"
HPC_ILASTIK_PATH="${HPC_ILASTIK_PATH}"

S3_BUCKET_NAME="${S3_BUCKET_NAME:-n5test}"
S3_KEY="${S3_KEY}" #used by upload_dir.py to upload results over to swift/s3
S3_SECRET="${S3_SECRET}" #used by upload_dir.py to upload results over to swift/s3


USE_MPIRUN="${USE_MPIRUN:-false}"
# ----- end script params -----

if $USE_MPIRUN; then
    srun(){
        if [ "$1" == "--ntasks" ]; then
            shift;
            mpirun -N "$@"
        else
            mpirun -N 8 "$@"
        fi
    }
fi

export HDF5_USE_FILE_LOCKING=FALSE #allow multiple ilastiks to open the same .ilp file concurrently
export PYTHONPATH="${ILASTIK_PYTHONPATH:-/users/bp000188/source/ndstructs/}"

if echo "$ILASTIK_RAW_DATA" | grep -E '\.n5\.tar(\.|$)' ;  then
    EXTRACTION_DIR="$(mktemp -u | rev | cut -d/ -f1 | rev)"
    mkdir "$EXTRACTION_DIR"
    srun --ntasks 1 tar -xvf "$ILASTIK_RAW_DATA" -C "$EXTRACTION_DIR"
    ILASTIK_RAW_DATA="$(find ${EXTRACTION_DIR} | grep -E '\.n5/[^/]+/attributes.json' | head -n1 | sed 's@/attributes.json@@')"
fi

JOB_ID=${PWD##*/} #FIXME: try to get from unicore
OUT_FILE_NAME="out_${JOB_ID}.n5"
srun $HPC_PYTHON_EXECUTABLE -u $HPC_ILASTIK_PATH \
    --headless \
    --project "$ILASTIK_PROJECT_FILE" \
    --distributed --distributed_block_size="$ILASTIK_BLOCK_SIZE" \
    --output_filename_format "$OUT_FILE_NAME" \
    --raw_data "${ILASTIK_RAW_DATA}"

srun --ntasks 1 $HPC_PYTHON_EXECUTABLE -u upload_dir.py -n 10 "${OUT_FILE_NAME}" "${S3_BUCKET_NAME}"

srun --ntasks 1 "${HPC_PYTHON_EXECUTABLE}" -u update_status.py \
  "${ILASTIK_JOB_RESULT_ENDPOINT}" "${JOB_ID}" \
  --output "${OUT_FILE_NAME}" --bucket "${S3_BUCKET_NAME}"
