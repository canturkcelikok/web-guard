#!/usr/bin/env python3
"""Hash selected redacted evidence. No network, signing keys, or recursive collection."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath

CONTEXT_KEYS = ('target', 'environment', 'revision', 'run_id')


def safe_file(root, name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Evidence paths must be nonempty relative POSIX paths')
    parts = PurePosixPath(name)
    if parts.is_absolute() or '..' in parts.parts or ':' in name or not parts.parts:
        raise ValueError('Absolute/traversing paths are forbidden')
    root = Path(root).resolve(strict=True)
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlinks are forbidden')
    resolved = current.resolve(strict=True)
    resolved.relative_to(root)
    if not resolved.is_file():
        raise ValueError('Selected evidence must be a file')
    return resolved, parts.as_posix()


def fingerprint(path):
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
            size += len(chunk)
    return {'sha256': digest.hexdigest(), 'size': size}


def context_fields(context):
    if not isinstance(context, dict):
        raise ValueError('Context must be an object')
    if any(not isinstance(context.get(k), str) or not context[k].strip() for k in CONTEXT_KEYS):
        raise ValueError('Context requires target, environment, revision and run_id')
    return {k: context[k] for k in CONTEXT_KEYS}


def create_manifest(root, names, context):
    context = context_fields(context)
    if not names:
        raise ValueError('Select at least one evidence file')
    files = []
    seen = set()
    for name in names:
        path, canonical = safe_file(root, name)
        if canonical in seen:
            raise ValueError('Duplicate evidence path')
        seen.add(canonical)
        files.append({'path': canonical, **fingerprint(path)})
    return {'schema_version': 1, 'algorithm': 'sha256',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'context': context, 'signature_status': 'unsigned',
            'files': sorted(files, key=lambda row: row['path']),
            'limitation': 'Hashes prove listed-byte consistency only, not authorship or test execution.'}


def verify_manifest(root, manifest):
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or manifest.get('algorithm') != 'sha256':
        raise ValueError('Unsupported manifest')
    context_fields(manifest.get('context'))
    rows = manifest.get('files')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Manifest must list files')
    seen, failures = set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid file record')
        name, digest, size = row.get('path'), row.get('sha256'), row.get('size')
        if (not isinstance(digest, str) or len(digest) != 64 or
                any(c not in '0123456789abcdef' for c in digest) or
                not isinstance(size, int) or isinstance(size, bool) or size < 0):
            raise ValueError('Invalid hash/size')
        # Validate paths even when a selected file no longer exists.
        try:
            path, canonical = safe_file(root, name)
            if canonical in seen:
                raise ValueError('Duplicate evidence path')
            seen.add(canonical)
            actual = fingerprint(path)
            if actual['sha256'] != digest or actual['size'] != size:
                failures.append({'path': canonical, 'reason': 'content_changed'})
        except FileNotFoundError:
            if name in seen:
                raise ValueError('Duplicate evidence path')
            seen.add(name)
            failures.append({'path': name, 'reason': 'missing'})
    return {'valid': not failures, 'checked': len(rows), 'failures': failures,
            'signature_verified': False,
            'limitation': 'Manifest trust, signatures, completeness and test truth require independent validation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create')
    create.add_argument('--root', type=Path, required=True)
    create.add_argument('--context', type=Path, required=True)
    create.add_argument('--out', type=Path, required=True)
    create.add_argument('files', nargs='+')
    verify = sub.add_parser('verify')
    verify.add_argument('--root', type=Path, required=True)
    verify.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'create':
            if args.out.exists() or args.out.is_symlink():
                raise ValueError('Refusing to overwrite an existing manifest')
            result = create_manifest(args.root, args.files, json.loads(args.context.read_text(encoding='utf-8')))
            for row in result['files']:
                if safe_file(args.root, row['path'])[0] == args.out.resolve():
                    raise ValueError('Manifest cannot include itself')
            with args.out.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            args.out.chmod(0o600)
            print(json.dumps({'created': True, 'files': len(result['files']), 'signature_status': 'unsigned'}))
        else:
            result = verify_manifest(args.root, json.loads(args.manifest.read_text(encoding='utf-8')))
            print(json.dumps(result, ensure_ascii=False))
            parser.exit(0 if result['valid'] else 1)
    except (ValueError, OSError, TypeError, KeyError):
        parser.exit(2, 'Evidence input/path error; no integrity pass inferred.\n')


if __name__ == '__main__':
    main()
