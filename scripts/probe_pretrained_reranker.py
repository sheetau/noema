"""Unadapted multilingual relevance classifier as a definition-matching diagnostic."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

import torch
from safetensors.torch import load_file, save_file

from noema.bem_probe import summarize
from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.pretrained_reranker import FrozenReranker, concept_scores, raw_pairs
from noema.semantics import require
from noema.shared_matcher import predict
from scripts.prepare_reference_corpus import write
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/pretrained-reranker-v1')
RAW = Path('artifacts/pretrained-reranker-v1')
BASELINE = 'artifacts/broad-matcher-v1/v6-minilm.json'
MODES = ('isolated', 'sentence')
CODE = ['noema/pretrained_reranker.py', 'noema/encoder.py', 'noema/definition_probe.py',
        'noema/bem_probe.py', 'noema/shared_matcher.py', 'noema/semantics.py', 'noema/glossary.py',
        'noema/language.py', 'scripts/probe_pretrained_reranker.py', 'scripts/train_mention_scope.py',
        'scripts/prepare_reference_corpus.py', 'docs/pretrained-reranker-v1-protocol.md',
        'data/definition-probe-v6.json', 'reports/broad-matcher-v1/run.json', BASELINE]
CODE += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]


def report(predictions):
    return {'metrics': summarize(predictions),
            'top_candidates': Counter(p['top'][0]['concept'] for p in predictions)}


def check_forward(reranker, pairs):
    first = reranker.score(pairs)
    second = reranker.score(pairs)
    encoded = reranker.tokenizer([p[0] for p in pairs], [p[1] for p in pairs], padding=True,
                                 truncation=False, return_tensors='pt')
    with torch.inference_mode():
        direct = reranker.model(**encoded).logits[:, 0]
    require(torch.equal(first, second) and torch.equal(first, direct), 'Reranker repeat or wrapper differs')
    require(not any(p.requires_grad for p in reranker.model.parameters())
            and not any(m.training for m in reranker.model.modules()), 'Reranker is not frozen in eval mode')
    return first, {'pairs': len(pairs), 'repeat_exact': True, 'direct_forward_exact': True, 'frozen_eval': True}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in CODE}, 'modes': list(MODES), 'fitted_parameters': 0,
                'confirmed_translations': 0, 'inference_batch_size': 16}
    previous = json.loads(Path('reports/broad-matcher-v1/run.json').read_text(encoding='utf-8'))
    require(digest(BASELINE) == previous['outputs_sha256'][BASELINE], 'Baseline prediction hash changed')
    bank = sorted(definitions(), key=lambda d: d['id'])
    ids = [d['id'] for d in bank]
    rows = rows_from_fixture(json.loads(Path('data/definition-probe-v6.json').read_text(encoding='utf-8')), set(ids))
    baseline = json.loads(Path(BASELINE).read_text(encoding='utf-8'))
    require(len(rows) == len(baseline) and all(all(old.get(k) == v for k, v in row.items())
            for row, old in zip(rows, baseline, strict=True)), 'Baseline rows changed')
    repeated = defaultdict(list)
    for row in rows:
        repeated[row['language'], row['span']].append(row)
    collisions = [{'language': language, 'span': span, 'row_ids': [r['id'] for r in group],
                   'expected': [r['expected'] for r in group]}
                  for (language, span), group in repeated.items() if len({r['expected'] for r in group}) > 1]
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Reranker dependency changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'Reranker artifact changed')
        require(bank == json.loads((ROOT / 'definitions.json').read_text(encoding='utf-8')), 'Definitions changed')
        require(collisions == json.loads((ROOT / 'isolated-collisions.json').read_text(encoding='utf-8')), 'Collision audit changed')
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        RAW.mkdir(parents=True, exist_ok=False)
        write(ROOT / 'protocol.json', contract)
        write(ROOT / 'definitions.json', bank)
        write(ROOT / 'isolated-collisions.json', collisions)
        write(ROOT / 'baseline-evaluation.json', report(baseline))
    with forbidden_paths() as guards:
        reranker = FrozenReranker()
        # Include both languages and both query modes, without selecting by gold labels.
        probe = [raw_pairs([rows[i]], bank[:2], mode)[0][j]
                 for i, j, mode in ((0, 0, 'isolated'), (1, 1, 'isolated'), (0, 1, 'sentence'), (1, 0, 'sentence'))]
        probe_values, check = check_forward(reranker, probe)
        if args.verify_only:
            require(reranker.metadata == run['model'], 'Reranker environment or model changed')
            require(torch.equal(probe_values, load_file(str(RAW / 'probe.safetensors'))['scores']), 'Fresh probe differs')
        else:
            save_file({'scores': probe_values}, str(RAW / 'probe.safetensors'))
            print('reranker loaded; repeated and direct forward exact', flush=True)
        evaluation, audit = {}, {}
        for mode in MODES:
            if args.verify_only:
                matrix = load_file(str(RAW / f'{mode}.safetensors'))['scores']
            else:
                start = time.monotonic()
                def progress(done, total):
                    if done % 256 == 0 or done == total:
                        print(mode, done, '/', total, 'seconds', round(time.monotonic() - start, 1), flush=True)
                matrix, audit[mode] = concept_scores(reranker, rows, bank, mode, progress=progress)
                audit[mode]['seconds'] = time.monotonic() - start
                save_file({'scores': matrix}, str(RAW / f'{mode}.safetensors'))
            predictions = predict(matrix, rows, ids)
            evaluation[mode] = report(predictions)
            if args.verify_only:
                require(predictions == json.loads((RAW / f'{mode}-predictions.json').read_text(encoding='utf-8')),
                        'Reranker score replay differs')
            else:
                write(RAW / f'{mode}-predictions.json', predictions)
                write(ROOT / f'{mode}-evaluation.json', evaluation[mode])
                print(mode, {lang: evaluation[mode]['metrics'][lang]['supported'] for lang in ('ja', 'en')}, flush=True)
        require(all(g.call_count == 0 for g in guards), 'Forbidden inference path used')
        check['forbidden_calls'] = [g.call_count for g in guards]
    if args.verify_only:
        for mode in MODES:
            require(evaluation[mode] == json.loads((ROOT / f'{mode}-evaluation.json').read_text(encoding='utf-8')),
                    'Reranker metrics replay differs')
        require(report(baseline) == json.loads((ROOT / 'baseline-evaluation.json').read_text(encoding='utf-8')),
                'Baseline metrics changed')
        write(ROOT / 'verification.json', {'fresh_probe_exact': True, 'cached_matrix_rows_per_mode': len(rows),
                                          'predictions_metrics_exact': True, 'forward_check': check, **contract})
        print('reranker verification passed', flush=True)
    else:
        paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
        write(ROOT / 'run.json', {**contract, 'model': reranker.metadata, 'forward_check': check, 'audit': audit,
              'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
