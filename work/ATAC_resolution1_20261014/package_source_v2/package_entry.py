"""Finite afterany wrapper; publication requires actual complete producer proofs."""
import sys
sys.dont_write_bytecode = True
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import traceback
from common import SRC, frozen_guard, load, need, sha, verify_source


def main():
    need(len(sys.argv) == 1, 'This fixed finite package stage accepts no input arguments')
    policy = load(SRC / 'package_policy.json')
    need(SRC.name == policy['source_version'], 'Require reviewed deployed package source')
    need(policy['shared_cap_bytes'] == 500000000000 and policy['shared_cap_inodes'] == 40000 and
         policy['quota_headroom_bytes'] == 605000000000 and policy['quota_headroom_inodes'] == 53000 and
         policy['own_attempt_cap_bytes'] == 1000000000 and policy['own_attempt_cap_inodes'] == 4000 and
         policy['sample_interval_seconds'] == 30, 'Fixed shared/headroom/own monitoring bounds changed')
    root = Path(policy['root'])
    need(os.getuid() == policy['uid'] and sys.version_info[:2] == (3, 12) and not sys.flags.optimize and
         not os.environ.get('PYTHONPATH') and not os.environ.get('PYTHONHOME') and
         os.environ.get('PYTHONNOUSERSITE') == '1' and os.environ.get('PYTHONDONTWRITEBYTECODE') == '1',
         'Require preserved owner/unoptimized isolated Python3.12')
    need(Path(sys.executable) == root / 'pre_processed_RNA/analysis_environment/rna_py312/bin/python',
         'Require preserved absolute analysis Python')
    need(not os.environ.get('SLURM_ARRAY_JOB_ID'), 'This finite stage is not an array')
    source_sha = verify_source(SRC)
    guard = frozen_guard(policy)
    job = os.environ['SLURM_JOB_ID']
    need(job.isdigit(), 'Actual numeric package job identity required')
    controller = subprocess.check_output(['scontrol', 'show', 'job', '-o', job], text=True, timeout=30)
    fields = guard.fields(controller)
    need(fields.get('JobId') == job and fields.get('JobState') == 'RUNNING' and
         fields.get('UserId') == 'mujahid(10796)' and fields.get('Account') == policy['account'],
         'Actual package owner/account/state mismatch')
    need(fields.get('JobName') == 'p5-ATAC-res1-package' and fields.get('NumNodes') == '1' and
         fields.get('Requeue') == '0' and 'ArrayJobId' not in fields and
         int(fields['NumCPUs']) == 2 and int(fields['CPUs/Task']) == 2 and
         guard.memory_MiB(fields['MinMemoryNode']) == 8192 and
         0 < guard.time_seconds(fields['TimeLimit']) <= 1800,
         'Require finite single-node 2CPU/8GiB/30min non-array no-requeue allocation')
    need(fields.get('Command') == str(SRC / 'package.sbatch'), 'Actual package command differs')
    run_root = root / 'pre_processed_ATAC/analysis_runs' / policy['source_version']
    run_root.mkdir(exist_ok=True)
    need(not run_root.is_symlink(), 'Package output namespace is a symlink')
    lock_path = run_root / '.source.lock'
    need(not lock_path.is_symlink(), 'Package source execution lock is a symlink')
    lock = lock_path.open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    out = run_root / ('job-' + job)
    out.mkdir(exist_ok=False)
    (out / 'tmp').mkdir()
    try:
        def interrupted(sig, frame):
            raise RuntimeError('Parent signal ' + str(sig))
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, interrupted)
        os.environ.update(TMPDIR=str(out / 'tmp'), OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                          MKL_NUM_THREADS='2', NUMBA_NUM_THREADS='2', MPLBACKEND='Agg', TZ='UTC')
        registry = guard.OwnedFDRegistry(out, policy)
        guard.save(out / 'quota_before.json', guard.quota(policy))
        first = guard.sample(root, out, registry, policy, 'package_admission')
        with (run_root / '.source.once.intent.json').open('x') as handle:
            json.dump({'utc': guard.utc(), 'job_id': job, 'source_manifest_sha256': source_sha,
                       'upstream_actual_job_id': '7470007', 'no_automatic_retry': True}, handle, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        guard.save(out / 'started.json', {'utc': guard.utc(), 'job_id': job, 'controller': controller,
            'source_manifest_sha256': source_sha, 'upstream_job_id': '7470007',
            'strict_guard_dependency_manifest_sha256': policy['guard_dependency_manifest_sha256'],
            'shared_usage': first['shared_usage'], 'raw_matrix_or_graph_read': False,
            'new_clustering_executed': False, 'HTML_resolution1_enabled': False})
        guard.monitored([sys.executable, '-B', str(SRC / 'package_results.py'), str(out), job],
                         root, out, registry, policy, 'package.log', 'validate_actual_Leiden_results_and_package', 1500)
        stage = load(out / 'stage_result.json')
        need(stage['status'] in ['validated_initial_resolution1_package', 'review_needed_no_package_published'] and
             stage['upstream_job_id'] == '7470007' and stage['package_job_id'] == job and
             stage['normalization_ready'] is False and stage['final_QC_or_annotation_adopted'] is False,
             'Unexpected package-stage outcome or scientific scope')
        need(stage['package_published'] is (stage['status'] == 'validated_initial_resolution1_package'),
             'Package publication flag differs from actual validated outcome')
        need(not registry.live_descendants(), 'Known live/unknown child remains')
        verify_source(SRC)
        guard.save(out / 'quota_after.json', guard.quota(policy))
        guard.save(out / 'execution_complete.json', {'utc': guard.utc(), 'job_id': job, 'returncode': 0,
            'source_manifest_sha256': source_sha, 'stage_result_sha256': sha(out / 'stage_result.json'),
            'upstream_result_status': stage['status'], 'package_published': stage['package_published']})
        guard.save(out / 'storage_complete.json', guard.usage(root, out, registry, policy))
        guard.save(out / 'complete.json', {'utc': guard.utc(), 'job_id': job, 'returncode': 0,
            'source_manifest_sha256': source_sha, 'stage_result_sha256': sha(out / 'stage_result.json'),
            'package_published': stage['package_published'], 'status': stage['status'],
            'upstream_job_id': '7470007', 'normalization_ready': False,
            'final_QC_or_annotation_adopted': False, 'HTML_resolution1_enabled': False})
        final = guard.sample(root, out, registry, policy, 'after_final_package_receipts')
        guard.save(out / 'storage_complete.json', final['shared_usage'])
    except BaseException as error:
        guard.save(out / 'failed.json', {'utc': guard.utc(), 'job_id': job, 'error': repr(error),
            'traceback': traceback.format_exc(), 'package_published': False,
            'partials_preserved': True, 'normalization_ready': False, 'no_automatic_retry': True})
        raise
    finally:
        lock.close()


if __name__ == '__main__':
    main()
