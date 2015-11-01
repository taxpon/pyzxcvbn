#!/bin/bash

SH_SCRIPT_DIR=$(cd $(dirname $BASH_SOURCE); pwd)
LIB_DIR="${SH_SCRIPT_DIR}/pyzxcvbn"


for filename in $(ls ${LIB_DIR}/*.py)
do
    base=$(basename ${filename})
    PYSCRIPT_PATH=${LIB_DIR}/${base}
    case ${base} in
        matching.py)
            IGNORE="--ignore=E501,E241,E226"
            ;;
        scoring.py)
            IGNORE="--ignore=E501,E241,E226"
            ;;
        *)
            IGNORE="--ignore=E501"
            ;;
    esac
    pep8 ${IGNORE} ${PYSCRIPT_PATH}
done

pep8 --ignore=E501,E241,E226 tests.py

