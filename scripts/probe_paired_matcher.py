"""Train candidate-independent pair heads; select only on held-out development concepts."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.bem_probe import summarize
from noema.definition_probe import definitions, digest, rows_from_fixture
from noema.encoder import deterministic
from noema.joint_lexical import decode_joint
from noema.lexical_frames import SharedConceptMatcher
from noema.lexical_frame_metrics import assess_lexical_frames, summarize_lexical_frames
from noema.paired_matcher import PairCompatibilityHead, paired_features, independent_features, pooled_pair
from noema.semantics import require
from noema.shared_matcher import TRAIN_IDS, DEV_IDS, predict, query_features
from scripts.prepare_reference_corpus import write
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/paired-matcher-v1')
RAW = Path('artifacts/paired-matcher-v1')
SETTINGS = {'seed': 17, 'epochs': 20, 'batch_size': 32, 'learning_rate': .002,
            'weight_decay': .001, 'temperature_multiplier': 10., 'residual_bound': .25}
CONFIGS = [('independent-linear', 'independent', 0), ('independent-mlp', 'independent', 64),
           ('paired-linear', 'paired', 0), ('paired-mlp', 'paired', 64)]
SOURCES = ['noema/paired_matcher.py', 'noema/encoder.py', 'noema/definition_probe.py', 'noema/bem_probe.py',
           'noema/shared_matcher.py', 'noema/lexical_frames.py', 'noema/joint_lexical.py', 'noema/lexical_frame_metrics.py',
           'noema/semantics.py', 'noema/language.py', 'noema/glossary.py', 'scripts/probe_paired_matcher.py',
           'scripts/train_mention_scope.py', 'scripts/prepare_reference_corpus.py',
           'docs/paired-matcher-v1-protocol.md', 'data/definition-probe-v4.json', 'data/definition-probe-v5.json',
           'data/lexical-frames-v1.json', 'data/joint-lexical-v2.json', 'reports/joint-lexical-v2/run.json',
           'reports/shared-matcher-v1/run.json', 'reports/shared-matcher-v1/selection.json',
           'reports/shared-matcher-v1/definitions.json', 'reports/shared-matcher-v1/linear-training.json']
SOURCES += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]


def score(head, features):
    with torch.inference_mode():
        return torch.cat([head(features[i:i + 32]) for i in range(0, len(features), 32)])


def accuracy(head, features, rows, ids):
    predicted = score(head, features).argmax(1).tolist()
    values = {lang: sum(ids[p] == row['expected'] for p, row in zip(predicted, rows, strict=True) if row['language'] == lang)
                   / sum(row['language'] == lang for row in rows) for lang in ('ja', 'en')}
    return {**values, 'macro': sum(values.values()) / 2}


def fit(train, dev, selected, train_ids, ids, hidden):
    deterministic()
    head = PairCompatibilityHead(train.shape[-1], hidden)
    labels = torch.tensor([train_ids.index(r['expected']) for r in selected['train']])
    optimizer = torch.optim.AdamW(head.parameters(), lr=SETTINGS['learning_rate'], weight_decay=SETTINGS['weight_decay'])
    history = [{'epoch': 0, 'training_loss': None, 'dev': accuracy(head, dev, selected['dev'], ids)}]
    best_epoch, best_accuracy = 0, history[0]['dev']['macro']
    best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    generator = torch.Generator().manual_seed(17)
    for epoch in range(1, SETTINGS['epochs'] + 1):
        order, total = torch.randperm(len(train), generator=generator), 0.
        head.train()
        for offset in range(0, len(order), SETTINGS['batch_size']):
            indices = order[offset:offset + SETTINGS['batch_size']]
            loss = torch.nn.functional.cross_entropy(head(train[indices]) * 10., labels[indices])
            require(bool(torch.isfinite(loss)), 'Non-finite pair training loss')
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(indices)
        head.eval()
        result = accuracy(head, dev, selected['dev'], ids)
        history.append({'epoch': epoch, 'training_loss': total / len(train), 'dev': result})
        if result['macro'] > best_accuracy:
            best_epoch, best_accuracy = epoch, result['macro']
            best = {k: v.detach().clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best, strict=True)
    head.eval().requires_grad_(False)
    return head, {'selected_epoch': best_epoch, 'selected_dev': history[best_epoch]['dev'], 'history': history,
                  'parameters': sum(p.numel() for p in head.parameters())}


def extract(encoder, rows, bank, mode, name):
    if mode == 'paired':
        result = paired_features(encoder, rows, bank, progress=lambda done, count: print(name, done, '/', count, flush=True))
    else:
        result = independent_features(encoder, rows, bank)
    save_file({'features': result}, str(RAW / f'{name}.safetensors'))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in SOURCES}, 'settings': SETTINGS, 'configs': CONFIGS}
    # JSON serializes tuples as lists; normalize the contract for exact replay comparisons.
    contract = json.loads(json.dumps(contract))
    selected = json.loads(Path('reports/shared-matcher-v1/selection.json').read_text(encoding='utf-8'))
    require(not any(set(r['sentence_concepts']) & DEV_IDS for r in selected['train']), 'Heldout concept leaked')
    require({r['expected'] for r in selected['train']} == TRAIN_IDS and {r['expected'] for r in selected['dev']} == DEV_IDS,
            'Selection concept inventory differs')
    require(not {r['text'] for r in selected['train']} & {r['text'] for r in selected['dev']}, 'Sentence leakage')
    bank = sorted(definitions(), key=lambda d: d['id'])
    require(bank == sorted(json.loads(Path('reports/shared-matcher-v1/definitions.json').read_text(encoding='utf-8')), key=lambda d: d['id']), 'Definitions changed')
    ids, train_ids = [d['id'] for d in bank], sorted(TRAIN_IDS)
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Pair experiment source changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'Pair experiment artifact changed')
        results = {}
        for key, mode, hidden in CONFIGS:
            train = load_file(str(RAW / f'{mode}-train.safetensors'))['features']
            dev = load_file(str(RAW / f'{mode}-dev.safetensors'))['features']
            head, history = fit(train, dev, selected, train_ids, ids, hidden)
            require(history == json.loads((ROOT / f'{key}-training.json').read_text(encoding='utf-8')), 'Pair history changed')
            weights = load_file(str(RAW / f'{key}.safetensors'))
            require(all(torch.equal(v, weights[k]) for k, v in head.state_dict().items()), 'Pair weights changed')
            for fixture in ('v4', 'v5'):
                rows = rows_from_fixture(json.loads(Path(f'data/definition-probe-{fixture}.json').read_text(encoding='utf-8')), set(ids))
                features = load_file(str(RAW / f'{mode}-{fixture}.safetensors'))['features']
                predictions = predict(score(head, features), rows, ids)
                require(predictions == json.loads((RAW / f'{key}-{fixture}.json').read_text(encoding='utf-8')), 'Pair predictions changed')
                report = json.loads((ROOT / f'{fixture}-evaluation.json').read_text(encoding='utf-8'))
                require(summarize(predictions) == report[key], 'Pair metrics changed')
            results[key] = {'weights_exact': True, 'history_exact': True, 'predictions_exact': True}
            print('verified', key, flush=True)
        for item in json.loads((RAW / 'joint.json').read_text(encoding='utf-8')):
            require(decode_joint(item['baseline'], item['concept_table'], item['role_logits']) == item['joint'], 'Pair joint replay differs')
        write(ROOT / 'verification.json', {'results': results, 'joint_replayed': 32, **contract})
        return
    ROOT.mkdir(parents=True, exist_ok=False)
    RAW.mkdir(parents=True, exist_ok=False)
    write(ROOT / 'protocol.json', contract)
    prior_run = json.loads(Path('reports/joint-lexical-v2/run.json').read_text(encoding='utf-8'))
    for path, sha in prior_run['outputs_sha256'].items():
        require(digest(path) == sha, 'Previous raw structure evidence changed')
    with forbidden_paths() as guards:
        matcher = SharedConceptMatcher()
        encoder = matcher.encoder
        heads, histories = {}, {}
        for mode in ('independent', 'paired'):
            train = extract(encoder, selected['train'], [d for d in bank if d['id'] in TRAIN_IDS], mode, f'{mode}-train')
            dev = extract(encoder, selected['dev'], bank, mode, f'{mode}-dev')
            print('features complete', mode, flush=True)
            for key, kind, hidden in CONFIGS:
                if mode != kind:
                    continue
                heads[key], histories[key] = fit(train, dev, selected, train_ids, ids, hidden)
                save_file(heads[key].state_dict(), str(RAW / f'{key}.safetensors'))
                write(ROOT / f'{key}-training.json', histories[key])
                print('selected', key, histories[key]['selected_epoch'], histories[key]['selected_dev'], flush=True)
        selected_key = max((key for key, _, _ in CONFIGS), key=lambda key: histories[key]['selected_dev']['macro'])
        write(ROOT / 'selection.json', {'selected': selected_key, 'selection_scope': 'development only, 91 candidates'})
        # Repeat the same extraction including deduplication and masks, without changing selected settings.
        repeat_rows = selected['dev'][:2]
        first = paired_features(encoder, repeat_rows, bank[:2])
        second = paired_features(encoder, repeat_rows, bank[:2])
        require(torch.equal(first, second), 'Pair feature repetition differs')
        direct_pairs = list(dict.fromkeys((r['text'], d[r['language']]) for r in repeat_rows for d in bank[:2]))
        encoded = encoder.tokenizer([p[0] for p in direct_pairs], [p[1] for p in direct_pairs], padding=True,
                                    truncation=False, return_tensors='pt', return_offsets_mapping=True)
        offsets = encoded.pop('offset_mapping').tolist()
        sequences = [encoded.sequence_ids(i) for i in range(len(direct_pairs))]
        with torch.inference_mode():
            direct = encoder.model(**encoded).last_hidden_state
        for i, row in enumerate(repeat_rows):
            for j, definition in enumerate(bank[:2]):
                k = direct_pairs.index((row['text'], definition[row['language']]))
                require(torch.equal(first[i, j], pooled_pair(direct[k], offsets[k], sequences[k], row['start'], row['end'])),
                        'Pair extraction differs from direct model forward')
        for fixture in ('v4', 'v5'):
            rows = rows_from_fixture(json.loads(Path(f'data/definition-probe-{fixture}.json').read_text(encoding='utf-8')), set(ids))
            report = {}
            for mode in ('independent', 'paired'):
                features = extract(encoder, rows, bank, mode, f'{mode}-{fixture}')
                for key, kind, _ in CONFIGS:
                    if mode != kind:
                        continue
                    predictions = predict(score(heads[key], features), rows, ids)
                    write(RAW / f'{key}-{fixture}.json', predictions)
                    report[key] = summarize(predictions)
            with torch.inference_mode():
                mini = predict(matcher.head(query_features(encoder, rows), matcher.index.vectors), rows, ids)
            write(RAW / f'minilm-{fixture}.json', mini)
            report['minilm'] = summarize(mini)
            write(ROOT / f'{fixture}-evaluation.json', report)
            print('confirmation', fixture, {key: {l: v[l]['supported']['correct'] for l in ('ja', 'en')} for key, v in report.items()}, flush=True)
        joint_records, report = [], {}
        mode = next(mode for key, mode, _ in CONFIGS if key == selected_key)
        for group, fixture in (('regression', 'lexical-frames-v1'), ('confirmation', 'joint-lexical-v2')):
            cases = {'previous': [], 'selected_pair_head': []}
            for row in json.loads(Path(f'data/{fixture}.json').read_text(encoding='utf-8')):
                prior = json.loads(Path(f'artifacts/joint-lexical-v2/{group}-{row["id"]}.json').read_text(encoding='utf-8'))['result']
                spans = prior['concept_table']['spans']
                queries = [{'language': 'ja', 'text': row['text'], 'span': row['text'][s['start']:s['end']], **s} for s in spans]
                features = (paired_features if mode == 'paired' else independent_features)(encoder, queries, bank)
                table = {'ids': ids, 'spans': spans, 'scores': score(heads[selected_key], features).tolist()}
                result = decode_joint(prior['baseline'], table, prior['role_logits'])
                joint_records.append({'group': group, 'id': row['id'], 'baseline': prior['baseline'], 'concept_table': table,
                                      'role_logits': prior['role_logits'], 'joint': result})
                cases['previous'].append(assess_lexical_frames(row, prior['joint']))
                cases['selected_pair_head'].append(assess_lexical_frames(row, result))
            report[group] = {key: {'summary': summarize_lexical_frames(values), 'cases': values} for key, values in cases.items()}
            print('joint', group, {k: summarize_lexical_frames(v)['core_frames_exact'] for k, v in cases.items()}, flush=True)
        write(RAW / 'joint.json', joint_records)
        write(ROOT / 'joint-evaluation.json', report)
        calls = [g.call_count for g in guards]
        require(not any(calls), 'Forbidden inference path used')
        require(not any(p.requires_grad for p in encoder.model.parameters()) and not any(m.training for m in encoder.model.modules()), 'Unfrozen encoder')
    paths = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
    write(ROOT / 'run.json', {**contract, 'encoder': encoder.metadata, 'selected': selected_key,
          'repeated_pairs': 4, 'repeat_exact': True, 'direct_forward_exact': True, 'forbidden_path_calls': calls, 'confirmed_translations': 0,
          'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})


if __name__ == '__main__':
    main()
