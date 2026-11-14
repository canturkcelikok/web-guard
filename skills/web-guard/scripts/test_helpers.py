#!/usr/bin/env python3
"""Offline/local regression tests; never contacts an external target."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import observe
import results
import gate
from datetime import datetime, timezone


def fixture():
    b = {'schema_version': 1, 'run_id': 'local-demo', 'phase': 'baseline',
         'timestamp': '2026-11-14T12:00:00Z', 'target': 'https://example.test',
         'scope_id': 'scope-v1', 'environment': 'local', 'revision': 'a', 'test_profile': 'tests-v1',
         'coverage': [{'control': 'AUTHZ', 'status': 'fail', 'evidence': ['before.txt']}],
         'findings': [{'id': 'WG-001', 'key': 'AUTHZ|order|read', 'title': 'Tenant access',
                       'asset': 'order', 'severity': 'high', 'status': 'open',
                       'confidence': 'confirmed', 'evidence': ['before.txt'],
                       'test': {'id': 'authz-v1', 'surface': 'local', 'role': 'alpha-user',
                                'result': 'fail', 'timestamp': '2026-11-14T12:00:00Z',
                                'evidence': ['before.txt']}}]}
    a = deepcopy(b)
    a.update(phase='final', revision='b', timestamp='2026-11-14T12:01:00Z')
    a['coverage'][0].update(status='pass', evidence=['after.txt'])
    a['findings'][0]['status'] = 'verified_fixed'
    a['findings'][0]['test'].update(result='pass', timestamp=a['timestamp'], evidence=['after.txt'])
    return b, a


class ComparisonTests(unittest.TestCase):
    def test_fixed(self):
        self.assertEqual(results.compare(*fixture())['counts'], {'verified_fixed': 1})

    def test_omitted_not_fixed(self):
        b, a = fixture()
        a['findings'] = []
        self.assertEqual(results.compare(b, a)['counts'], {'unverified': 1})

    def test_scope_change(self):
        b, a = fixture()
        a['scope_id'] = 'narrower'
        r = results.compare(b, a)
        self.assertFalse(r['comparable'])
        self.assertEqual(r['counts'], {'unverified': 1})

    def test_old_evidence(self):
        b, a = fixture()
        a['findings'][0]['test']['evidence'] = ['before.txt']
        self.assertEqual(results.compare(b, a)['counts'], {'unverified': 1})

    def test_role_change(self):
        b, a = fixture()
        a['findings'][0]['test']['role'] = 'admin'
        self.assertEqual(results.compare(b, a)['counts'], {'unverified': 1})

    def test_missing_proof_rejected(self):
        b, a = fixture()
        a['findings'][0]['test']['evidence'] = []
        with self.assertRaises(ValueError):
            results.compare(b, a)

    def test_duplicate_rejected(self):
        b, a = fixture()
        b['findings'].append(deepcopy(b['findings'][0]))
        with self.assertRaises(ValueError):
            results.compare(b, a)

    def test_persisted_new_and_regression(self):
        b, a = fixture()
        b['coverage'].append({'control': 'SESSION', 'status': 'pass', 'evidence': ['session-before']})
        a['coverage'].append({'control': 'SESSION', 'status': 'fail', 'evidence': ['session-after']})
        a['findings'][0]['status'] = 'open'
        a['findings'][0]['test']['result'] = 'fail'
        f = deepcopy(a['findings'][0])
        f.update(id='WG-002', key='SESSION|logout', title='Logout')
        a['findings'].append(f)
        r = results.compare(b, a)
        self.assertEqual(r['counts'], {'persisted': 1})
        self.assertEqual(r['new_count'], 1)
        self.assertEqual(r['coverage_regressions'], ['SESSION'])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, data in zip(('before.json', 'after.json'), fixture()):
                (root/name).write_text(json.dumps(data))
            command = [sys.executable, str(Path(results.__file__)), 'compare',
                       str(root/'before.json'), str(root/'after.json'), '--out', str(root/'diff.json')]
            p = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads((root/'diff.json').read_text())['counts'], {'verified_fixed': 1})


class GateTests(unittest.TestCase):
    NOW = datetime(2026, 11, 14, 12, 2, tzinfo=timezone.utc)

    def evaluate(self, b, a, required=None):
        return gate.evaluate(b, a, required or ['AUTHZ'], ['critical', 'high'], now=self.NOW)

    def test_pass(self):
        self.assertTrue(self.evaluate(*fixture())['pass'])

    def test_missing_required(self):
        self.assertFalse(self.evaluate(*fixture(), required=['AUTHZ', 'CHANGE'])['pass'])

    def test_scope_change(self):
        b, a = fixture()
        a['environment'] = 'different'
        self.assertFalse(self.evaluate(b, a)['pass'])

    def test_stale_result(self):
        b, a = fixture()
        a['timestamp'] = '2026-11-10T12:01:00Z'
        self.assertFalse(self.evaluate(b, a)['pass'])

    def test_future_result(self):
        b, a = fixture()
        a['timestamp'] = '2026-11-20T12:01:00Z'
        self.assertFalse(self.evaluate(b, a)['pass'])

    def test_open_high(self):
        b, a = fixture()
        a['findings'][0]['status'] = 'fixed_unverified'
        self.assertFalse(self.evaluate(b, a)['pass'])

    def test_omission(self):
        b, a = fixture()
        a['findings'] = []
        self.assertFalse(self.evaluate(b, a)['pass'])

    def test_new_high(self):
        b, a = fixture()
        f = deepcopy(a['findings'][0])
        f.update(id='WG-002', key='NEW|api', status='open')
        a['findings'].append(f)
        self.assertFalse(self.evaluate(b, a)['pass'])

    def test_duplicate_coverage(self):
        b, a = fixture()
        a['coverage'].append(deepcopy(a['coverage'][0]))
        with self.assertRaises(ValueError):
            self.evaluate(b, a)

    def test_invalid_budget_or_time(self):
        b, a = fixture()
        with self.assertRaises(ValueError):
            gate.evaluate(b, a, [], ['high'], now=self.NOW)
        with self.assertRaises(ValueError):
            gate.evaluate(b, a, ['AUTHZ'], ['high'], max_age_hours=-1, now=self.NOW)
        a['timestamp'] = '2026-11-14T12:00:00'
        with self.assertRaises(ValueError):
            self.evaluate(b, a)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            b, a = fixture()
            now = datetime.now(timezone.utc)
            b['timestamp'] = (now - gate.timedelta(minutes=2)).isoformat()
            a['timestamp'] = now.isoformat()
            b['findings'][0]['test']['timestamp'] = b['timestamp']
            a['findings'][0]['test']['timestamp'] = a['timestamp']
            for name, data in (('b.json', b), ('a.json', a)):
                (root/name).write_text(json.dumps(data))
            command = [sys.executable, str(Path(gate.__file__)), '--before', str(root/'b.json'),
                       '--after', str(root/'a.json'), '--required-control', 'AUTHZ']
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(subprocess.run(command + ['--required-control', 'CHANGE'], capture_output=True).returncode, 1)
            (root/'a.json').write_text('{bad')
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)


class ObserveTests(unittest.TestCase):
    def test_invalid_urls(self):
        for url in ('ftp://example.test', 'https://user:secret@example.test',
                    'https://example.test/?token=secret', 'https://example.test/#secret',
                    'https://example.test:8080'):
            with self.assertRaises(ValueError):
                observe.target_parts(url)

    def test_private_blocked(self):
        with patch.object(observe.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 80))]):
            with self.assertRaises(ValueError):
                observe.observe('http://localhost')

    def test_local_response_redaction_no_redirect(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(302)
                self.send_header('Set-Cookie', 'session=PRIVATE_COOKIE')
                self.send_header('Location', 'https://outside.test/?token=PRIVATE_TOKEN')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            # Pin the test-only ephemeral port via mocked socket creation; production helper stays 80/443.
            original = observe.socket.create_connection
            def connect(address, timeout=8, source_address=None):
                return original(server.server_address, timeout, source_address)
            with patch.object(observe.socket, 'create_connection', side_effect=connect):
                r = observe.observe('http://127.0.0.1/', allow_private=True)
            self.assertEqual(r['status'], 302)
            self.assertEqual(len(requests), 1)
            self.assertNotIn('PRIVATE_', json.dumps(r))
            self.assertEqual(r['headers']['x-content-type-options'], ['nosniff'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
