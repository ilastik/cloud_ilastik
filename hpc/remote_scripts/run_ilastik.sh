#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPTS_DIR"/utils.sh

#--- Script params -----
# These combined with "set -u" check that all params are set
ILASTIK_RAW_DATA="${ILASTIK_RAW_DATA}"

ILASTIK_PROJECT_FILE="${ILASTIK_PROJECT_FILE}"
ILASTIK_JOB_RESULT_ENDPOINT="${ILASTIK_JOB_RESULT_ENDPOINT}"
ILASTIK_EXPORT_SOURCE="${ILASTIK_EXPORT_SOURCE}"
ILASTIK_BLOCK_SIZE="${ILASTIK_BLOCK_SIZE:-1024}"
ILASTIK_EXTRA_OPTIONS="${ILASTIK_EXTRA_OPTIONS:-}"
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


export HDF5_USE_FILE_LOCKING=FALSE #allow multiple ilastiks to open the same .ilp file concurrently
export PYTHONPATH="${ILASTIK_PYTHONPATH:-/users/bp000188/source/ndstructs/}"

ILASTIK_RAW_DATA="$(extract_if_n5_archive "$ILASTIK_RAW_DATA")"

OUT_FILE_NAME="out_$(echo $ILASTIK_EXPORT_SOURCE | tr ' ' -)_${JOB_ID}.n5"
srun $HPC_PYTHON_EXECUTABLE -u $HPC_ILASTIK_PATH \
    --headless \
    --project "$ILASTIK_PROJECT_FILE" \
    --distributed --distributed_block_size="$ILASTIK_BLOCK_SIZE" \
    --export_source="${ILASTIK_EXPORT_SOURCE}" \
    --output_filename_format "$OUT_FILE_NAME" \
    --raw_data "${ILASTIK_RAW_DATA}" \
    ${ILASTIK_EXTRA_OPTIONS}

srun --ntasks 1 $HPC_PYTHON_EXECUTABLE -u "$SCRIPTS_DIR/upload_dir.py" -n 10 "${OUT_FILE_NAME}" "${S3_BUCKET_NAME}"

srun --ntasks 1 "${HPC_PYTHON_EXECUTABLE}" -u "$SCRIPTS_DIR/update_status.py" \
  "${ILASTIK_JOB_RESULT_ENDPOINT}" "${JOB_ID}" \
  --output "${OUT_FILE_NAME}" --bucket "${S3_BUCKET_NAME}"
