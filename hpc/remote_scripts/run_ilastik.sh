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

OUTPUT_BUCKET_NAME="${OUTPUT_BUCKET_NAME:-n5test}"
# ----- end script params -----


export HDF5_USE_FILE_LOCKING=FALSE #allow multiple ilastiks to open the same .ilp file concurrently
export PYTHONPATH="${ILASTIK_PYTHONPATH:-/users/bp000188/source/ndstructs/}"

ILASTIK_RAW_DATA="$(download_datasource "$ILASTIK_RAW_DATA")"

OUT_FILE_NAME="out_$(echo $ILASTIK_EXPORT_SOURCE | tr ' ' -)_${JOB_ID}.n5"
srun ilastik.py \
    --headless \
    --project "$ILASTIK_PROJECT_FILE" \
    --distributed --distributed_block_size="$ILASTIK_BLOCK_SIZE" \
    --export_source="${ILASTIK_EXPORT_SOURCE}" \
    --output_filename_format "$OUT_FILE_NAME" \
    --raw_data "${ILASTIK_RAW_DATA}" \
    ${ILASTIK_EXTRA_OPTIONS}

srun --ntasks 1 swift upload "$OUTPUT_BUCKET_NAME" "$OUT_FILE_NAME"

srun --ntasks 1 python -u "$SCRIPTS_DIR/update_status.py" \
  "${ILASTIK_JOB_RESULT_ENDPOINT}" "${JOB_ID}" \
  --output "${OUT_FILE_NAME}" --bucket "${OUTPUT_BUCKET_NAME}"
