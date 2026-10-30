"""Read-only, nonblocking py-spy snapshot of a running legacy audit.

Requires py-spy with support for the target Python version. Does not inject code.
An observed review ordinal is not a whole-audit percentage or an ETA.
"""
import argparse
import json
from pathlib import Path
import subprocess


def summarize(snapshot, registry):
    order = [(work, row['review']) for work, active in registry['works'].items()
             for row in active['reviews']]
    for thread in snapshot:
        for frame in thread.get('frames', []):
            if frame['name'] != 'validate_binding' or not frame['filename'].replace('\\', '/').endswith('/noema/review_registry.py'):
                continue
            values = {v['name']: v['repr'] for v in frame.get('locals', [])}
            try:
                current = (json.loads(values['work']), json.loads(values['name']))
                completed = order.index(current)
            except (KeyError, ValueError):
                continue
            return dict(stage='review_provenance', completed=completed, total=len(order),
                        current_review=current[1], phase_percent=round(completed * 100 / len(order), 1),
                        whole_audit_percent=None, remaining_seconds=None,
                        observation='Nonblocking sample; later draft audit and final checks remain.')
    return dict(stage='unknown_from_this_sample', whole_audit_percent=None, remaining_seconds=None)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--pid', type=int, required=True)
    cli.add_argument('--py-spy', type=Path, required=True)
    cli.add_argument('--index', type=Path, required=True)
    cli.add_argument('--snapshot', type=Path, required=True)
    args = cli.parse_args(argv)
    if args.snapshot.exists():
        raise ValueError('Choose a new snapshot path')
    raw = subprocess.check_output([str(args.py_spy), 'dump', '--pid', str(args.pid),
                                   '--nonblocking', '--json', '--locals'], encoding='utf-8')
    snapshot = json.loads(raw)
    with args.snapshot.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(raw)
    print(json.dumps(summarize(snapshot, json.loads(args.index.read_text(encoding='utf-8'))),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    raise SystemExit(main())
