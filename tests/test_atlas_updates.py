"""Tiny generated overlay/restore fixtures only; no real archive rehash or download."""
import copy
import hashlib
import http.server
import io
import json
from pathlib import Path
import sys
import stat
import tarfile
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas_snapshot as snapshot
import atlas_updates as overlay
import start_atlas


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Overlay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'snapshot').mkdir()
        self.inventory = b'{"files":[],"generated":true}\n'
        (self.root / 'snapshot/FILES.json').write_bytes(self.inventory)
        self.rows = []
        for route in sorted(overlay.REQUIRED):
            suffix = route[len(overlay.PREFIX):]
            name = 'updates/' + overlay.UPDATE_ID + '/atlas/' + suffix
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = ('generated ' + suffix + '\n').encode()
            path.write_bytes(raw)
            self.rows.append(dict(http_path=route, path=name, bytes=len(raw), sha256=sha(raw)))
        self.spec = dict(schema_version=2, update_id=overlay.UPDATE_ID,
                         base_inventory_sha256=sha(self.inventory), files=self.rows)
        self.pointer = self.root / 'updates/current.json'
        self.write()

    def write(self, spec=None):
        self.pointer.write_text(json.dumps(self.spec if spec is None else spec))

    def test_valid_portable_explicit_routes(self):
        spec, routes = overlay.load_update(self.root)
        self.assertEqual(spec, self.spec)
        self.assertEqual(set(routes), overlay.REQUIRED)
        for route, asset in routes.items():
            self.assertEqual(asset.read()[0], ('generated ' + route[len(overlay.PREFIX):] + '\n').encode())
        # No absolute development-machine path is recorded in portable manifests.
        self.assertNotIn(str(self.root), self.pointer.read_text())

    def test_explicit_png_preview_route(self):
        suffix = 'downloads/diagnostic.preview.png'
        relative = 'updates/' + overlay.UPDATE_ID + '/atlas/' + suffix
        path = self.root/relative
        path.parent.mkdir(exist_ok=True)
        raw = b'generated PNG preview bytes'
        path.write_bytes(raw)
        self.rows.append(dict(http_path=overlay.PREFIX+suffix, path=relative,
                              bytes=len(raw), sha256=sha(raw)))
        self.write()
        _, routes = overlay.load_update(self.root)
        self.assertEqual(routes[overlay.PREFIX+suffix].read()[0], raw)

    def test_absent_pointer_is_optional_but_unreadable_pointer_is_fatal(self):
        self.pointer.unlink()
        self.assertEqual(overlay.load_update(self.root), (None, {}))
        self.write()
        original = Path.lstat
        canonical = self.pointer.resolve()
        def denied(path, *args, **kwargs):
            if path == canonical:
                raise PermissionError('generated unreadable pointer')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'lstat', denied), self.assertRaises(PermissionError):
            overlay.load_update(self.root)

    def test_typed_schema_duplicate_and_base_binding(self):
        for changes in [dict(schema_version=True), dict(schema_version=2.0),
                        dict(update_id='old_QC74'), dict(base_inventory_sha256='0'*64)]:
            self.write(dict(self.spec, **changes))
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                overlay.load_update(self.root)
        self.write(dict(self.spec, files=self.rows + [self.rows[0]]))
        with self.assertRaises(ValueError):
            overlay.load_update(self.root)
        self.pointer.write_text('{"schema_version":2,"schema_version":2}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            overlay.load_update(self.root)

    def test_path_and_route_aliases_are_rejected(self):
        for field, value in [('http_path', '/outside/index.html'),
                             ('http_path', overlay.PREFIX + '../index.html'),
                             ('http_path', overlay.PREFIX + 'data//rna_microglia.json'),
                             ('http_path', overlay.PREFIX + '%69ndex.html'),
                             ('http_path', overlay.PREFIX + 'qc_status.json'),
                             ('path', '/absolute/index.html'),
                             ('path', 'updates/../outside'),
                             ('path', self.rows[1]['path'])]:
            spec = copy.deepcopy(self.spec)
            spec['files'][0][field] = value
            self.write(spec)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                overlay.load_update(self.root)

    def test_size_hash_missing_and_incomplete_assets_fail_closed(self):
        for field, value in [('bytes', True), ('bytes', 0), ('bytes', overlay.MAX_FILE_BYTES+1),
                             ('bytes', self.rows[0]['bytes']+1), ('sha256', '0'*64), ('sha256', 'invalid')]:
            spec = copy.deepcopy(self.spec)
            spec['files'][0][field] = value
            self.write(spec)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                overlay.load_update(self.root)
        self.write(dict(self.spec, files=self.rows[:-1]))
        with self.assertRaises(ValueError):
            overlay.load_update(self.root)
        self.write()
        (self.root/self.rows[0]['path']).unlink()
        with self.assertRaises(FileNotFoundError):
            overlay.load_update(self.root)

    def test_symlink_file_directory_and_pointer_fail_closed(self):
        original = self.pointer.read_bytes()
        for mode in ['file', 'directory', 'pointer']:
            with self.subTest(mode=mode):
                if mode == 'file':
                    path = self.root/self.rows[0]['path']
                elif mode == 'directory':
                    path = self.root/'updates'/overlay.UPDATE_ID/'atlas/data'
                else:
                    path = self.pointer
                saved = path.with_name(path.name + '.generated-original')
                path.rename(saved)
                try:
                    try:
                        path.symlink_to(saved, target_is_directory=saved.is_dir())
                    except OSError as error:
                        self.skipTest('Local OS cannot create a generated symlink: '+str(error))
                    with self.assertRaises((ValueError, OSError)):
                        overlay.load_update(self.root)
                finally:
                    if path.is_symlink():
                        path.unlink()
                    saved.rename(path)
        self.assertEqual(self.pointer.read_bytes(), original)

    def test_windows_directory_junction_reparse_is_an_alias(self):
        self.assertTrue(overlay._alias(SimpleNamespace(
            st_mode=stat.S_IFDIR, st_file_attributes=0x400)))
        self.assertFalse(overlay._alias(SimpleNamespace(
            st_mode=stat.S_IFDIR, st_file_attributes=0)))

    def test_http_overlay_alias_base_and_changed_asset(self):
        _, routes = overlay.load_update(self.root)
        base = self.root/'outputs/p5_workflow'
        index = base/overlay.PREFIX.lstrip('/')/'index.html'
        index.parent.mkdir(parents=True)
        index.write_bytes(b'generated original base')
        (index.parent/'base.js').write_bytes(b'generated base library')
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), overlay.handler_factory(base, routes))
        worker = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .01})
        worker.start()
        try:
            origin = 'http://127.0.0.1:'+str(server.server_port)
            for suffix in ['index.html', './index.html', 'data/../index.html', '']:
                with urlopen(origin+overlay.PREFIX+suffix, timeout=3) as result:
                    self.assertEqual(result.read(), b'generated index.html\n')
                    self.assertEqual(result.headers['Cache-Control'], 'no-cache')
            with urlopen(origin+overlay.PREFIX+'base.js', timeout=3) as result:
                self.assertEqual(result.read(), b'generated base library')
            with urlopen(Request(origin+overlay.PREFIX+'index.html', method='HEAD'), timeout=3) as result:
                self.assertEqual(result.read(), b'')
            target = routes[overlay.PREFIX+'index.html']
            (self.root/target.path).write_bytes(b'changed AFTER startup')
            with self.assertRaises(HTTPError) as error:
                urlopen(origin+overlay.PREFIX+'index.html', timeout=3)
            self.assertEqual(error.exception.code, 503)
            self.assertEqual(index.read_bytes(), b'generated original base')
        finally:
            server.shutdown()
            worker.join(timeout=3)
            server.server_close()

    def test_launcher_rejects_overlay_before_base_payload_checks(self):
        self.write(dict(self.spec, schema_version=0))
        with patch.object(start_atlas, 'ROOT', self.root), patch.object(start_atlas, 'load_manifests') as load, \
             patch.object(sys, 'argv', ['start_atlas.py', '--check']), self.assertRaises(SystemExit):
            start_atlas.main()
        load.assert_not_called()

    def test_base_snapshot_explicitly_ignores_invalid_overlay(self):
        self.write(dict(self.spec, schema_version=0))
        with patch.object(start_atlas, 'ROOT', self.root), \
             patch.object(start_atlas, 'load_update', side_effect=AssertionError('must not read overlay')), \
             patch.object(start_atlas, 'load_manifests', return_value=({}, {}, {})), \
             patch.object(start_atlas, 'verify_files', return_value=([], [])) as verify, \
             patch.object(sys, 'argv', ['start_atlas.py', '--base-snapshot', '--check']), \
             patch('sys.stdout', new_callable=io.StringIO):
            start_atlas.main()
        self.assertEqual(verify.call_count, 1)


class TinyRestore(unittest.TestCase):
    def test_original_restore_survives_repository_relocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'another-computer'
            (root/'snapshot').mkdir(parents=True)
            root = root.resolve()
            payloads = {'outputs/p5_workflow/base.txt': b'generated base bytes\n',
                        'work/generated_builder.py': b'# generated archival original\n'}
            rows = [dict(path=name, bytes=len(raw), sha256=sha(raw)) for name, raw in payloads.items()]
            inventory = (json.dumps(dict(files=rows, uncompressed_bytes=sum(map(len, payloads.values()))))+'\n').encode()
            (root/'snapshot/FILES.json').write_bytes(inventory)
            archive = io.BytesIO()
            with tarfile.open(fileobj=archive, mode='w:gz') as tar:
                for name, raw in payloads.items():
                    member = tarfile.TarInfo(name)
                    member.size = len(raw)
                    tar.addfile(member, io.BytesIO(raw))
            raw = archive.getvalue()
            parts = []
            for n, offset in enumerate(range(0, len(raw), 31)):
                content = raw[offset:offset+31]
                name = 'part-%03d'%n
                (root/'snapshot'/name).write_bytes(content)
                parts.append(dict(path=name, bytes=len(content), sha256=sha(content)))
            manifest = dict(file_manifest='FILES.json', file_manifest_sha256=sha(inventory), files=len(rows), parts=parts)
            (root/'snapshot/manifest.json').write_text(json.dumps(manifest))
            before = {p.name: p.read_bytes() for p in (root/'snapshot').iterdir()}
            with patch.object(snapshot, 'ROOT', root):
                self.assertEqual(snapshot.restore()['restored_files'], 2)
                _, _, expected = snapshot.load_manifests()
                self.assertEqual(snapshot.verify_files(expected), ([], []))
                self.assertEqual(snapshot.restore()['restored_files'], 0)
            for name, data in payloads.items():
                self.assertEqual((root/name).read_bytes(), data)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root/'snapshot').iterdir()})


if __name__ == '__main__':
    unittest.main(verbosity=2)
