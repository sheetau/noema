"""Broaden shared-head supervision while holding out target concepts across splits."""
import argparse
from collections import Counter
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.broad_matcher_data import prepare
from noema.bem_probe import summarize
from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.encoder import deterministic
from noema.joint_lexical import decode_joint
from noema.lexical_frames import SharedConceptMatcher
from noema.lexical_frame_metrics import assess_lexical_frames, summarize_lexical_frames
from noema.paired_matcher import PairCompatibilityHead, paired_features
from noema.semantics import require
from noema.shared_matcher import predict, query_features
from scripts.prepare_reference_corpus import write
from scripts.probe_paired_matcher import score
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/broad-matcher-v1')
RAW = Path('artifacts/broad-matcher-v1')
SETTINGS = {'seed': 17, 'epochs': 20, 'batch_size': 32, 'learning_rate': .002, 'weight_decay': .001,
            'temperature': 10., 'selection': 'language-and-concept macro accuracy', 'training_weight': 'inverse language-concept count'}
SOURCES = ['noema/broad_matcher_data.py', 'noema/paired_matcher.py', 'noema/encoder.py', 'noema/definition_probe.py',
           'noema/bem_probe.py', 'noema/shared_matcher.py', 'noema/lexical_frames.py', 'noema/joint_lexical.py',
           'noema/lexical_frame_metrics.py', 'noema/semantics.py', 'noema/language.py', 'noema/glossary.py',
           'scripts/probe_broad_matcher.py', 'scripts/probe_paired_matcher.py', 'scripts/prepare_reference_corpus.py',
           'scripts/train_mention_scope.py', 'docs/broad-matcher-v1-protocol.md',
           'reports/shared-matcher-v1/selection.json', 'reports/shared-matcher-v1/definitions.json',
           'reports/shared-matcher-v1/run.json', 'reports/shared-matcher-v1/linear-training.json',
           'reports/paired-matcher-v1/run.json', 'reports/joint-lexical-v2/run.json',
           'data/lexical-frames-v1.json', 'data/joint-lexical-v2.json']
SOURCES += [f'data/definition-probe-v{n}.json' for n in range(1, 7)]
SOURCES += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]


def balanced_weights(rows):
    counts = Counter((r['language'], r['expected']) for r in rows)
    require(rows and all(r['expected'] is not None for r in rows), 'Missing training label')
    return torch.tensor([len(rows) / (len(counts) * counts[r['language'], r['expected']]) for r in rows])


def macro_accuracy(predicted, rows, ids):
    counts, correct = Counter(), Counter()
    for p, row in zip(predicted, rows, strict=True):
        key = row['language'], row['expected']
        counts[key] += 1
        correct[key] += ids[p] == row['expected']
    result = {}
    for language in ('ja', 'en'):
        keys = [k for k in counts if k[0] == language]
        require(keys, 'Missing development language')
        result[language] = sum(correct[k] / counts[k] for k in keys) / len(keys)
    return {**result, 'macro': sum(result.values()) / 2}


def fit(train, dev, selection, ids):
    deterministic()
    rows = selection['rows']
    train_ids = selection['concepts']['train']
    head = PairCompatibilityHead(train.shape[-1], hidden=0)
    weights = balanced_weights(rows['train'])
    labels = torch.tensor([train_ids.index(r['expected']) for r in rows['train']])
    optimizer = torch.optim.AdamW(head.parameters(), lr=.002, weight_decay=.001)
    def assess():
        return macro_accuracy(score(head, dev).argmax(1).tolist(), rows['dev'], ids)
    history = [{'epoch': 0, 'training_loss': None, 'dev': assess()}]
    best_accuracy, best_epoch = history[0]['dev']['macro'], 0
    best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    generator = torch.Generator().manual_seed(17)
    for epoch in range(1, 21):
        order, total = torch.randperm(len(train), generator=generator), 0.
        head.train()
        for offset in range(0, len(order), 32):
            indices = order[offset:offset + 32]
            loss = (torch.nn.functional.cross_entropy(head(train[indices]) * 10., labels[indices], reduction='none') * weights[indices]).mean()
            require(bool(torch.isfinite(loss)), 'Non-finite broad training loss')
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(indices)
        head.eval()
        value = assess()
        history.append({'epoch': epoch, 'training_loss': total / len(train), 'dev': value})
        if value['macro'] > best_accuracy:
            best_accuracy, best_epoch = value['macro'], epoch
            best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best, strict=True)
    head.eval().requires_grad_(False)
    return head, {'selected_epoch': best_epoch, 'selected_dev': history[best_epoch]['dev'], 'history': history,
                  'parameters': sum(p.numel() for p in head.parameters())}


def extract(encoder, rows, bank, name):
    result = paired_features(encoder, rows, bank, progress=lambda done, count: print(name, done, '/', count, flush=True))
    save_file({'features': result}, str(RAW / f'{name}.safetensors'))
    return result


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in SOURCES}, 'settings': SETTINGS}
    selection = prepare()
    bank = sorted(definitions(), key=lambda d: d['id'])
    ids = [d['id'] for d in bank]
    new_rows = rows_from_fixture(json.loads(Path('data/definition-probe-v6.json').read_text(encoding='utf-8')), set(ids))
    require({r['expected'] for r in new_rows if r['expected']} == set(selection['concepts']['test']), 'New confirmation target concepts differ')
    require(not {r['text'] for r in new_rows} & {r['text'] for rs in selection['rows'].values() for r in rs}, 'New confirmation text is not new')
    evaluations = {'historical_test': selection['rows']['test'], 'v6': new_rows,
                   'observed_unknown': selection['unknown_observed_diagnostic']}
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Broad experiment sources changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'Broad artifact changed')
        require(selection == json.loads((ROOT / 'data-selection.json').read_text(encoding='utf-8')), 'Data split changed')
        train, dev = (load_file(str(RAW / f'{name}.safetensors'))['features'] for name in ('train', 'dev'))
        head, history = fit(train, dev, selection, ids)
        require(history == json.loads((ROOT / 'training.json').read_text(encoding='utf-8')), 'Broad history changed')
        weights = load_file(str(RAW / 'linear.safetensors'))
        require(all(torch.equal(v, weights[k]) for k, v in head.state_dict().items()), 'Broad weights changed')
        for name, rows in evaluations.items():
            features = load_file(str(RAW / f'{name}.safetensors'))['features']
            predictions = predict(score(head, features), rows, ids)
            require(predictions == json.loads((RAW / f'{name}-broad.json').read_text(encoding='utf-8')), 'Broad predictions changed')
            report = json.loads((ROOT / f'{name}-evaluation.json').read_text(encoding='utf-8'))
            require(summarize(predictions) == report['broad'], 'Broad evaluation changed')
        for item in json.loads((RAW / 'joint.json').read_text(encoding='utf-8')):
            require(decode_joint(item['baseline'], item['concept_table'], item['role_logits']) == item['joint'], 'Broad joint replay differs')
        write(ROOT / 'verification.json', {'selection_exact': True, 'weights_exact': True, 'history_exact': True,
              'prediction_rows_replayed': {k: len(v) for k, v in evaluations.items()}, 'joint_replayed': 32, **contract})
        print('broad verification passed', flush=True)
        return
    ROOT.mkdir(parents=True, exist_ok=False)
    RAW.mkdir(parents=True, exist_ok=False)
    write(ROOT / 'protocol.json', contract)
    write(ROOT / 'data-selection.json', selection)
    prior_run = json.loads(Path('reports/joint-lexical-v2/run.json').read_text(encoding='utf-8'))
    for path, sha in prior_run['outputs_sha256'].items():
        require(digest(path) == sha, 'Prior joint evidence changed')
    old_run = json.loads(Path('reports/paired-matcher-v1/run.json').read_text(encoding='utf-8'))
    old_path = 'artifacts/paired-matcher-v1/paired-linear.safetensors'
    require(digest(old_path) == old_run['outputs_sha256'][old_path], 'Prior pair weights changed')
    with forbidden_paths() as guards:
        matcher = SharedConceptMatcher()
        encoder = matcher.encoder
        train = extract(encoder, selection['rows']['train'], [d for d in bank if d['id'] in selection['concepts']['train']], 'train')
        dev = extract(encoder, selection['rows']['dev'], bank, 'dev')
        head, history = fit(train, dev, selection, ids)
        write(ROOT / 'training.json', history)
        save_file(head.state_dict(), str(RAW / 'linear.safetensors'))
        print('selected broad epoch', history['selected_epoch'], history['selected_dev'], flush=True)
        old_head = PairCompatibilityHead(encoder.dimension, hidden=0)
        old_head.load_state_dict(load_file(old_path), strict=True)
        old_head.eval().requires_grad_(False)
        first = paired_features(encoder, selection['rows']['dev'][:2], bank[:2])
        require(torch.equal(first, paired_features(encoder, selection['rows']['dev'][:2], bank[:2])), 'Broad feature repetition differs')
        for name, rows in evaluations.items():
            features = extract(encoder, rows, bank, name)
            with torch.inference_mode():
                predictions = {'broad': predict(score(head, features), rows, ids),
                               'previous_pair': predict(score(old_head, features), rows, ids),
                               'minilm': predict(matcher.head(query_features(encoder, rows), matcher.index.vectors), rows, ids)}
            for method, values in predictions.items():
                write(RAW / f'{name}-{method}.json', values)
            report = {k: summarize(v) for k, v in predictions.items()}
            write(ROOT / f'{name}-evaluation.json', report)
            print(name, {k: {lang: v[lang]['supported']['correct'] for lang in ('ja', 'en')} for k, v in report.items()}, flush=True)
        records, report, overlaps = [], {}, []
        supervised_texts = {r['text'] for split in ('train', 'dev') for r in selection['rows'][split]}
        for group, fixture in (('regression', 'lexical-frames-v1'), ('confirmation', 'joint-lexical-v2')):
            cases = {'previous': [], 'broad': []}
            for row in json.loads(Path(f'data/{fixture}.json').read_text(encoding='utf-8')):
                if row['text'] in supervised_texts:
                    overlaps.append(row['id'])
                prior = json.loads(Path(f'artifacts/joint-lexical-v2/{group}-{row["id"]}.json').read_text(encoding='utf-8'))['result']
                spans = prior['concept_table']['spans']
                queries = [{'language': 'ja', 'text': row['text'], 'span': row['text'][s['start']:s['end']], **s} for s in spans]
                features = paired_features(encoder, queries, bank)
                table = {'ids': ids, 'spans': spans, 'scores': score(head, features).tolist()}
                result = decode_joint(prior['baseline'], table, prior['role_logits'])
                records.append({'group': group, 'id': row['id'], 'baseline': prior['baseline'], 'concept_table': table,
                                'role_logits': prior['role_logits'], 'joint': result})
                cases['previous'].append(assess_lexical_frames(row, prior['joint']))
                cases['broad'].append(assess_lexical_frames(row, result))
            report[group] = {k: {'summary': summarize_lexical_frames(v), 'cases': v} for k, v in cases.items()}
            print('joint', group, {k: summarize_lexical_frames(v)['core_frames_exact'] for k, v in cases.items()}, flush=True)
        write(RAW / 'joint.json', records)
        write(ROOT / 'joint-evaluation.json', report)
        calls = [g.call_count for g in guards]
        require(not any(calls), 'Forbidden inference path used')
        require(not any(p.requires_grad for p in encoder.model.parameters()) and not any(m.training for m in encoder.model.modules()), 'Unfrozen base model')
    paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
    write(ROOT / 'run.json', {**contract, 'encoder': encoder.metadata, 'forbidden_path_calls': calls,
          'repeat_exact': True, 'repeated_pairs': 4, 'joint_supervised_text_overlap': overlaps, 'confirmed_translations': 0,
          'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
