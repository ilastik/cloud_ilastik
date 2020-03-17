#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPTS_DIR"/utils.sh

# ---- Script params -----
ILASTIK_EXPORT_SOURCE="${ILASTIK_EXPORT_SOURCE:-Object Predictions}"
ILASTIK_PREDICTION_MAPS="$(download_datasource "$ILASTIK_PREDICTION_MAPS")"
# ---- end script params ---

ILASTIK_EXTRA_OPTIONS="--prediction_maps ${ILASTIK_PREDICTION_MAPS}"
source "${SCRIPTS_DIR}"/run_ilastik.sh
