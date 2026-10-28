"""Validate and serve an explicit reviewed overlay over the immutable snapshot."""
from __future__ import annotations

import functools
import hashlib
import http.server
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

PREFIX = "/full_workflow_20261014/atlas_preview/"
UPDATE_ID = "rna_microglia_20261017"
REQUIRED = {PREFIX + name for name in (
    "index.html", "app.js", "rna_microglia.js", "te_group_trends.js", "rna_microglia.css",
    "paired_views.js", "paired_views.css", "microglia_marker_focus.js", "microglia_deg.js", "microglia_deg.css",
    "published_figure1c.js", "published_figure1c.css",
    "data/rna_microglia.json", "data/microglia_coordinates.json",
)}
MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_TOTAL_BYTES = 270 * 1024 * 1024
MAX_FILES = 410


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _unique(pairs):
    value = {}
    for key, item in pairs:
        _need(key not in value, "Duplicate JSON key: " + key)
        value[key] = item
    return value


def _relative(name):
    _need(type(name) is str and name != "", "A relative POSIX path is required")
    path = PurePosixPath(name)
    _need(not path.is_absolute() and path.as_posix() == name and
          all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", p) for p in path.parts),
          "Unsafe or noncanonical overlay path: " + name)
    return path


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode)


def _alias(info):
    # Windows directory junctions are reparse points, not always S_ISLNK.
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) &
        getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _read(root, name, limit):
    """Return one bounded immutable byte string; reject aliases and read races."""
    relative = _relative(name)
    ancestors = []
    path = root
    for component in relative.parts[:-1]:
        path = path / component
        info = path.lstat()
        _need(stat.S_ISDIR(info.st_mode) and not _alias(info),
              "Overlay directory symlink/non-directory rejected")
        ancestors.append((path, _identity(info)))
    path = root.joinpath(*relative.parts)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        _need(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limit and
              _identity(before) == _identity(path.lstat()),
              "Bounded regular overlay file required: " + name)
        chunks = []
        size = 0
        while True:
            block = os.read(descriptor, min(65536, limit + 1 - size))
            if not block:
                break
            size += len(block)
            _need(size <= before.st_size, "Overlay file grew during verification")
            chunks.append(block)
        _need(size == before.st_size and _identity(before) ==
              _identity(os.fstat(descriptor)) == _identity(path.lstat()),
              "Overlay file changed during verification")
        _need(all(_identity(parent.lstat()) == identity for parent, identity in ancestors),
              "Overlay ancestry changed during verification")
        return b"".join(chunks), before
    finally:
        os.close(descriptor)


def _json(root, name, limit):
    raw, _ = _read(root, name, limit)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique), raw


@dataclass(frozen=True)
class Asset:
    root: Path
    path: str
    size: int
    sha256: str

    def read(self):
        raw, info = _read(self.root, self.path, self.size)
        _need(len(raw) == self.size and hashlib.sha256(raw).hexdigest() == self.sha256,
              "Reviewed overlay bytes differ: " + self.path)
        return raw, info


def load_update(root):
    """Validate every declared asset before serving; an invalid overlay is fatal."""
    root = Path(root).resolve(strict=True)
    updates = root / "updates"
    try:
        update_info = updates.lstat()
    except FileNotFoundError:
        return None, {}
    _need(stat.S_ISDIR(update_info.st_mode) and not _alias(update_info), "Invalid updates directory")
    pointer = updates / "current.json"
    try:
        pointer.lstat()
    except FileNotFoundError:
        return None, {}
    spec, _ = _json(root, "updates/current.json", 1_000_000)
    _need(type(spec) is dict and set(spec) == {
        "schema_version", "update_id", "base_inventory_sha256", "files"},
        "Exact overlay manifest fields required")
    _need(type(spec["schema_version"]) is int and spec["schema_version"] == 2 and
          spec["update_id"] == UPDATE_ID, "Unsupported atlas update schema or ID")
    _, inventory = _json(root, "snapshot/FILES.json", 8_000_000)
    _need(hashlib.sha256(inventory).hexdigest() == spec["base_inventory_sha256"],
          "Overlay belongs to a different immutable base inventory")
    rows = spec["files"]
    _need(type(rows) is list and 0 < len(rows) <= MAX_FILES, "Finite overlay roster required")
    routes = {}
    paths = set()
    total = 0
    for row in rows:
        _need(type(row) is dict and set(row) == {"http_path", "path", "bytes", "sha256"},
              "Exact overlay file fields required")
        route = row["http_path"]
        _need(type(route) is str and route.startswith(PREFIX), "Overlay route leaves atlas prefix")
        suffix = route[len(PREFIX):]
        relative = _relative(suffix)
        allowed_download = (len(relative.parts) == 2 and relative.parts[0] == "downloads" and
                            (relative.suffix in {".pdf", ".png", ".jpg", ".svg", ".npy", ".tsv", ".csv", ".json", ".md", ".txt", ".bed"} or
                             relative.name.endswith((".tsv.gz", ".tsv.xz")) or
                             relative.name in {"Microglia_TE_model_audit_tables.zip", "Figure2_BCDE_reviewed_tables_and_PDFs.zip", "Microglia_RNA_TE_QC_panels_and_tables.zip", "Microglia_RNA_TE_DE_tables_and_figures.zip", "Microglia_TE_ATAC_MAnorm2_tables.zip", "Microglia_per_animal_peak_TE_20261023.zip", "Microglia_TE_ATAC_coverage_20261023_data.zip", "Microglia_RNA_DEG_all_results_20261025.zip"}))
        _need(route in REQUIRED or allowed_download, "Unreviewed overlay route class: " + route)
        expected_path = "updates/" + UPDATE_ID + "/atlas/" + suffix
        _need(row["path"] == expected_path, "Overlay disk and HTTP paths must match exactly")
        _relative(row["path"])
        _need(route not in routes and row["path"] not in paths, "Duplicate overlay route or source path")
        size = row["bytes"]
        _need(type(size) is int and 0 < size <= MAX_FILE_BYTES, "Overlay file size outside bound")
        _need(type(row["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
              "Exact SHA-256 required")
        total += size
        _need(total <= MAX_TOTAL_BYTES, "Overlay total size outside bound")
        asset = Asset(root, row["path"], size, row["sha256"])
        asset.read()
        routes[route] = asset
        paths.add(row["path"])
    _need(REQUIRED <= routes.keys(), "Overlay lacks a required HTML/script/style/data route")
    return spec, routes


def handler_factory(directory, routes):
    class UpdatedAtlasHandler(http.server.SimpleHTTPRequestHandler):
        def send_head(self):
            requested = unquote(urlsplit(self.path).path)
            normalized = posixpath.normpath("/" + requested.lstrip("/"))
            route = normalized
            if normalized == PREFIX.rstrip("/") and PREFIX + "index.html" in routes:
                if not requested.endswith("/"):
                    self.send_response(301)
                    self.send_header("Location", PREFIX)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return None
                route = PREFIX + "index.html"
            asset = routes.get(route)
            if asset is None:
                return super().send_head()
            try:
                raw, info = asset.read()
            except (OSError, ValueError):
                self.send_error(503, "Reviewed atlas overlay asset failed verification")
                return None
            self.send_response(200)
            self.send_header("Content-Type", "application/x-xz" if str(asset.path).endswith(".tsv.xz") else "application/gzip" if str(asset.path).endswith(".tsv.gz") else self.guess_type(asset.path))
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Last-Modified", self.date_time_string(info.st_mtime))
            self.end_headers()
            return io.BytesIO(raw)

        def end_headers(self):
            self.send_header("Cache-Control", "no-cache")
            super().end_headers()

    return functools.partial(UpdatedAtlasHandler, directory=str(directory))
