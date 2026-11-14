#!/usr/bin/env python3
"""Local evidence helper regression tests; no external services."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import evidence

CONTEXT = {'target': 'https://example.test', 'environment': 'local', 'revision': 'abc', 'run_id': 'demo'}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'redacted.txt').write_text('synthetic test result\n')
        self.manifest = evidence.create_manifest(self.root, ['redacted.txt'], CONTEXT)

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_unsigned(self):
        result = evidence.verify_manifest(self.root, self.manifest)
        self.assertTrue(result['valid'])
        self.assertFalse(result['signature_verified'])

    def test_changed(self):
        (self.root/'redacted.txt').write_text('modified')
        self.assertFalse(evidence.verify_manifest(self.root, self.manifest)['valid'])

    def test_missing(self):
        (self.root/'redacted.txt').unlink()
        self.assertEqual(evidence.verify_manifest(self.root, self.manifest)['failures'][0]['reason'], 'missing')

    def test_bad_paths(self):
        for name in ('../secret', '/etc/passwd', 'C:/secret', 'dir\\secret', ''):
            with self.assertRaises(ValueError):
                evidence.create_manifest(self.root, [name], CONTEXT)

    def test_symlink(self):
        (self.root/'link').symlink_to(self.root/'redacted.txt')
        with self.assertRaises(ValueError):
            evidence.create_manifest(self.root, ['link'], CONTEXT)

    def test_symlink_directory(self):
        (self.root/'data').mkdir()
        (self.root/'data'/'file.txt').write_text('synthetic')
        (self.root/'dir-link').symlink_to(self.root/'data', target_is_directory=True)
        with self.assertRaises(ValueError):
            evidence.create_manifest(self.root, ['dir-link/file.txt'], CONTEXT)

    def test_claimed_signature_not_trusted(self):
        self.manifest['signature_status'] = 'verified'
        self.assertFalse(evidence.verify_manifest(self.root, self.manifest)['signature_verified'])

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            evidence.create_manifest(self.root, ['redacted.txt', './redacted.txt'], CONTEXT)
        self.manifest['files'].append(deepcopy(self.manifest['files'][0]))
        with self.assertRaises(ValueError):
            evidence.verify_manifest(self.root, self.manifest)

    def test_bad_context_or_digest(self):
        with self.assertRaises(ValueError):
            evidence.create_manifest(self.root, ['redacted.txt'], {})
        self.manifest['files'][0]['sha256'] = 'invalid'
        with self.assertRaises(ValueError):
            evidence.verify_manifest(self.root, self.manifest)

    def test_context_minimization(self):
        context = dict(CONTEXT, password='never-copy')
        result = evidence.create_manifest(self.root, ['redacted.txt'], context)
        self.assertNotIn('password', result['context'])

    def test_cli(self):
        (self.root/'context.json').write_text(json.dumps(CONTEXT))
        common = [sys.executable, str(Path(evidence.__file__))]
        create = common + ['create', '--root', str(self.root), '--context', str(self.root/'context.json'),
                           '--out', str(self.root/'manifest.json'), 'redacted.txt']
        verify = common + ['verify', '--root', str(self.root), '--manifest', str(self.root/'manifest.json')]
        self.assertEqual(subprocess.run(create, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(create, capture_output=True).returncode, 2)
        self.assertEqual(subprocess.run(verify, capture_output=True).returncode, 0)
        (self.root/'redacted.txt').write_text('changed')
        self.assertEqual(subprocess.run(verify, capture_output=True).returncode, 1)


if __name__ == '__main__':
    unittest.main()
