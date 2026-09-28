"""Replay fixed GlossReader features under four prespecified geometry controls."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.bem_probe import summarize
from noema.definition_probe import digest, rows_from_fixture
from noema.encoder import deterministic
from noema.gloss_geometry import METHODS, geometry_scores, geometry_summary
from noema.semantics import require
from scripts.prepare_reference_corpus import write
from scripts.probe_target_ablation import evaluate

ROOT = Path('reports/gloss-geometry-v1')
RAW = Path('artifacts/gloss-geometry-v1')
PRIOR = Path('reports/glossreader-v1/run.json')
FEATURES = 'artifacts/glossreader-v1/features.safetensors'
FIXTURES = {f'v{n}': f'data/definition-probe-v{n}.json' for n in range(1, 7)}
FIXTURES['target-switch'] = 'data/target-switch-v1.json'
CODE = ['noema/gloss_geometry.py', 'scripts/probe_gloss_geometry.py', 'docs/gloss-geometry-v1-protocol.md',
        'noema/definition_probe.py', 'noema/shared_matcher.py', 'noema/bem_probe.py', 'noema/target_ablation.py',
        'noema/encoder.py', 'noema/semantics.py', 'scripts/probe_target_ablation.py',
        'scripts/probe_pretrained_reranker.py', 'scripts/prepare_reference_corpus.py',
        'reports/glossreader-v1/run.json', 'reports/glossreader-v1/verification.json']


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    deterministic()
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    # Validate both the annotations and the saved feature ordering contract.
    for path in FIXTURES.values():
        require(digest(path) == prior['source_sha256'][path], 'Prior fixture changed')
    source_files = [FEATURES, 'reports/glossreader-v1/definitions.json']
    source_files += [f'artifacts/glossreader-v1/{key}-glossreader.json' for key in FIXTURES]
    for path in source_files:
        require(digest(path) == prior['outputs_sha256'][path], 'Prior feature or prediction artifact changed')
    contract = {'source_sha256': {p: digest(p) for p in [*CODE, *FIXTURES.values(), *source_files]},
                'methods': list(METHODS), 'fitted_parameters': 0, 'confirmed_translations': 0,
                'fresh_encoder_forward': False, 'torch': str(torch.__version__),
                'threads': torch.get_num_threads(), 'seed': 17}
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Geometry contract changed')
        for p, sha in run['outputs_sha256'].items():
            require(digest(p) == sha, 'Geometry output changed')
        saved_scores = load_file(str(RAW / 'scores.safetensors'))
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        RAW.mkdir(parents=True, exist_ok=False)
        write(ROOT / 'protocol.json', contract)
    bank = json.loads(Path(source_files[1]).read_text(encoding='utf-8'))
    ids = [d['id'] for d in bank]
    features = load_file(FEATURES)
    combined = {method: [] for method in METHODS}
    all_scores, summary, negative_control = {}, {}, {}
    for key, path in FIXTURES.items():
        rows = rows_from_fixture(json.loads(Path(path).read_text(encoding='utf-8')), set(ids))
        previous = json.loads(Path(f'artifacts/glossreader-v1/{key}-glossreader.json').read_text(encoding='utf-8'))
        require(rows == [{k: v for k, v in row.items() if k != 'top'} for row in previous], 'Feature row order changed')
        scores = geometry_scores(features[key], features['glosses'])
        results, predictions = {}, {}
        for method, matrix in scores.items():
            name = key + '-' + method
            predictions[method], results[method] = evaluate(matrix, rows, ids)
            if method == 'dot':
                require(predictions[method] == previous, 'Raw dot failed to reproduce prior evidence')
            combined[method].extend([{**r, 'id': key + ':' + r['id'], 'pair': key + ':' + r['pair']}
                                     for r in predictions[method]])
            all_scores[name] = matrix
            target = RAW / (name + '.json')
            if args.verify_only:
                require(torch.equal(matrix, saved_scores[name]), 'Geometry score replay differs')
                require(predictions[method] == json.loads(target.read_text(encoding='utf-8')), 'Geometry prediction differs')
            else:
                write(target, predictions[method])
        negative_control[key] = {'top1_changes': sum(a['top'][0]['concept'] != b['top'][0]['concept']
                                                    for a, b in zip(predictions['dot'], predictions['centered_dot'], strict=True)),
                                 'max_subtraction_error': (scores['centered_dot'] - scores['dot']
                                     + (features[key] @ features['glosses'].mean(0))[:, None]).abs().max().item()}
        summary[key] = {'evaluation': results, 'geometry': geometry_summary(features[key], features['glosses'])}
        print(key, {m: {l: r['metrics'][l]['supported']['correct'] for l in ('ja', 'en')} for m, r in results.items()}, flush=True)
    report = {'fixtures': summary, 'overall': {m: summarize(rows) for m, rows in combined.items()},
              'centered_dot_control': negative_control, 'rows_per_method': len(combined['dot'])}
    if args.verify_only:
        require(report == json.loads((ROOT / 'evaluation.json').read_text(encoding='utf-8')), 'Geometry metrics differ')
        write(ROOT / 'verification.json', {**contract, 'scores_predictions_metrics_exact': True,
                                          'rows_per_method': len(combined['dot']), 'prior_raw_predictions_exact': True})
        print('Geometry verification passed', flush=True)
    else:
        save_file(all_scores, str(RAW / 'scores.safetensors'))
        write(ROOT / 'evaluation.json', report)
        paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
        write(ROOT / 'run.json', {**contract, 'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
