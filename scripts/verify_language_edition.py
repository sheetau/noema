"""Verify a sealed edition using only the standard library, without the ledger."""
import argparse
import hashlib
import json
from pathlib import Path

LOCK = 'data/language-release-lock-v1.json'
REPORT = 'reports/language-release-v1.json'


def confined(root, name):
    root = Path(root).resolve()
    target = (root / name).resolve()
    if not target.is_relative_to(root) or Path(name).is_absolute():
        raise ValueError('Nonlocal release path: ' + name)
    return target


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(root, progress=None):
    root = Path(root)
    raw = (root / LOCK).read_bytes()
    lock = json.loads(raw)
    report = json.loads((root / REPORT).read_text(encoding='utf-8'))
    if report['artifact_lock_sha256'] != digest(raw) or report['status'] != 'complete_under_stated_scope':
        raise ValueError('Edition seal differs')
    if report['files'] != len(lock['files']):
        raise ValueError('Edition inventory differs')
    total = len(lock['files'])
    for i, (name, expected) in enumerate(lock['files'].items()):
        if progress and i % 256 == 0:
            progress(i, total)
        if digest(confined(root, name).read_bytes()) != expected:
            raise ValueError('Changed release artifact: ' + name)
    if progress:
        progress(total, total)
    return dict(edition=lock['edition'],files=total,unchanged=True,
                semantic_judgments='retained, not rerun')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', default='.')
    args = p.parse_args()
    def progress(done,total):
        print(json.dumps(dict(stage='content verification',completed=done,total=total)),flush=True)
    print(json.dumps(verify(args.root,progress),ensure_ascii=False))


if __name__ == '__main__':
    main()
