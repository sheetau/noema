"""Fresh, run-isolated audit with content-checked restart checkpoints.

Does NOT claim to be the legacy --full run: originals remain unchanged.
Never consumes .noema-cache/validation.sqlite or another run's database.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from noema.validation_cache import ValidationCache, digest
from scripts.long_run import LongRun, PauseRequested, atomic_json


class ProgressCache(ValidationCache):
    def __init__(self, root, run):
        self.run = run
        super().__init__(root, path=run.directory / 'acceleration.sqlite')

    def parse(self, parser, text, namespace):
        with self.run.activity('parse:' + namespace + ':' + digest(text.encode('utf-8'))[:16]):
            return super().parse(parser, text, namespace)

    def catalog(self, loader, root, basis_path, *, document_path=None):
        with self.run.activity('catalog:' + str(basis_path)):
            return super().catalog(loader, root, basis_path, document_path=document_path)

    def symbols(self, parser, text):
        with self.run.activity('draft-document:' + digest(text.encode('utf-8'))[:16]):
            result = super().symbols(parser, text)
        if self.run.state['stage'] == 'draft_inventory':
            self.run.emit('document_complete', completed=self.run.state['completed'] + 1)
        return result


def manifest(root, index, verify):
    """Pin every expected dependency and report membership before starting."""
    cache = ValidationCache(root, enabled=False)
    expected = json.loads((root / verify).read_text(encoding='utf-8'))
    registry = json.loads((root / index).read_text(encoding='utf-8'))
    names = set(expected['source_sha256']) | set(registry['source_sha256']) | {index, verify}
    names |= {p.relative_to(root).as_posix() for p in (root / 'reports').glob('*.json')}
    runner = {p.name: digest(p.read_bytes()) for p in
              (Path(__file__), Path(__file__).with_name('long_run.py'))}
    return dict(schema=1, mode='fresh_run_isolated_checkpoints', root=str(root), index=index,
                verify=verify, python=sys.version, engine=cache.code, runner=runner,
                inputs=cache.hashes(names))


def perform(root, index, verify, run):
    from noema import review_registry
    from scripts import project_work
    # project_work.audit remains the producer. Wrapping its imported callable
    # separates high-level phases without changing its final equality/pin checks.
    cache = ProgressCache(root, run)
    registry = json.loads((root / index).read_text(encoding='utf-8'))
    total = sum(len(w['reviews']) for w in registry['works'].values())
    original_binding = review_registry.validate_binding
    original_partial = project_work.partial_report
    completed = 0

    def binding(*args, **kwargs):
        nonlocal completed
        work, active, selection = args[1:4]
        name = selection['review']
        run.emit('review_start', stage='reviews', completed=completed, total=total, review=name)
        result = run.step('review:' + work + ':' + name, selection,
                          lambda: original_binding(*args, **kwargs),
                          validate=lambda row: cache.validate_hashes(
                              review_registry.legacy.validate_hashes, root, row['source_sha256']))
        completed += 1
        run.emit('review_complete', completed=completed)
        # _load_reviews pops source_sha256; never mutate the saved value.
        return deepcopy(result)

    def partial(current_cache):
        expected = json.loads((root / verify).read_text(encoding='utf-8'))
        run.emit('stage', stage='draft_inventory', completed=0,
                 total=expected['parsed_noema_documents'])
        result = original_partial(current_cache)
        run.emit('inventory_complete', completed=result['parsed_noema_documents'],
                 total=result['parsed_noema_documents'])
        return result

    try:
        with cache.adapters():
            review_registry.validate_binding = binding
            project_work.partial_report = partial
            result = project_work.audit(cache, index)
        run.emit('stage', stage='final_comparison', completed=0, total=1)
        if result != json.loads((root / verify).read_text(encoding='utf-8')):
            raise ValueError('Stored aggregate differs')
        # Rehash the entire frozen inventory; rejects changed/new/removed inputs.
        if manifest(root, index, verify) != run.manifest:
            raise ValueError('Inputs changed during audit')
        receipt = dict(mode='fresh_run_isolated_checkpoints', legacy_full=False,
                       result_sha256=digest(json.dumps(result, ensure_ascii=False, sort_keys=True).encode('utf-8')),
                       manifest_sha256=digest(json.dumps(run.manifest, sort_keys=True).encode('utf-8')),
                       verified=verify, cache=cache.stats)
        atomic_json(run.directory / 'result.json', receipt)
        run.emit('comparison_complete', completed=1, total=1)
        return receipt
    finally:
        review_registry.validate_binding = original_binding
        project_work.partial_report = original_partial
        cache.close()


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--run-dir', type=Path, required=True)
    cli.add_argument('--index', required=True)
    cli.add_argument('--verify', required=True)
    cli.add_argument('--resume', action='store_true')
    args = cli.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    inputs = manifest(root, args.index, args.verify)
    try:
        with LongRun(args.run_dir, inputs, resume=args.resume) as run:
            perform(root, args.index, args.verify, run)
    except (PauseRequested, KeyboardInterrupt):
        return 130
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
