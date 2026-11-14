#!/usr/bin/env python3
"""Validate paired audit results and emit conservative, deterministic differences."""
import argparse
from collections import Counter
import json
from pathlib import Path

SEVERITIES = {'critical', 'high', 'medium', 'low', 'info'}
STATUSES = {'open', 'fixed_unverified', 'verified_fixed', 'risk_accepted', 'not_retested'}


def validate(data):
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported schema_version')
    for field in ('run_id', 'timestamp', 'target', 'scope_id', 'environment', 'revision', 'test_profile'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError('Missing/invalid ' + field)
    if data.get('phase') not in ('baseline', 'final'):
        raise ValueError('Invalid phase')
    ids, keys = set(), set()
    if not isinstance(data.get('findings'), list) or not isinstance(data.get('coverage'), list):
        raise ValueError('findings and coverage must be lists')
    for row in data['coverage']:
        if not row.get('control') or row.get('status') not in {'pass', 'fail', 'not_tested', 'not_applicable'}:
            raise ValueError('Invalid coverage row')
        if row['status'] in {'pass', 'fail'} and not row.get('evidence'):
            raise ValueError('Coverage pass/fail needs evidence')
        if row['status'] in {'not_tested', 'not_applicable'} and not row.get('reason'):
            raise ValueError('Coverage gap needs reason')
    for f in data['findings']:
        for field in ('id', 'key', 'title', 'asset'):
            if not isinstance(f.get(field), str) or not f[field].strip():
                raise ValueError('Finding missing ' + field)
        if f['id'] in ids or f['key'] in keys:
            raise ValueError('Duplicate finding id/key')
        ids.add(f['id'])
        keys.add(f['key'])
        if f.get('severity') not in SEVERITIES or f.get('status') not in STATUSES:
            raise ValueError('Invalid severity/status: ' + f['id'])
        if f.get('confidence') not in {'confirmed', 'suspected'}:
            raise ValueError('Invalid confidence')
        if f['confidence'] == 'confirmed' and not f.get('evidence'):
            raise ValueError('Confirmed finding requires evidence')
        test = f.get('test', {})
        if test and test.get('result') not in {'pass', 'fail', 'blocked', 'not_tested'}:
            raise ValueError('Invalid test result')
        if f['status'] == 'verified_fixed' and not proven_pass(test):
            raise ValueError('verified_fixed needs a timestamped passing test and evidence')
    return data


def proven_pass(test):
    return (test.get('result') == 'pass' and
            all(test.get(k) for k in ('id', 'surface', 'role', 'timestamp', 'evidence')))


def compare(before, after):
    validate(before)
    validate(after)
    if before['phase'] != 'baseline' or after['phase'] != 'final':
        raise ValueError('Expected baseline then final')
    different = [k for k in ('target', 'scope_id', 'environment', 'test_profile')
                 if before[k] != after[k]]
    comparable = not different
    old = {f['id']: f for f in before['findings']}
    new = {f['id']: f for f in after['findings']}
    rows = []
    for fid, base in old.items():
        current = new.get(fid)
        result, reason = 'unverified', 'No equivalent evidenced passing retest'
        if current is None:
            reason = 'Original finding omitted; omission is not a fix'
        elif current['key'] != base['key']:
            reason = 'Stable finding identity changed'
        elif current.get('test', {}).get('result') == 'fail':
            result, reason = 'persisted', 'Retest still fails'
        elif comparable and base['confidence'] == 'confirmed':
            bt, ft = base.get('test', {}), current.get('test', {})
            equivalent = all(bt.get(k) and bt[k] == ft.get(k) for k in ('id', 'surface', 'role'))
            if (equivalent and bt.get('result') == 'fail' and
                    current['status'] == 'verified_fixed' and proven_pass(ft)
                    and ft['timestamp'] != bt.get('timestamp')
                    and ft['evidence'] != bt.get('evidence')):
                result, reason = 'verified_fixed', 'Equivalent failed test now passes with fresh evidence'
        if different and result == 'unverified':
            reason = 'Noncomparable: ' + ', '.join(different)
        rows.append({'id': fid, 'title': base['title'], 'severity': base['severity'],
                     'result': result, 'reason': reason})
    additions = [{'id': f['id'], 'key': f['key'], 'title': f['title'], 'severity': f['severity']}
                 for fid, f in new.items() if fid not in old]
    before_coverage = {r['control']: r for r in before['coverage']}
    coverage_regressions = [r['control'] for r in after['coverage']
                            if r['status'] == 'fail' and
                            before_coverage.get(r['control'], {}).get('status') == 'pass']
    return {'schema_version': 1, 'comparable': comparable, 'differences': different,
            'baseline_revision': before['revision'], 'final_revision': after['revision'],
            'counts': dict(Counter(r['result'] for r in rows)), 'new_count': len(additions),
            'findings': rows, 'new_findings': additions,
            'coverage_regressions': coverage_regressions,
            'severity_before': dict(Counter(f['severity'] for f in before['findings'])),
            'severity_remaining': dict(Counter(
                [r['severity'] for r in rows if r['result'] != 'verified_fixed'] +
                [f['severity'] for f in additions])),
            'coverage_before': dict(Counter(r['status'] for r in before['coverage'])),
            'coverage_after': dict(Counter(r['status'] for r in after['coverage'])),
            'limitation': 'Structural comparison only; independently verify evidence and deployment.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('compare')
    c.add_argument('before', type=Path)
    c.add_argument('after', type=Path)
    c.add_argument('--out', required=True, type=Path)
    v = sub.add_parser('validate')
    v.add_argument('file', type=Path)
    args = p.parse_args()
    try:
        if args.command == 'validate':
            data = validate(json.loads(args.file.read_text(encoding='utf-8')))
            print(json.dumps({'valid': True, 'findings': len(data['findings'])}))
        else:
            result = compare(json.loads(args.before.read_text(encoding='utf-8')),
                             json.loads(args.after.read_text(encoding='utf-8')))
            if args.out.resolve() in (args.before.resolve(), args.after.resolve()):
                raise ValueError('Output cannot overwrite input evidence')
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({k: result[k] for k in ('comparable', 'counts', 'new_count')}, ensure_ascii=False))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        p.exit(2, 'Result error: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
