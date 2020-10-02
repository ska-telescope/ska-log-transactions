#!/usr/bin/env bash

# Based on:  https://gitlab.com/ska-telescope/lmc-base-classes/blob/master/scripts/validate-metadata.sh

# PACKAGE METADATA
# ----------------
if [[ $(python3 setup.py --name) == "UNKNOWN" ]] ; then
    echo "[error] metadata: name missing"
    exit 2
fi

if [[ $(python3 setup.py --version) == "0.0.0" ]] ; then
    echo "[error] metadata: version missing"
    exit 2
fi

if [[ $(python3 setup.py --url) == "UNKNOWN" ]] ; then
    echo "[error] metadata: url missing"
    exit 2
fi

if [[ $(python3 setup.py --license) == "UNKNOWN" ]] ; then
    echo "[error] metadata: license missing"
    exit 2
fi

if [[ $(python3 setup.py --description) == "UNKNOWN" ]] ; then
    echo "[error] metadata: description missing"
    exit 2
fi

if ! [[ $(python3 setup.py --classifiers) ]] ; then
    echo "[error] metadata: classifiers missing"
    exit 2
fi

echo "[info] metadata: all required tags present"

# CONFIRM TAG VERSION
# -------------------
if [ -n "$CI_COMMIT_TAG" ]; then
    if ! python3 setup.py --version | grep -q -E '^([0-9]+)\.([0-9]+)\.([0-9]+)$' ; then
        echo "[error] metadata: version [$(python3 setup.py --version)] is not according to versioning standards"
        exit 2
    fi

    if [[ $(python3 setup.py --version) != $CI_COMMIT_TAG ]] ; then
       echo "[error] metadata: python package version [$(python3 setup.py --version)] differs from git tag version [$CI_COMMIT_TAG]"
       exit 2
    fi

    echo "[info] metadata: version is valid for tagged commit"
fi
