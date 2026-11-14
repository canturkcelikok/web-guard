#!/usr/bin/env python3
"""One bounded HTTP observation. Does not scan, crawl or follow redirects."""
import argparse
from datetime import datetime, timezone
import http.client
import ipaddress
import json
from pathlib import Path
import socket
import ssl
from urllib.parse import urlsplit, urlunsplit

HEADERS = {'content-type', 'content-security-policy', 'content-security-policy-report-only',
           'strict-transport-security', 'x-content-type-options', 'x-frame-options',
           'referrer-policy', 'permissions-policy', 'cache-control', 'access-control-allow-origin',
           'access-control-allow-credentials', 'vary', 'retry-after'}


def target_parts(url):
    u = urlsplit(url)
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password:
        raise ValueError('Use an http(s) URL without credentials')
    if u.query or u.fragment:
        raise ValueError('Use a URL without query/fragment to avoid credential leakage')
    if u.port not in (None, 80, 443):
        raise ValueError('This minimal helper accepts only standard web ports')
    return u


def observe(url, allow_private=False):
    u = target_parts(url)
    host = u.hostname.encode('idna').decode('ascii')
    port = u.port or (443 if u.scheme == 'https' else 80)
    addresses = sorted({row[4][0] for row in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)})
    if not addresses or (not allow_private and any(not ipaddress.ip_address(a).is_global for a in addresses)):
        raise ValueError('Nonpublic destination requires --allow-private and an authorized private scope')
    # Pin the validated address; TLS still verifies the original hostname.
    address = addresses[0]
    connection_cls = http.client.HTTPSConnection if u.scheme == 'https' else http.client.HTTPConnection
    kwargs = {'timeout': 8}
    if u.scheme == 'https':
        kwargs['context'] = ssl.create_default_context()
    connection = connection_cls(host, port, **kwargs)
    def pinned_connect(addr, timeout=8, source_address=None):
        return socket.create_connection((address, port), timeout, source_address)
    connection._create_connection = pinned_connect
    result = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'target': urlunsplit((u.scheme, u.netloc, u.path or '/', '', '')),
              'kind': 'http_observation_only', 'requests': 1, 'redirects_followed': 0,
              'limits': 'One GET, no body read, no credentials, no exploit tests',
              'warnings': []}
    try:
        connection.request('GET', u.path or '/', headers={'User-Agent': 'WebGuard-Observation/1.0',
                                                        'Connection': 'close'})
        response = connection.getresponse()
        result['status'] = response.status
        headers = {}
        for key, value in response.getheaders():
            key = key.lower()
            if key in HEADERS:
                headers.setdefault(key, []).append(value[:2048])
        result['headers'] = headers
        # Never retain Set-Cookie values, Location URLs or response bodies.
        if 300 <= response.status < 400:
            result['warnings'].append('Redirect not followed; authorize/observe destination separately')
        if response.status in (401, 403, 429) or response.status >= 500:
            result['warnings'].append('Blocked/error/rate-limited; application coverage unavailable')
        for name in ('content-security-policy', 'x-content-type-options'):
            if name not in headers:
                result['warnings'].append('Contextual review needed: header absent: ' + name)
        if u.scheme == 'http':
            result['warnings'].append('Plain HTTP observed; HTTPS/redirect needs separate verification')
        elif 'strict-transport-security' not in headers:
            result['warnings'].append('Contextual review needed: HSTS absent')
    finally:
        connection.close()
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('url')
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--authorized', action='store_true', help='Assert the target is explicitly authorized')
    p.add_argument('--allow-private', action='store_true', help='Only for explicitly scoped private targets')
    args = p.parse_args()
    if not args.authorized:
        p.error('Confirm target authorization first; then pass --authorized')
    if args.out.exists():
        p.error('Output exists; use a new evidence filename')
    try:
        result = observe(args.url, args.allow_private)
        with args.out.open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')
        args.out.chmod(0o600)
        print(json.dumps({'status': result['status'], 'requests': 1,
                          'warnings': len(result['warnings']), 'evidence': str(args.out)}))
    except (ValueError, OSError, http.client.HTTPException) as exc:
        # Avoid echoing arbitrary network exception strings that may include secrets.
        p.exit(2, 'Observation failed (' + type(exc).__name__ + '); no security pass inferred.\n')


if __name__ == '__main__':
    main()
