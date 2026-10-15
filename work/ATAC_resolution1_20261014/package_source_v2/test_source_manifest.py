"""Actual accepted manifest regression and generated unsafe-path boundaries."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from common import SRC, load, safe_source_member, verify_source

ACCEPTED = None
POLICY = load(SRC / 'package_policy.json')


class ManifestPaths(unittest.TestCase):
    def test_actual_accepted_initial16_manifest_and_nested_workflow(self):
        manifest = load(ACCEPTED / 'source_manifest.json')
        self.assertEqual(len(manifest), 16)
        self.assertIn('workflow/full_study_20261008_r3/atac_postmapping.py', manifest)
        self.assertEqual(verify_source(ACCEPTED, POLICY['accepted_initial_source_manifest_sha256']),
                         '1602256721588ea9839ec42b5e0c5ca77793c278ee46d5ef3cf1683d0a59d115')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'frozen_source'; self.root.mkdir()
        self.nested = self.root / 'workflow/revision/tool.py'; self.nested.parent.mkdir(parents=True)
        self.nested.write_text('# generated fixture only\n')
        self.digest = hashlib.sha256(self.nested.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, name):
        path = self.root / 'source_manifest.json'
        path.write_text(json.dumps({name: self.digest}))

    def test_safe_generated_nested_regular_descendant(self):
        self.manifest('workflow/revision/tool.py')
        verify_source(self.root)

    def test_changed_nested_content_is_rejected(self):
        self.manifest('workflow/revision/tool.py'); self.nested.write_text('changed')
        with self.assertRaises(RuntimeError): verify_source(self.root)

    def test_absolute_member_rejected(self):
        for name in [str(self.nested), 'C:/outside.py']:
            self.manifest(name)
            with self.subTest(name=name), self.assertRaises(RuntimeError): verify_source(self.root)

    def test_parent_traversal_rejected(self):
        for name in ['../outside.py', 'workflow/../workflow/revision/tool.py', 'workflow/revision/../../outside.py']:
            self.manifest(name)
            with self.subTest(name=name), self.assertRaises(RuntimeError): verify_source(self.root)

    def test_dot_empty_and_double_slash_aliases_rejected(self):
        for name in ['', '.', './workflow/revision/tool.py', 'workflow//revision/tool.py', 'workflow/revision/tool.py/']:
            self.manifest(name)
            with self.subTest(name=name), self.assertRaises(RuntimeError): verify_source(self.root)

    def test_backslash_member_rejected(self):
        self.manifest('workflow\\revision\\tool.py')
        with self.assertRaises(RuntimeError): verify_source(self.root)

    def test_escaping_leaf_symlink_rejected(self):
        outside = Path(self.temp.name) / 'outside.py'; outside.write_text('outside')
        (self.root / 'escape.py').symlink_to(outside)
        self.manifest('escape.py')
        with self.assertRaises(RuntimeError): verify_source(self.root)

    def test_escaping_directory_symlink_rejected(self):
        outside = Path(self.temp.name) / 'outside'; outside.mkdir(); (outside / 'tool.py').write_text('outside')
        (self.root / 'escape').symlink_to(outside, target_is_directory=True)
        self.manifest('escape/tool.py')
        with self.assertRaises(RuntimeError): verify_source(self.root)

    def test_even_in_tree_symlink_alias_is_rejected(self):
        (self.root / 'alias.py').symlink_to(self.nested)
        self.manifest('alias.py')
        with self.assertRaises(RuntimeError): verify_source(self.root)

    def test_source_root_symlink_rejected(self):
        alias = Path(self.temp.name) / 'source_alias'; alias.symlink_to(self.root, target_is_directory=True)
        self.manifest('workflow/revision/tool.py')
        with self.assertRaises(RuntimeError): verify_source(alias)

    def test_missing_or_directory_member_rejected(self):
        for name in ['missing.py', 'workflow/revision']:
            self.manifest(name)
            with self.subTest(name=name), self.assertRaises(RuntimeError): verify_source(self.root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--accepted-initial-source', type=Path, required=True)
    args = parser.parse_args()
    ACCEPTED = args.accepted_initial_source
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ManifestPaths)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun != 12 or result.skipped:
        raise SystemExit(1)
    print('passed12_manifest_path_regressions_including_actual_accepted16_source; no study matrix or graph reads')
