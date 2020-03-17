set -e
set -u
set -x
set -o pipefail

if [ -n "${HPC_PATH_PREFIX:-}" ]; then
    export PATH="$HPC_PATH_PREFIX:$PATH"
fi

# FIXME: this is very specific to our current setup, and should probably be done by ilastik itself
download_datasource(){
    DATASET_URL="$1"

    SWIFT_AUTH_COMPONENT="$(echo $DATASET_URL | grep -Eo 'AUTH_\w+/' || echo 'NOT_FOUND')"
    if [ "$SWIFT_AUTH_COMPONENT" = NOT_FOUND ]; then
        FILENAME="$(random_filename)_$(last_path_component "$DATASET_URL")"
        wget "$DATASET_URL" -O "$FILENAME"
        echo "$FILENAME"
        return 0
    fi
    GUESSED_BUCKET_NAME="$(echo "$DATASET_URL" | awk -F $SWIFT_AUTH_COMPONENT '{print $2}' | cut -d / -f 1)"
    BUCKET_NAME="${2:-$GUESSED_BUCKET_NAME}"
    PREFIX="$(echo $1 | awk --field-separator $BUCKET_NAME/ '{print $2}' | sed 's@\.n5\.tar$@.n5@')"
    OUTPUT_DIR=$(random_filename)

    if [ -z "$PREFIX" ]; then
        echo "Trying to download the whole bucket!!" >&2
        return 1
    fi

    srun --ntasks 1 swift --quiet download -p "$PREFIX" -D $OUTPUT_DIR "$BUCKET_NAME"
    if echo "$PREFIX" | grep -Eq '\.n5$' ; then
        find_n5_dataset "$OUTPUT_DIR"
    else
        echo "$OUTPUT_DIR/$PREFIX"
    fi
}

find_n5_dataset(){
    N5_DIR_PATH="$1"
    find "$N5_DIR_PATH" | grep -E '\.n5/[^/]+/attributes.json' | head -n1 | sed 's@/attributes.json@@'
}

last_path_component(){
    echo $1 | rev | cut -d/ -f1 | rev
}

random_filename(){
    last_path_component "$(mktemp -u)"
}

USE_MPIRUN="${USE_MPIRUN:-false}"
if $USE_MPIRUN; then
    srun(){
        if [ "$1" == "--ntasks" ]; then
            shift;
            mpirun -N "$@"
        else
            mpirun -N 8 "$@"
        fi
    }
    JOB_ID="$(random_filename)"
else
    JOB_ID=${PWD##*/} #FIXME: try to get from unicore
fi
