set -e
set -u
set -x
set -o pipefail

if [ -n "${HPC_PATH_PREFIX:-}" ]; then
    export PATH="$HPC_PATH_PREFIX:$PATH"
fi

# FIXME: this is very specific to our current setup
download_datasource(){
    BUCKET_NAME="${2:-datasources}"
    PREFIX="$(echo $1 | awk --field-separator $BUCKET_NAME/ '{print $2}' | sed 's@\.n5\.tar$@.n5@')"
    OUTPUT_DIR=$(random_filename)

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

random_filename(){
    mktemp -u | rev | cut -d/ -f1 | rev
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
