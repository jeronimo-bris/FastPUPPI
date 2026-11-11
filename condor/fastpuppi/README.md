# FastPUPPI HTCondor workflow

Keep input production and jet ntuplizing as separate jobs, joined by an
HTCondor DAG.  For every source ROOT file the DAG contains:

```text
DIGIL1 file -> inputs170X file -> jetNtuple170X file
```

This preserves the expensive intermediate output, lets DAGMan retry either
stage independently, and still submits and monitors the sample as one workflow.

## Full two-stage sample

From the TrainTagger checkout:

```bash
python3 condor/fastpuppi/submit_fastpuppi.py \
    /dice/projects/L1T/AD/mH20_bb \
    --run-dir output/condor_runs/mH20_bb \
    --submit
```

Directories are scanned non-recursively for `*.root`. Use `--recursive` when
needed. Instead of a directory, pass individual ROOT files, several files, or a
text file containing one ROOT path per line:

```bash
python3 condor/fastpuppi/submit_fastpuppi.py files.txt --submit
python3 condor/fastpuppi/submit_fastpuppi.py file0.root file1.root --submit

EOS paths are converted to XRootD URIs before they are written to the DAG. CMS
logical file names beginning with /store/ use the CMS global redirector.
CERN /eos/cms, /eos/user, and /eos/project paths use their corresponding
XRootD endpoints.

To discover all files in a DAS dataset, use --das-dataset. The option may be
repeated and may also be combined with explicit input sources:

    python3 condor/fastpuppi/submit_fastpuppi.py \
        --das-dataset "/HiddenGluGluH_mH-125_Phi-15_ctau-10_uuuu_TuneCP5_14TeV-pythia8/Phase2Spring24DIGIRECOMiniAOD-PU200_Trk1GeV_140X_mcRun4_realistic_v6-v1/GEN-SIM-DIGI-RAW-MINIAOD" \
        --stage inputs \
        --cmssw-dir "$CMSSW_BASE" \
        --output-dir /eos/user/j/jesegal/fastpuppi_outputs/HiddenGluGluH \
        --run-dir "$PWD/condor_out/condor_runs/HiddenGluGluH" \
        --submit

Dataset discovery uses dasgoclient with an unlimited query and converts returned
/store/... logical file names to CMS global XRootD URLs. Create a valid CMS
proxy before querying DAS or submitting XRootD jobs.

```

Without `--submit`, the command only creates `workflow.dag` and `manifest.tsv`.
Inspect the manifest and submit later with the printed `condor_submit_dag`
command.

By default outputs are written to:

```text
output/inputs170X/inputs170X_<source-stem>.root
output/jetNtuples170X/jetNtuple170X_<source-stem>.root
```

Logs live below the chosen run directory. The defaults allow at most 75 input
jobs and 75 ntuple jobs to run concurrently; change these with
`--max-input-jobs` and `--max-ntuple-jobs`.

## EOS output on CERN batch

When `--output-dir` begins with `/eos/`, each worker copies its completed
ROOT file directly to EOS with `xrdcp`. This avoids asking the CERN access
point to write through an EOS FUSE path. Create a valid proxy before
submitting:

```bash
voms-proxy-init --voms cms
```

For example:

```bash
python3 condor/fastpuppi/submit_fastpuppi.py \
    /eos/cms/store/group/phys_exotica/L1P2AD/CRAB_PrivateMC/SVJ_mMed_500_SLIMMED_TPs/251117_081934/ \
    --recursive \
    --stage ntuples \
    --cmssw-dir "$CMSSW_BASE" \
    --output-dir /eos/user/j/jesegal/fastpuppi_outputs/SVJ_mMed_500 \
    --run-dir "$PWD/condor_out/condor_runs/SVJ_mMed_500" \
    --max-ntuple-jobs 5000 \
    --submit
```

Keep the run directory and logs on AFS or another normal filesystem. For
non-EOS output paths, including the existing `/dice/...` paths on `hm01`,
the workflow retains the original HTCondor output-transfer behavior.

## Pilot and stage-only modes

Run a small event pilot into a separate output directory before processing all
events:

```bash
python3 condor/fastpuppi/submit_fastpuppi.py \
    /dice/projects/L1T/AD/mH20_bb/anomalyR04_bb_mH20_DIGIL1_0.root \
    --max-events 10 \
    --output-dir output/fastpuppi_pilot \
    --run-dir output/condor_runs/mH20_bb_pilot \
    --submit
```

To run the stages manually rather than as one DAG:

```bash
python3 condor/fastpuppi/submit_fastpuppi.py SOURCE_OR_LIST --stage inputs --submit
python3 condor/fastpuppi/submit_fastpuppi.py output/inputs170X --stage ntuples --submit
```

Use a different `--run-dir` for each command. Stage-2-only mode treats the
supplied files as already-produced FastPUPPI input files.

## Monitoring

```bash
condor_q -dag
condor_q -hold
```

DAGMan retries failed nodes twice by default. It writes a rescue DAG if failures
remain after the retries.

The jobs read /dice source files directly from the shared filesystem and read
EOS or DAS inputs through XRootD. They deliberately do not copy large source
ROOT files through HTCondor file transfer.

The jobs transfer and run the configs directly from:

```text
/dice/users/ek19824/CMSSW_17_0_0_pre2/src/FastPUPPI/NtupleProducer/python/
```

There are no copied configs or intermediate Python entry points in this
workflow. Both CMSSW configs use plain `VarParsing()` so their explicitly
registered `inputFile`, `outputFile`, and `maxEvents` options do not collide
with the built-ins registered by `VarParsing('analysis')`.

## Validation status

The submission helper was tested against the 100 files in `mH20_bb`; it creates
100 input jobs, 100 dependent ntuple jobs, and 100 parent/child links. DAGMan
accepted the generated DAG, and `edmConfigDump` confirmed the requested input
and output names in both resolved CMSSW configurations.

A local `cmsRun` event test on `gpu00` segfaulted during CMSSW initialization,
before a usable output file was written. That runtime behavior is outside the
DAG generation itself, so run the 10-event, one-file pilot above and inspect
both job logs before launching the full 100-file sample.
