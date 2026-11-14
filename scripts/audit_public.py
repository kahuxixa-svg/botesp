"""Audit Git's index without printing any possible secret values."""
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_PARTS = {'.local', '.tools', '.venv', '__pycache__', 'managed_components', 'build'}
PRIVATE_SUFFIXES = {'.bin', '.log', '.pem', '.key', '.pfx', '.p12', '.pyc'}
PATTERNS = {
    'JWT credential': re.compile(rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
    'GitHub credential': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'private key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'AWS credential': re.compile(rb'AKIA[0-9A-Z]{16}'),
}


def main():
    result = subprocess.run(['git', 'ls-files', '--stage', '-z'], cwd=ROOT,
                            check=True, capture_output=True)
    failures = []
    count = 0
    candidates = []
    for record in result.stdout.split(b'\0'):
        if not record:
            continue
        metadata, encoded_path = record.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        name = encoded_path.decode('utf-8')
        path = PurePosixPath(name)
        count += 1
        if (mode == b'160000' or stage != b'0' or
                PRIVATE_PARTS.intersection(path.parts) or
                path.suffix.lower() in PRIVATE_SUFFIXES or name == 'hardware.json' or
                (path.name.startswith('.env') and path.name != '.env.example') or
                path.name in {'sdkconfig', 'sdkconfig.old'}):
            failures.append(f'{name}: private/generated path or embedded Git repository')
            continue
        candidates.append((name, oid))
    # Batch-read exactly the blobs Git would publish, including staged edits.
    request = b''.join(oid + b'\n' for _, oid in candidates)
    blobs = subprocess.run(['git', 'cat-file', '--batch'], input=request, cwd=ROOT,
                           check=True, capture_output=True).stdout
    offset = 0
    for name, oid in candidates:
        header_end = blobs.index(b'\n', offset)
        actual_oid, kind, size = blobs[offset:header_end].split()
        if actual_oid != oid or kind != b'blob':
            raise ValueError('Unexpected Git object in public index')
        offset = header_end + 1
        data = blobs[offset:offset + int(size)]
        offset += int(size) + 1
        if len(data) > 50 * 1024 * 1024:
            failures.append(f'{name}: file exceeds project size limit')
        if b'\0' not in data[:8192]:
            for label, pattern in PATTERNS.items():
                if pattern.search(data):
                    failures.append(f'{name}: possible {label}; value withheld')
    if not count:
        failures.append('No indexed files: stage the intended public files first')
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(f'PASS: {count} indexed files; no excluded paths, gitlinks or detected credentials')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
