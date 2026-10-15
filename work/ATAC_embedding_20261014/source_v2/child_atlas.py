#!/usr/bin/env python3
"""Run the frozen builder in the same process as its SQLite storage sampler."""
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import threading

PROJECT = Path('/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_embedding_20261014_v2')
RESULTS = Path(os.environ['P5_ATAC_JOB_OUTPUT'])
SOURCE = PROJECT / 'workflow/full_study_20261008_r3/atac_postmapping.py'
BUILDER = PROJECT / 'pipeline.py'
SOURCE_SHA = '7bf312cfe6ca521a7b5d99b13d288b164d18cc1b614045766e92a5705af88d9b'
FUNCTION_SHA = '409f95d6a087007d3962d7ee8fa479a4720ae467acb54b02d2f37044a9091693'
BUILDER_SHA = json.loads((PROJECT/'source_manifest.json').read_text())[BUILDER.name]


def load_original_usage():
    source = SOURCE.read_text()
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise RuntimeError('Frozen allocated SQLite monitor source changed')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'output_usage')
    segment = ast.get_source_segment(source, node)
    if hashlib.sha256(segment.encode()).hexdigest() != FUNCTION_SHA:
        raise RuntimeError('Frozen output_usage function bytes changed')
    namespace = {'Path': Path, 'os': os}
    exec(compile(segment, str(SOURCE), 'exec'), namespace)
    return namespace['output_usage']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('builder_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if os.getpid() != os.getpgrp():
        raise RuntimeError('Child must own its process group before any scoped termination')
    if args.receipt.parent != RESULTS / 'receipts':
        raise RuntimeError('Child receipt is not this finite allocated action')
    if hashlib.sha256(BUILDER.read_bytes()).hexdigest() != BUILDER_SHA:
        raise RuntimeError('Frozen scientific builder changed')
    started = json.loads((args.receipt / 'started.json').read_text())
    roots = [Path(p) for p in started['aggregate_paths']]
    cap, inode_cap = started['aggregate_cap_bytes'], started['aggregate_file_cap']
    if cap != 500_000_000_000 or inode_cap != 40_000:
        raise RuntimeError('Finite shared matrix/QC cap changed')
    usage = load_original_usage()
    stop = threading.Event()

    def sample():
        # Roots do not overlap. Summing per-file max(logical, allocated) plus
        # directories is conservative relative to the parent regular-file scan.
        observed = [usage(p) if p.exists() else (0, 0) for p in roots]
        record = {'observed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'own_pid': os.getpid(), 'own_pgid': os.getpgrp(),
                  'capacity_bytes_including_own_unlinked_SQLite': sum(x[0] for x in observed),
                  'inodes_including_directories_and_own_unlinked_SQLite': sum(x[1] for x in observed),
                  'per_root': [{'path': str(p), 'bytes': v[0], 'inodes': v[1]} for p, v in zip(roots, observed)]}
        with (args.receipt / 'own_SQLite_storage_samples.jsonl').open('a') as handle:
            handle.write(json.dumps(record) + '\n')
        if record['capacity_bytes_including_own_unlinked_SQLite'] > cap or record['inodes_including_directories_and_own_unlinked_SQLite'] > inode_cap:
            raise RuntimeError('Aggregate matrix/QC cap including own unlinked SQLite temporaries exceeded')
        return record

    def monitor():
        try:
            while not stop.is_set():
                sample()
                stop.wait(30)
        except BaseException as error:
            failure = {'observed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                       'error': str(error), 'own_pid': os.getpid(), 'own_pgid': os.getpgrp(),
                       'source_and_incomplete_outputs_preserved': True}
            try:
                (args.receipt / 'child_storage_failure.json').write_text(json.dumps(failure, indent=2) + '\n')
            finally:
                # execute(start_new_session=True) makes this only our action and
                # its MACS children; the parent and other allocated jobs survive.
                os.killpg(os.getpid(), signal.SIGTERM)

    sample()  # Do not launch the science action if the shared allowance is full.
    thread = threading.Thread(target=monitor, name='own-SQLite-storage', daemon=True)
    thread.start()
    builder_args = args.builder_args
    if builder_args and builder_args[0] == '--':
        builder_args = builder_args[1:]
    sys.path.insert(0, str(BUILDER.parent))
    sys.argv = [str(BUILDER)] + builder_args
    try:
        runpy.run_path(str(BUILDER), run_name='__main__')
    finally:
        stop.set()
        thread.join(timeout=60)
        if thread.is_alive():
            raise RuntimeError('Own SQLite storage sampler failed to finish')
    # Only one sampler observes our FDs and appends receipts at a time.
    final = sample()
    (args.receipt / 'child_storage_complete.json').write_text(json.dumps(final, indent=2) + '\n')


if __name__ == '__main__':
    main()
