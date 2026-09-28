"""Controlled group-ranking comparison using cached frozen features and genuine annotations."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.contrastive_verifier import partition, group_objective, ranking_metrics
from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.encoder import deterministic
from noema.semantics import require
from noema.verification_matcher import VerificationHead, binary_metrics
from scripts.prepare_reference_corpus import write
from scripts.probe_wic_verifier import scores, noema_report

ROOT = Path('reports/contrastive-verifier-v1')
RAW = Path('artifacts/contrastive-verifier-v1')
SOURCE = Path('artifacts/wic-tsv-source-v1')
PRIOR = Path('artifacts/wic-verifier-v1')
CONFIGS = [('linear-binary', 0, 0.), ('linear-ranking', 0, 1.), ('mlp-binary', 64, 0.), ('mlp-ranking', 64, 1.)]
SETTINGS = {'seed': 17, 'epochs': 20, 'batch_groups': 32, 'learning_rate': .002, 'weight_decay': .001,
            'threshold': 0, 'selection': 'internal development group-mean pair accuracy, then binary balanced accuracy'}
CODE = ['noema/contrastive_verifier.py', 'noema/verification_matcher.py', 'noema/definition_probe.py', 'noema/encoder.py',
        'noema/bem_probe.py', 'noema/shared_matcher.py', 'noema/semantics.py', 'noema/glossary.py', 'noema/language.py',
        'scripts/probe_contrastive_verifier.py', 'scripts/probe_wic_verifier.py', 'scripts/prepare_reference_corpus.py',
        'docs/contrastive-verifier-v1-protocol.md', 'reports/wic-tsv-source-v1/manifest.json', 'reports/wic-verifier-v1/run.json']
CODE += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]
CODE += [f'data/definition-probe-v{n}.json' for n in range(1, 7)]


def assess(head, features, rows, split):
    logits = scores(head, features).tolist()
    indices = split['indices']
    return {'ranking': ranking_metrics(logits, split['groups']),
            'binary': binary_metrics([logits[i] for i in indices], [rows[i]['matches'] for i in indices])}


def selection_key(value):
    return value['ranking']['group_mean_pair_accuracy'], value['binary']['balanced_accuracy']


def fit(features, rows, selection, hidden, rank_weight):
    deterministic()
    head = VerificationHead(features.shape[-1], hidden)
    labels = torch.tensor([r['matches'] for r in rows], dtype=torch.float32)
    train, dev = selection['splits']['train'], selection['splits']['dev']
    groups = train['groups']
    optimizer = torch.optim.AdamW(head.parameters(), lr=.002, weight_decay=.001)
    history = [{'epoch': 0, 'binary_loss': None, 'ranking_loss': None, 'dev': assess(head, features, rows, dev)}]
    best_key, best_epoch = selection_key(history[0]['dev']), 0
    best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    generator = torch.Generator().manual_seed(17)
    for epoch in range(1, 21):
        order = torch.randperm(len(groups), generator=generator).tolist()
        binary_total, ranking_total = 0., 0.
        head.train()
        for offset in range(0, len(order), 32):
            chosen = [groups[i] for i in order[offset:offset + 32]]
            indices = [i for group in chosen for i in group['indices']]
            local = {global_index: j for j, global_index in enumerate(indices)}
            remapped = [{name: [local[i] for i in group[name]] for name in ('indices', 'positive', 'negative')} for group in chosen]
            logits = head(features[indices])
            loss, binary, ranking = group_objective(logits, labels[indices], remapped, rank_weight,
                                                    len(groups), train['comparison_groups'])
            require(bool(torch.isfinite(loss)), 'Non-finite contrastive loss')
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            binary_total += binary.item() * len(chosen)
            ranking_total += ranking.item() * len(chosen)
        head.eval()
        value = assess(head, features, rows, dev)
        history.append({'epoch': epoch, 'binary_loss': binary_total / len(groups), 'ranking_loss': ranking_total / len(groups), 'dev': value})
        key = selection_key(value)
        if key > best_key:
            best_key, best_epoch = key, epoch
            best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best, strict=True)
    head.eval().requires_grad_(False)
    return head, {'selected_epoch': best_epoch, 'selected_dev': history[best_epoch]['dev'], 'history': history,
                  'parameters': sum(p.numel() for p in head.parameters())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in CODE}, 'settings': SETTINGS, 'configs': [list(c) for c in CONFIGS]}
    prior_run = json.loads(Path('reports/wic-verifier-v1/run.json').read_text(encoding='utf-8'))
    source_manifest = json.loads(Path('reports/wic-tsv-source-v1/manifest.json').read_text(encoding='utf-8'))
    for p, sha in source_manifest['files_sha256'].items():
        require(digest(SOURCE / p) == sha, 'Contrast source annotation changed')
    # Cache validity includes the exact frozen extraction code and source data.
    for p, sha in prior_run['source_sha256'].items():
        require(digest(p) == sha, 'Frozen verification dependency changed')
    cache_paths = [PRIOR / 'source-features.safetensors', *[PRIOR / f'v{n}-features.safetensors' for n in range(1, 7)]]
    for p in cache_paths:
        require(digest(p) == prior_run['outputs_sha256'][str(p).replace('\\', '/')], 'Frozen verification feature cache changed')
    rows = json.loads((SOURCE / 'train.json').read_text(encoding='utf-8'))
    official = json.loads((SOURCE / 'dev.json').read_text(encoding='utf-8'))
    selection = partition(rows)
    features = load_file(str(PRIOR / 'source-features.safetensors'))
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Contrast run sources changed')
        for p, sha in run['outputs_sha256'].items():
            require(digest(p) == sha, 'Contrast artifact changed')
        require(selection == json.loads((ROOT / 'data-selection.json').read_text(encoding='utf-8')), 'Contrast partition changed')
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        RAW.mkdir(parents=True, exist_ok=False)
        write(ROOT / 'protocol.json', contract)
        write(ROOT / 'data-selection.json', selection)
    heads, histories, official_report = {}, {}, {}
    for key, hidden, coefficient in CONFIGS:
        head, history = fit(features['train'], rows, selection, hidden, coefficient)
        heads[key], histories[key] = head, history
        result = binary_metrics(scores(head, features['dev']).tolist(), [r['matches'] for r in official])
        official_report[key] = result
        if args.verify_only:
            require(history == json.loads((ROOT / f'{key}-training.json').read_text(encoding='utf-8')), 'Contrast history changed')
            weights = load_file(str(RAW / f'{key}.safetensors'))
            require(all(torch.equal(v, weights[k]) for k, v in head.state_dict().items()), 'Contrast weights changed')
        else:
            write(ROOT / f'{key}-training.json', history)
            save_file(head.state_dict(), str(RAW / f'{key}.safetensors'))
            print('contrast head', key, history['selected_epoch'], history['selected_dev'], flush=True)
    chosen = max(heads, key=lambda key: selection_key(histories[key]['selected_dev']))
    chosen_record = {'selected': chosen, 'scope': 'internal heldout contexts and lemmas; no official dev or Noema selection'}
    if args.verify_only:
        require(chosen_record == json.loads((ROOT / 'selection.json').read_text(encoding='utf-8')), 'Contrast choice changed')
        require(official_report == json.loads((ROOT / 'official-dev.json').read_text(encoding='utf-8')), 'Official dev replay differs')
    else:
        write(ROOT / 'selection.json', chosen_record)
        write(ROOT / 'official-dev.json', official_report)
    bank = sorted(definitions(), key=lambda d: d['id'])
    ids = [d['id'] for d in bank]
    for n in range(1, 7):
        fixture = rows_from_fixture(json.loads(Path(f'data/definition-probe-v{n}.json').read_text(encoding='utf-8')), set(ids))
        paired = load_file(str(PRIOR / f'v{n}-features.safetensors'))['features']
        report = {}
        for key, head in heads.items():
            predictions, report[key] = noema_report(scores(head, paired), fixture, ids, bank)
            if args.verify_only:
                require(predictions == json.loads((RAW / f'{key}-v{n}.json').read_text(encoding='utf-8')), 'Contrast predictions changed')
            else:
                write(RAW / f'{key}-v{n}.json', predictions)
        if args.verify_only:
            require(report == json.loads((ROOT / f'v{n}-evaluation.json').read_text(encoding='utf-8')), 'Contrast Noema evaluation changed')
        else:
            write(ROOT / f'v{n}-evaluation.json', report)
            print('contrast Noema', n, {k: {l: v[l]['supported']['correct'] for l in ('ja', 'en')} for k, v in report.items()}, flush=True)
    if args.verify_only:
        write(ROOT / 'verification.json', {'retrained_heads': 4, 'selection_history_weights_predictions_exact': True,
                                           'noema_rows_per_head': 442, **contract})
        print('contrast verification passed', flush=True)
    else:
        paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
        write(ROOT / 'run.json', {**contract, 'selected': chosen, 'fresh_encoder_calls': 0,
              'encoder_feature_run_sha256': digest('reports/wic-verifier-v1/run.json'), 'confirmed_translations': 0,
              'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
