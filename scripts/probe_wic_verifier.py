"""Learn definition compatibility from external binary annotations, then inspect Noema transfer."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.bem_probe import summarize
from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.encoder import FrozenEncoder, deterministic
from noema.paired_matcher import paired_features
from noema.semantics import require
from noema.shared_matcher import predict
from noema.verification_matcher import VerificationHead, verification_features, binary_metrics
from scripts.prepare_reference_corpus import write
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/wic-verifier-v1')
RAW = Path('artifacts/wic-verifier-v1')
SOURCE = Path('artifacts/wic-tsv-source-v1')
SETTINGS = {'seed': 17, 'epochs': 20, 'batch_size': 64, 'learning_rate': .002, 'weight_decay': .001,
            'threshold_logit': 0, 'max_pair_length': 256, 'selection': 'official dev balanced accuracy'}
CODE = ['noema/verification_matcher.py', 'noema/wic_tsv_data.py', 'noema/paired_matcher.py', 'noema/encoder.py',
        'noema/definition_probe.py', 'noema/bem_probe.py', 'noema/shared_matcher.py', 'noema/semantics.py',
        'noema/glossary.py', 'noema/language.py', 'scripts/probe_wic_verifier.py', 'scripts/prepare_reference_corpus.py',
        'scripts/train_mention_scope.py', 'docs/wic-verifier-v1-protocol.md', 'reports/wic-tsv-source-v1/manifest.json']
CODE += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]
CODE += [f'data/definition-probe-v{n}.json' for n in range(1, 7)]


def scores(head, features):
    with torch.inference_mode():
        return torch.cat([head(features[i:i + 32]) for i in range(0, len(features), 32)])


def fit(features, rows, hidden):
    deterministic()
    head = VerificationHead(features['train'].shape[-1], hidden)
    labels = torch.tensor([r['matches'] for r in rows['train']], dtype=torch.float32)
    dev_labels = [r['matches'] for r in rows['dev']]
    optimizer = torch.optim.AdamW(head.parameters(), lr=.002, weight_decay=.001)
    history = [{'epoch': 0, 'training_loss': None, 'dev': binary_metrics(scores(head, features['dev']).tolist(), dev_labels)}]
    best_accuracy, epoch_best = history[0]['dev']['balanced_accuracy'], 0
    best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    generator = torch.Generator().manual_seed(17)
    for epoch in range(1, 21):
        order, total = torch.randperm(len(labels), generator=generator), 0.
        head.train()
        for offset in range(0, len(order), 64):
            selected = order[offset:offset + 64]
            loss = torch.nn.functional.binary_cross_entropy_with_logits(head(features['train'][selected]), labels[selected])
            require(bool(torch.isfinite(loss)), 'Non-finite verification loss')
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(selected)
        head.eval()
        metrics = binary_metrics(scores(head, features['dev']).tolist(), dev_labels)
        history.append({'epoch': epoch, 'training_loss': total / len(labels), 'dev': metrics})
        if metrics['balanced_accuracy'] > best_accuracy:
            best_accuracy, epoch_best = metrics['balanced_accuracy'], epoch
            best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best, strict=True)
    head.eval().requires_grad_(False)
    return head, {'selected_epoch': epoch_best, 'selected_dev': history[epoch_best]['dev'], 'history': history,
                  'parameters': sum(p.numel() for p in head.parameters())}


def noema_report(values, rows, ids, bank):
    predictions = predict(values, rows, ids)
    kinds = {d['id']: d['kind'] for d in bank}
    positive = (values >= 0).sum(1).tolist()
    for p, count in zip(predictions, positive, strict=True):
        p['positive_candidate_count'] = count
    result = summarize(predictions)
    result['threshold_diagnostic'] = {language: {
        'unknown_rows': sum(r['language'] == language and r['expected'] is None for r in predictions),
        'unknown_with_positive_candidate': sum(r['language'] == language and r['expected'] is None and r['positive_candidate_count'] > 0 for r in predictions),
        'known_top1_correct_and_positive': sum(r['language'] == language and r['expected'] is not None and r['top'][0]['concept'] == r['expected'] and r['top'][0]['score'] >= 0 for r in predictions)}
        for language in ('ja', 'en')}
    result['by_gold_kind'] = {language: {kind: {
        'count': sum(p['language'] == language and kinds.get(p['expected']) == kind for p in predictions),
        'correct': sum(p['language'] == language and kinds.get(p['expected']) == kind and p['top'][0]['concept'] == p['expected'] for p in predictions)}
        for kind in ('entity', 'place', 'event', 'state')} for language in ('ja', 'en')}
    return predictions, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in CODE}, 'settings': SETTINGS}
    manifest = json.loads(Path('reports/wic-tsv-source-v1/manifest.json').read_text(encoding='utf-8'))
    for path, sha in manifest['files_sha256'].items():
        require(digest(SOURCE / path) == sha, 'WiC annotation source changed')
    rows = {split: json.loads((SOURCE / f'{split}.json').read_text(encoding='utf-8')) for split in ('train', 'dev')}
    bank = sorted(definitions(), key=lambda d: d['id'])
    ids = [d['id'] for d in bank]
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Verifier source contract changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'Verifier artifact changed')
        features = load_file(str(RAW / 'source-features.safetensors'))
        for key, hidden in (('linear', 0), ('mlp', 64)):
            head, history = fit(features, rows, hidden)
            require(history == json.loads((ROOT / f'{key}-training.json').read_text(encoding='utf-8')), 'Verifier history changed')
            weights = load_file(str(RAW / f'{key}.safetensors'))
            require(all(torch.equal(v, weights[k]) for k, v in head.state_dict().items()), 'Verifier weights changed')
            for n in range(1, 7):
                fixture = rows_from_fixture(json.loads(Path(f'data/definition-probe-v{n}.json').read_text(encoding='utf-8')), set(ids))
                features_n = load_file(str(RAW / f'v{n}-features.safetensors'))['features']
                predictions, report = noema_report(scores(head, features_n), fixture, ids, bank)
                require(predictions == json.loads((RAW / f'{key}-v{n}.json').read_text(encoding='utf-8')), 'Verifier Noema predictions changed')
                require(report == json.loads((ROOT / f'v{n}-evaluation.json').read_text(encoding='utf-8'))[key], 'Verifier Noema metrics changed')
        write(ROOT / 'verification.json', {'retrained_heads': 2, 'weights_and_history_exact': True, 'noema_rows_replayed_per_head': 442, **contract})
        print('verifier replay passed', flush=True)
        return
    ROOT.mkdir(parents=True, exist_ok=False)
    RAW.mkdir(parents=True, exist_ok=False)
    write(ROOT / 'protocol.json', contract)
    with forbidden_paths() as guards:
        encoder = FrozenEncoder('minilm', offline=True)
        features = {split: verification_features(encoder, values) for split, values in rows.items()}
        save_file(features, str(RAW / 'source-features.safetensors'))
        first = verification_features(encoder, rows['dev'][:4])
        require(torch.equal(first, verification_features(encoder, rows['dev'][:4])), 'Verifier feature repetition differs')
        print('source features complete', flush=True)
        heads, histories = {}, {}
        for key, hidden in (('linear', 0), ('mlp', 64)):
            heads[key], histories[key] = fit(features, rows, hidden)
            save_file(heads[key].state_dict(), str(RAW / f'{key}.safetensors'))
            write(ROOT / f'{key}-training.json', histories[key])
            print('source selection', key, histories[key]['selected_epoch'], histories[key]['selected_dev'], flush=True)
        chosen = max(heads, key=lambda k: histories[k]['selected_dev']['balanced_accuracy'])
        write(ROOT / 'selection.json', {'selected': chosen, 'scope': 'WiC-TSV official development only; not independent test'})
        for n in range(1, 7):
            fixture = rows_from_fixture(json.loads(Path(f'data/definition-probe-v{n}.json').read_text(encoding='utf-8')), set(ids))
            paired = paired_features(encoder, fixture, bank, progress=lambda done, count: print(f'v{n}', done, '/', count, flush=True))
            save_file({'features': paired}, str(RAW / f'v{n}-features.safetensors'))
            reports = {}
            for key, head in heads.items():
                predictions, reports[key] = noema_report(scores(head, paired), fixture, ids, bank)
                write(RAW / f'{key}-v{n}.json', predictions)
            write(ROOT / f'v{n}-evaluation.json', reports)
            print('Noema regression', n, {k: {l: v[l]['supported']['correct'] for l in ('ja', 'en')} for k, v in reports.items()}, flush=True)
        calls = [g.call_count for g in guards]
        require(not any(calls), 'Forbidden inference path used')
        require(not any(p.requires_grad for p in encoder.model.parameters()) and not any(m.training for m in encoder.model.modules()), 'Base encoder is not frozen')
    paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
    write(ROOT / 'run.json', {**contract, 'encoder': encoder.metadata, 'source_pair_max_length': 256,
          'selected': chosen, 'forbidden_path_calls': calls, 'repeat_rows': 4, 'repeat_exact': True,
          'noema_training_examples': 0, 'confirmed_translations': 0,
          'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
