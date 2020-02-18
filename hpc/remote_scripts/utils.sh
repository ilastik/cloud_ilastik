set -e
set -u
set -x

USE_MPIRUN="${USE_MPIRUN:-false}"

extract_if_n5_archive(){
    if echo "$1" | grep -Eq '\.n5\.tar(\.|$)' ;  then
        EXTRACTION_DIR="$(random_filename)"
        mkdir "$EXTRACTION_DIR"
        srun --ntasks 1 tar -xf "$1" -C "$EXTRACTION_DIR"
        find_n5_dataset "$EXTRACTION_DIR"
    else
        echo "$1"
    fi
}

find_n5_dataset(){
    N5_DIR_PATH="$1"
    echo "$(find "$N5_DIR_PATH" | grep -E '\.n5/[^/]+/attributes.json' | head -n1 | sed 's@/attributes.json@@')"
}

random_filename(){
    mktemp -u | rev | cut -d/ -f1 | rev
}

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
    HPC_PYTHON_EXECUTABLE=$(which python)
else
    JOB_ID=${PWD##*/} #FIXME: try to get from unicore
fi
