"""Fixed-source helpers for the finite actual Leiden1 result package."""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath

SRC = Path(__file__).resolve().parent


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def load(path):
    need(path.is_file() and not path.is_symlink(), 'Required JSON absent/symlink: ' + str(path))
    return json.loads(path.read_text())


def sha(path):
    need(path.is_file() and not path.is_symlink(), 'Required file absent/symlink: ' + str(path))
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def safe_source_member(source, name):
    """Permit canonical POSIX descendant paths, never traversal or symlinks.

    The accepted initial16-file source includes one genuine workflow/... path.
    Rejecting every slash falsely rejected those immutable accepted bytes. We
    still reject all symlink components (even in-tree aliases) so a manifest
    binds one actual regular descendant and cannot escape the source root.
    """
    need(isinstance(name, str) and name and '\x00' not in name and '\\' not in name,
         'Unsafe source manifest member')
    parts = name.split('/')
    need(not Path(name).is_absolute() and not PureWindowsPath(name).is_absolute() and
         all(part not in ('', '.', '..') for part in parts),
         'Unsafe source manifest member')
    member = source
    for part in parts:
        member = member / part
        need(not member.is_symlink(), 'Symlink source manifest member/ancestor')
    # resolve(strict=True) and relative_to also reject a missing member and any
    # escaped resolution, independently of the lexical/path-component checks.
    try:
        member.resolve(strict=True).relative_to(source.resolve(strict=True))
    except (ValueError, OSError) as error:
        raise RuntimeError('Source member missing or escapes source root: ' + name) from error
    need(member.is_file(), 'Source manifest member is not a regular file')
    return member


def verify_source(source, expected=None, members=None):
    need(source.is_dir() and not source.is_symlink(), 'Source directory absent/symlink')
    manifest = load(source / 'source_manifest.json')
    observed = sha(source / 'source_manifest.json')
    need(isinstance(manifest, dict) and bool(manifest), 'Empty source manifest')
    if expected is not None:
        need(observed == expected, 'Pinned source manifest changed')
    if members is not None:
        need(manifest == members, 'Exact source member inventory changed')
    for name, digest in manifest.items():
        need(sha(safe_source_member(source, name)) == digest, 'Frozen source member changed: ' + name)
    return observed


def frozen_guard(policy):
    source = Path(policy['root']) / 'pre_processed_RNA/analysis_source' / policy['guard_dependency_version']
    need(len(policy['guard_dependency_members']) == 11, 'All 11 strict guard dependency pins required')
    verify_source(source, policy['guard_dependency_manifest_sha256'], policy['guard_dependency_members'])
    sys.path.insert(0, str(source))
    try:
        spec = importlib.util.spec_from_file_location('strict_Leiden_package_guard', source / 'guard.py')
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
    finally:
        sys.path.pop(0)
    return guard


def identity(path, maximum=None):
    need(path.is_file() and not path.is_symlink(), 'Product absent/symlink: ' + str(path))
    value = path.stat()
    if maximum is not None:
        need(value.st_size <= maximum, 'Small-product bound exceeded: ' + str(path))
    return {'path': str(path), 'bytes': value.st_size, 'inode': value.st_ino,
            'mtime_ns': value.st_mtime_ns, 'sha256': sha(path)}


def stat_input(record):
    path = Path(record['path'])
    need(path.is_file() and not path.is_symlink(), 'Accepted input absent/symlink')
    current = path.stat()
    need((current.st_size, current.st_ino, current.st_mtime_ns) ==
         (record['bytes'], record['inode'], record['mtime_ns']), 'Accepted input identity changed: ' + str(path))
