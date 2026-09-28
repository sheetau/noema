"""Test whether removing the requested span makes relevance ranking target-specific."""
import argparse
import json
from pathlib import Path
import time

import torch
from safetensors.torch import load_file, save_file

from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.pretrained_reranker import FrozenReranker, concept_scores, raw_pairs
from noema.semantics import require
from noema.shared_matcher import predict
from noema.target_ablation import masked_pairs, masked_scores, target_effect, target_switch_metrics
from scripts.prepare_reference_corpus import write
from scripts.probe_pretrained_reranker import check_forward, report
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/target-ablation-v1')
RAW = Path('artifacts/target-ablation-v1')
PRIOR = Path('reports/pretrained-reranker-v1/run.json')
FIXTURES = {'v6': 'data/definition-probe-v6.json', 'target-switch': 'data/target-switch-v1.json'}
AUDITED = sorted(p for p in Path('data').rglob('*.json') if str(p).replace('\\', '/') != FIXTURES['target-switch'])
CODE = ['noema/target_ablation.py', 'noema/pretrained_reranker.py', 'noema/encoder.py', 'noema/definition_probe.py',
        'noema/shared_matcher.py', 'noema/bem_probe.py', 'noema/semantics.py', 'noema/glossary.py', 'noema/language.py',
        'scripts/probe_target_ablation.py', 'scripts/probe_pretrained_reranker.py', 'scripts/prepare_reference_corpus.py',
        'scripts/train_mention_scope.py', 'docs/target-ablation-v1-protocol.md', str(PRIOR)]
CODE += list(FIXTURES.values()) + [str(p).replace('\\', '/') for p in AUDITED]
CODE += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def novelty(rows):
    texts = {r['text'] for r in rows}
    matches = []
    for path in AUDITED:
        overlap = texts & set(strings(json.loads(path.read_text(encoding='utf-8'))))
        matches.extend({'path': str(path).replace('\\', '/'), 'text': text} for text in sorted(overlap))
    require(not matches, 'New target-switch context already present in data JSON')
    return {'files': len(AUDITED), 'new_contexts': len(texts), 'targets': len(rows),
            'known_targets': sum(r['expected'] is not None for r in rows), 'matches': matches,
            'scope': 'exact strings in existing data/**/*.json; pretrained model corpus overlap is unknown'}


def evaluate(matrix, rows, ids):
    predictions = predict(matrix, rows, ids)
    return predictions, {**report(predictions), 'target_switch': target_switch_metrics(predictions)}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in CODE}, 'effect': 'full_logit - masked_logit',
                'fitted_parameters': 0, 'confirmed_translations': 0, 'batch_size': 16}
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    for path, sha in {**prior['source_sha256'], **prior['outputs_sha256']}.items():
        require(digest(path) == sha, 'Prior reranker dependency or evidence changed')
    bank = sorted(definitions(), key=lambda d: d['id'])
    ids = [d['id'] for d in bank]
    fixtures = {key: rows_from_fixture(json.loads(Path(path).read_text(encoding='utf-8')), set(ids))
                for key, path in FIXTURES.items()}
    audit_novelty = novelty(fixtures['target-switch'])
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Target ablation sources changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'Target ablation artifact changed')
        require(audit_novelty == json.loads((ROOT / 'novelty.json').read_text(encoding='utf-8')), 'Novelty audit changed')
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        RAW.mkdir(parents=True, exist_ok=False)
        write(ROOT / 'protocol.json', contract)
        write(ROOT / 'novelty.json', audit_novelty)
    with forbidden_paths() as guards:
        reranker = FrozenReranker()
        require(reranker.metadata == prior['model'], 'Frozen reranker model or environment changed')
        small = fixtures['target-switch'][:2]
        probe = raw_pairs(small, bank[:1], 'sentence')[0] + masked_pairs(small, bank[:1], reranker.tokenizer.mask_token)[0]
        probe_values, check = check_forward(reranker, probe)
        if args.verify_only:
            require(torch.equal(probe_values, load_file(str(RAW / 'probe.safetensors'))['scores']), 'Fresh masked probe differs')
        else:
            save_file({'scores': probe_values}, str(RAW / 'probe.safetensors'))
            print('target ablation model loaded; raw/masked direct and repeat checks passed', flush=True)
        counts, audits = {}, {}
        for fixture, rows in fixtures.items():
            matrices, audits[fixture] = {}, {}
            for mode in ('isolated', 'sentence', 'masked'):
                if fixture == 'v6' and mode != 'masked':
                    path = Path(f'artifacts/pretrained-reranker-v1/{mode}.safetensors')
                    matrices[mode] = load_file(str(path))['scores']
                    audits[fixture][mode] = {'cached': str(path).replace('\\', '/')}
                elif args.verify_only:
                    matrices[mode] = load_file(str(RAW / f'{fixture}-{mode}.safetensors'))['scores']
                else:
                    started = time.monotonic()
                    def progress(done, total):
                        if done % 256 == 0 or done == total:
                            print(fixture, mode, done, '/', total, 'seconds', round(time.monotonic() - started, 1), flush=True)
                    if mode == 'masked':
                        matrices[mode], audit = masked_scores(reranker, rows, bank, progress=progress)
                    else:
                        matrices[mode], audit = concept_scores(reranker, rows, bank, mode, progress=progress)
                    audits[fixture][mode] = {**audit, 'seconds': time.monotonic() - started}
                    save_file({'scores': matrices[mode]}, str(RAW / f'{fixture}-{mode}.safetensors'))
            matrices['effect'] = target_effect(matrices['sentence'], matrices['masked'])
            scores = {}
            for mode in ('isolated', 'sentence', 'effect'):
                predictions, scores[mode] = evaluate(matrices[mode], rows, ids)
                if args.verify_only:
                    require(predictions == json.loads((RAW / f'{fixture}-{mode}.json').read_text(encoding='utf-8')),
                            'Ablation prediction replay differs')
                else:
                    write(RAW / f'{fixture}-{mode}.json', predictions)
            if args.verify_only:
                require(scores == json.loads((ROOT / f'{fixture}-evaluation.json').read_text(encoding='utf-8')),
                        'Ablation evaluation replay differs')
            else:
                write(ROOT / f'{fixture}-evaluation.json', scores)
                print(fixture, {m: {lang: s['metrics'][lang]['supported']['correct'] for lang in ('ja', 'en')}
                                 for m, s in scores.items()}, flush=True)
            counts[fixture] = len(rows)
        require(all(g.call_count == 0 for g in guards), 'Forbidden inference path used')
        check['forbidden_calls'] = [g.call_count for g in guards]
    if args.verify_only:
        write(ROOT / 'verification.json', {'fresh_masked_probe_exact': True, 'rows_replayed_per_method': counts,
                                          'effect_predictions_metrics_exact': True, 'forward_check': check, **contract})
        print('target ablation verification passed', flush=True)
    else:
        paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
        write(ROOT / 'run.json', {**contract, 'model': reranker.metadata, 'forward_check': check, 'audit': audits,
              'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
