#!/usr/bin/env python3
"""Fail-closed release policy for paired Web Guard result files; no network calls."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import results


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError('Timestamp must be a string')
    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return value.astimezone(timezone.utc)


def evaluate(before, after, required, blocked, max_age_hours=24, now=None):
    if not required or any(not isinstance(c, str) or not c.strip() for c in required):
        raise ValueError('Explicit required controls are mandatory')
    if not blocked or not set(blocked) <= results.SEVERITIES:
        raise ValueError('Explicit valid blocked severities required')
    if not 0 < max_age_hours <= 8760:
        raise ValueError('max_age_hours must be >0 and <=8760')
    diff = results.compare(before, after)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Current time must include timezone')
    reasons = []
    final_time = parse_time(after['timestamp'])
    if final_time > now + timedelta(minutes=5):
        reasons.append('Final evidence timestamp is in the future')
    if now - final_time > timedelta(hours=max_age_hours):
        reasons.append('Final evidence is stale')
    if final_time < parse_time(before['timestamp']):
        reasons.append('Final evidence predates baseline')
    if not diff['comparable']:
        reasons.append('Noncomparable scope/environment/profile/target')
    coverage = {}
    for row in after['coverage']:
        if row['control'] in coverage:
            raise ValueError('Duplicate coverage control')
        coverage[row['control']] = row
    for control in sorted(set(required)):
        row = coverage.get(control, {})
        if row.get('status') != 'pass' or not row.get('evidence'):
            reasons.append('Required control lacks evidenced pass: ' + control)
    verified = {r['id'] for r in diff['findings'] if r['result'] == 'verified_fixed'}
    for f in before['findings']:
        if f['severity'] in blocked and f['id'] not in verified:
            reasons.append('Unresolved baseline finding: ' + f['id'])
    old_ids = {f['id'] for f in before['findings']}
    for f in after['findings']:
        if f['severity'] in blocked and (f['id'] not in old_ids or f['id'] not in verified):
            message = 'Unresolved final finding: ' + f['id']
            if 'Unresolved baseline finding: ' + f['id'] not in reasons:
                reasons.append(message)
        if f['id'] in verified:
            tested = parse_time(f['test']['timestamp'])
            original = next(x for x in before['findings'] if x['id'] == f['id'])
            original_time = parse_time(original['test']['timestamp'])
            if tested <= original_time or tested > final_time + timedelta(minutes=5):
                reasons.append('Invalid retest chronology: ' + f['id'])
            if now - tested > timedelta(hours=max_age_hours):
                reasons.append('Stale retest: ' + f['id'])
    for control in diff['coverage_regressions']:
        reasons.append('Coverage regression: ' + control)
    return {'pass': not reasons, 'reasons': reasons, 'required_controls': sorted(set(required)),
            'blocked_severities': sorted(set(blocked)), 'max_age_hours': max_age_hours,
            'limitation': 'Structural gate only; CI must bind trusted evidence to actual target/revision/environment.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', required=True, type=Path)
    p.add_argument('--after', required=True, type=Path)
    p.add_argument('--required-control', required=True, action='append')
    p.add_argument('--block-severity', choices=sorted(results.SEVERITIES), action='append')
    p.add_argument('--max-age-hours', type=float, default=24)
    args = p.parse_args()
    try:
        output = evaluate(json.loads(args.before.read_text(encoding='utf-8')),
                          json.loads(args.after.read_text(encoding='utf-8')),
                          args.required_control, args.block_severity or ['critical', 'high'],
                          args.max_age_hours)
        print(json.dumps(output, ensure_ascii=False))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        p.exit(2, 'Gate input error: ' + str(exc) + '\n')
    p.exit(0 if output['pass'] else 1)


if __name__ == '__main__':
    main()
