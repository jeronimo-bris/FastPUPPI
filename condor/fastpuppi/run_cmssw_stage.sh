#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 7 ]]; then
    echo "Usage: $0 CONFIG INPUT_FILE OUTPUT_FILE MAX_EVENTS CMSSW_DIR OUTPUT_DESTINATION STAGEOUT_MODE" >&2
    exit 2
fi

CONFIG=$1
INPUT_FILE=$2
OUTPUT_FILE=$3
MAX_EVENTS=$4
CMSSW_DIR=$5
OUTPUT_DESTINATION=$6
STAGEOUT_MODE=$7
JOB_WORKDIR=${_CONDOR_SCRATCH_DIR:-$(pwd)}

echo "============================================================"
echo "Host:       $(hostname)"
echo "Started:    $(date --iso-8601=seconds)"
echo "Config:     ${CONFIG}"
echo "Input:      ${INPUT_FILE}"
echo "Output:     ${OUTPUT_FILE}"
echo "Destination:${OUTPUT_DESTINATION}"
echo "Stage-out:  ${STAGEOUT_MODE}"
echo "Max events: ${MAX_EVENTS}"
echo "CMSSW:      ${CMSSW_DIR}"
echo "Scratch:    ${JOB_WORKDIR}"
echo "============================================================"

echo "Checking CMS environment path"
if ! timeout 60 test -r /cvmfs/cms.cern.ch/cmsset_default.sh; then
    echo "Cannot read /cvmfs/cms.cern.ch/cmsset_default.sh" >&2
    exit 10
fi
echo "Checking CMSSW source directory"
if ! timeout 60 test -d "${CMSSW_DIR}/src"; then
    echo "CMSSW source directory does not exist: ${CMSSW_DIR}/src" >&2
    exit 11
fi

echo "Loading the CMS environment"
source /cvmfs/cms.cern.ch/cmsset_default.sh
echo "CMS environment loaded"
cd "${CMSSW_DIR}/src"
echo "Building the scram runtime environment"
if ! SCRAM_RUNTIME=$(timeout 300 scram runtime -sh); then
    echo "scram runtime failed or exceeded five minutes" >&2
    exit 14
fi
eval "${SCRAM_RUNTIME}"
unset SCRAM_RUNTIME
echo "scram runtime environment loaded"
cd "${JOB_WORKDIR}"

if [[ ! -r "${CONFIG}" ]]; then
    echo "Transferred cmsRun config is missing: ${CONFIG}" >&2
    exit 12
fi

# Use XRootD for CMS and CERN EOS paths. Keep shared DICE paths on file:
# so the same wrapper remains usable on hm01.
case "${INPUT_FILE}" in
    file:*|root://*) INPUT_URI=${INPUT_FILE} ;;
    /store/*)        INPUT_URI="root://cms-xrd-global.cern.ch/${INPUT_FILE}" ;;
    /eos/cms/*)      INPUT_URI="root://eoscms.cern.ch/${INPUT_FILE}" ;;
    /eos/user/*)     INPUT_URI="root://eosuser.cern.ch/${INPUT_FILE}" ;;
    /eos/project/*)  INPUT_URI="root://eosproject.cern.ch/${INPUT_FILE}" ;;
    /eos/home-*)
        if [[ "${INPUT_FILE}" =~ ^/eos/home-([[:alnum:]])/(.+)$ ]]; then
            EOS_INPUT_PATH="/eos/user/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
            INPUT_URI="root://eosuser.cern.ch/${EOS_INPUT_PATH}"
        else
            echo "Unsupported EOS home path: ${INPUT_FILE}" >&2
            exit 19
        fi
        ;;
    /eos/*)
        echo "Unsupported EOS input path: ${INPUT_FILE}" >&2
        exit 20
        ;;
    /*) INPUT_URI="file:${INPUT_FILE}" ;;
    *)  INPUT_URI="file:$(pwd)/${INPUT_FILE}" ;;
esac
echo "Input URI:  ${INPUT_URI}"

echo "Starting cmsRun"
stdbuf -oL -eL cmsRun "${CONFIG}" \
    inputFile="${INPUT_URI}" \
    outputFile="${OUTPUT_FILE}" \
    maxEvents="${MAX_EVENTS}"

if [[ ! -s "${OUTPUT_FILE}" ]]; then
    echo "cmsRun returned successfully but did not create ${OUTPUT_FILE}" >&2
    exit 13
fi

ls -lh "${OUTPUT_FILE}"

case "${STAGEOUT_MODE}" in
    condor)
        echo "Leaving ${OUTPUT_FILE} for HTCondor output transfer"
        ;;
    eos)
        if ! command -v xrdcp >/dev/null 2>&1; then
            echo "xrdcp is unavailable in the CMSSW runtime environment" >&2
            exit 15
        fi

        EOS_PATH=${OUTPUT_DESTINATION}
        case "${EOS_PATH}" in
            /eos/user/*|/eos/home-*) EOS_HOST="eosuser.cern.ch" ;;
            /eos/project/*)          EOS_HOST="eosproject.cern.ch" ;;
            /eos/cms/*)              EOS_HOST="eoscms.cern.ch" ;;
            *)
                echo "Unsupported EOS destination: ${EOS_PATH}" >&2
                exit 16
                ;;
        esac

        # Convert the canonical /eos/home-X/user spelling back to the public
        # /eos/user/X/user namespace accepted by eosuser.cern.ch.
        if [[ "${EOS_PATH}" =~ ^/eos/home-([[:alnum:]])/(.+)$ ]]; then
            EOS_PATH="/eos/user/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        fi
        OUTPUT_URI="root://${EOS_HOST}/${EOS_PATH}"

        echo "Copying output to ${OUTPUT_URI}"
        if ! xrdcp --force --nopbar "${OUTPUT_FILE}" "${OUTPUT_URI}"; then
            echo "EOS stage-out failed for ${OUTPUT_URI}" >&2
            exit 17
        fi
        echo "EOS stage-out completed"
        ;;
    *)
        echo "Unsupported stage-out mode: ${STAGEOUT_MODE}" >&2
        exit 18
        ;;
esac

echo "Finished: $(date --iso-8601=seconds)"
