#!/usr/bin/env python3
"""Build the verified portable atlas as a static GitHub Pages site."""

from pathlib import Path
import shutil

from atlas_snapshot import ROOT, load_manifests, restore, verify_files
from atlas_updates import load_update


def main():
    update, routes = load_update(ROOT)
    if update is None:
        raise SystemExit("Reviewed atlas overlay is missing")
    _, _, expected = load_manifests()
    missing, changed = verify_files(expected, hashes=True)
    if changed:
        raise SystemExit("Base snapshot has changed: " + repr(changed[:5]))
    if missing:
        restore()
        missing, changed = verify_files(expected, hashes=True)
        if missing or changed:
            raise SystemExit("Base snapshot restoration failed")

    site = ROOT / "_site"
    if site.exists():
        shutil.rmtree(site)
    shutil.copytree(ROOT / "outputs" / "p5_workflow", site)
    for route, asset in routes.items():
        target = site / route.removeprefix("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(asset.read()[0])
    (site / ".nojekyll").touch()
    (site / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<title>GSE212606 atlas</title>'
        '<meta http-equiv="refresh" content="0;url=full_workflow_20261014/'
        'atlas_preview/index.html#rna">'
        '<a href="full_workflow_20261014/atlas_preview/index.html#rna">'
        'Open the GSE212606 atlas</a></html>\n',
        encoding="utf-8",
    )
    print(f"Static atlas ready: {len(routes)} reviewed routes in {site}")


if __name__ == "__main__":
    main()
