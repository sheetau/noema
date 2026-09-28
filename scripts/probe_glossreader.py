"""Compare pretrained context/gloss alignment to the current shared MiniLM head."""
import argparse
import json
from pathlib import Path
import time

import torch
from safetensors.torch import load_file, save_file

from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.glossreader import FrozenGlossReader
from noema.lexical_frames import SharedConceptMatcher
from noema.semantics import require
from noema.shared_matcher import predict, query_features
from scripts.prepare_reference_corpus import write
from scripts.probe_target_ablation import evaluate
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/glossreader-v1')
RAW = Path('artifacts/glossreader-v1')
FIXTURES = {f'v{n}': f'data/definition-probe-v{n}.json' for n in range(1, 7)}
FIXTURES['target-switch'] = 'data/target-switch-v1.json'
CODE = ['noema/glossreader.py', 'noema/encoder.py', 'noema/definition_probe.py', 'noema/lexical_frames.py',
        'noema/shared_matcher.py', 'noema/bem_probe.py', 'noema/target_ablation.py', 'noema/semantics.py',
        'noema/glossary.py', 'noema/language.py', 'scripts/probe_glossreader.py', 'scripts/probe_target_ablation.py',
        'scripts/probe_pretrained_reranker.py', 'scripts/train_mention_scope.py', 'scripts/prepare_reference_corpus.py',
        'docs/glossreader-v1-protocol.md', 'reports/glossreader-source-v1/manifest.json',
        'reports/shared-matcher-v1/run.json', 'reports/shared-matcher-v1/linear-training.json',
        'reports/shared-matcher-v1/definitions.json', 'artifacts/shared-matcher-v1/linear.safetensors',
        'reports/target-ablation-v1/run.json', 'reports/target-ablation-v1/target-switch-evaluation.json']
CODE += list(FIXTURES.values()) + [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]


def forward_check(model, rows, glosses):
    q, audit = model.encode_contexts(rows)
    g = model.encode_glosses(glosses)
    repeated, repeated_audit = model.encode_contexts(rows)
    require(torch.equal(q, repeated) and audit == repeated_audit and torch.equal(g, model.encode_glosses(glosses)),
            'GlossReader repeated features differ')
    texts = list(dict.fromkeys(r['text'] for r in rows))
    encoded = model.tokenizer(texts, padding=True, truncation=False, return_tensors='pt')
    with torch.inference_mode():
        direct = model.encoders['context'](**encoded).last_hidden_state
        direct_gloss = model.encoders['gloss'](**model.tokenizer(glosses, padding=True, truncation=False, return_tensors='pt')).last_hidden_state[:, 0]
    for i, row in enumerate(rows):
        require(torch.equal(q[i], direct[texts.index(row['text']), audit[i]['positions']].mean(0)), 'Context pooling differs')
    require(torch.equal(g, direct_gloss), 'Gloss CLS differs')
    require(all(not any(p.requires_grad for p in encoder.parameters()) and not any(m.training for m in encoder.modules())
                for encoder in model.encoders.values()), 'GlossReader is not frozen in eval mode')
    return {'context': q, 'gloss': g}, {'targets': len(rows), 'glosses': len(glosses), 'repeat_exact': True,
                                      'direct_forward_exact': True, 'frozen_eval': True}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in CODE}, 'score': 'unnormalized context dot English gloss CLS',
                'fitted_parameters': 0, 'confirmed_translations': 0}
    prior = json.loads(Path('reports/target-ablation-v1/run.json').read_text(encoding='utf-8'))
    prior_report = 'reports/target-ablation-v1/target-switch-evaluation.json'
    require(digest(prior_report) == prior['outputs_sha256'][prior_report], 'Prior target-switch evidence changed')
    bank = sorted(definitions(), key=lambda d: d['id'])
    ids = [d['id'] for d in bank]
    fixtures = {key: rows_from_fixture(json.loads(Path(path).read_text(encoding='utf-8')), set(ids))
                for key, path in FIXTURES.items()}
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'GlossReader probe sources changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'GlossReader probe artifact changed')
        features = load_file(str(RAW / 'features.safetensors'))
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        RAW.mkdir(parents=True, exist_ok=False)
        write(ROOT / 'protocol.json', contract)
        write(ROOT / 'definitions.json', bank)
        features = {}
    with forbidden_paths() as guards:
        model = FrozenGlossReader()
        probe, check = forward_check(model, fixtures['target-switch'][:6], [d['en'] for d in bank[:4]])
        if args.verify_only:
            require(model.metadata == run['model'], 'GlossReader model or environment changed')
            saved = load_file(str(RAW / 'probe.safetensors'))
            require(all(torch.equal(v, saved[k]) for k, v in probe.items()), 'Fresh GlossReader probe differs')
        else:
            save_file(probe, str(RAW / 'probe.safetensors'))
            print('GlossReader two encoders loaded; direct and repeated forward passed', flush=True)
            features['glosses'] = model.encode_glosses([d['en'] for d in bank])
        mini = SharedConceptMatcher()
        require(ids == mini.index.ids, 'Comparison candidate inventories differ')
        if not args.verify_only:
            features['minilm_glosses'] = mini.index.vectors
            save_file(mini.head.state_dict(), str(RAW / 'minilm-head.safetensors'))
        else:
            require(torch.equal(mini.index.vectors, features['minilm_glosses']), 'MiniLM candidate features changed')
        audits, counts, timings = {}, {}, {}
        for key, rows in fixtures.items():
            started = time.monotonic()
            if not args.verify_only:
                features[key], audits[key] = model.encode_contexts(rows)
                features[key + '-minilm'] = query_features(mini.encoder, rows)
                timings[key] = time.monotonic() - started
            with torch.inference_mode():
                matrices = {'glossreader': features[key] @ features['glosses'].T,
                            'minilm': mini.head(features[key + '-minilm'], features['minilm_glosses'])}
            results = {}
            for method, matrix in matrices.items():
                predictions, results[method] = evaluate(matrix, rows, ids)
                if args.verify_only:
                    require(predictions == json.loads((RAW / f'{key}-{method}.json').read_text(encoding='utf-8')),
                            'GlossReader probe score replay differs')
                else:
                    write(RAW / f'{key}-{method}.json', predictions)
            if args.verify_only:
                require(results == json.loads((ROOT / f'{key}-evaluation.json').read_text(encoding='utf-8')),
                        'GlossReader evaluation replay differs')
            else:
                write(ROOT / f'{key}-evaluation.json', results)
                print(key, {m: {lang: r['metrics'][lang]['supported']['correct'] for lang in ('ja', 'en')}
                            for m, r in results.items()}, flush=True)
            counts[key] = len(rows)
        require(all(g.call_count == 0 for g in guards), 'Forbidden inference path used')
        check['forbidden_calls'] = [g.call_count for g in guards]
    if args.verify_only:
        write(ROOT / 'verification.json', {'fresh_probe_features_exact': True, 'rows_replayed_per_method': counts,
                                          'scores_predictions_metrics_exact': True, 'forward_check': check, **contract})
        print('GlossReader verification passed', flush=True)
    else:
        save_file(features, str(RAW / 'features.safetensors'))
        write(ROOT / 'alignment.json', {key: [{'id': row['id'], **a} for row, a in zip(fixtures[key], values, strict=True)]
                                        for key, values in audits.items()})
        paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
        write(ROOT / 'run.json', {**contract, 'model': model.metadata, 'baseline': mini.metadata,
              'forward_check': check, 'context_and_baseline_feature_seconds': timings,
              'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
