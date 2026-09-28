"""Frozen embedding substitution with a shared three-parameter head."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from noema.bge_encoder import FrozenBGE
from noema.bem_probe import summarize
from noema.definition_probe import DefinitionIndex, definitions, digest, rows_from_fixture
from noema.joint_lexical import decode_joint, complete_concept_scores
from noema.lexical_frames import SharedConceptMatcher
from noema.lexical_frame_metrics import assess_lexical_frames, summarize_lexical_frames
from noema.semantics import CONCEPTS, require
from noema.shared_matcher import TRAIN_IDS, DEV_IDS, SETTINGS, fit, query_features, predict
from scripts.prepare_reference_corpus import write
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/bge-matcher-v1')
RAW = Path('artifacts/bge-matcher-v1')
FIXTURES = {k: Path(f'data/definition-probe-{k}.json') for k in ('v1', 'v2', 'v3', 'v4')}
SOURCES = ['noema/bge_encoder.py', 'noema/encoder.py', 'noema/shared_matcher.py', 'noema/definition_probe.py',
           'noema/bem_probe.py', 'noema/joint_lexical.py', 'noema/lexical_frames.py', 'noema/lexical_frame_metrics.py',
           'noema/semantics.py', 'noema/language.py', 'noema/glossary.py', 'scripts/probe_bge_matcher.py',
           'scripts/train_mention_scope.py', 'scripts/prepare_reference_corpus.py',
           'docs/bge-matcher-v1-protocol.md', 'reports/shared-matcher-v1/selection.json',
           'reports/shared-matcher-v1/definitions.json', 'reports/shared-matcher-v1/linear-training.json',
           'reports/shared-matcher-v1/run.json', 'reports/joint-lexical-v2/run.json',
           'data/lexical-frames-v1.json', 'data/joint-lexical-v2.json'] + list(map(str, FIXTURES.values()))
SOURCES += [str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json'))]


def train_head(features, selected, ids):
    train_ids, dev_ids = sorted(TRAIN_IDS), sorted(CONCEPTS)
    train_bank = features['definitions'][[ids.index(c) for c in train_ids]]
    dev_bank = features['definitions'][[ids.index(c) for c in dev_ids]]
    return fit(features['train'], features['dev'], train_bank, dev_bank, selected['train'], selected['dev'],
               train_ids, dev_ids, rank=0)


def validate_selection(selected):
    require({r['expected'] for r in selected['train']} == TRAIN_IDS, 'Training concept inventory changed')
    require({r['expected'] for r in selected['dev']} == DEV_IDS, 'Development concept inventory changed')
    require(not any(set(r['sentence_concepts']) & DEV_IDS for r in selected['train']), 'Development concept leaked')
    require(not {r['text'] for r in selected['train']} & {r['text'] for r in selected['dev']}, 'Sentence leakage')


def encoder_check(encoder):
    texts = ['A door was open.', '窓は閉まっていた。']
    first, second = encoder.encode(texts), encoder.encode(texts)
    require(all(torch.equal(a['tokens'], b['tokens']) for a, b in zip(first, second, strict=True)), 'BGE repetition differs')
    encoded = encoder.tokenizer(texts, return_tensors='pt', padding=True, truncation=True, max_length=128)
    with torch.inference_mode():
        direct = encoder.model(**encoded).last_hidden_state
    for i, feature in enumerate(first):
        n = int(encoded['attention_mask'][i].sum())
        require(torch.equal(feature['tokens'], direct[i, :n]) and torch.equal(feature['pooled'], direct[i, 0]),
                'BGE wrapper differs from direct forward or CLS')
    require(not any(p.requires_grad for p in encoder.model.parameters()) and not any(m.training for m in encoder.model.modules()),
            'BGE encoder is not frozen and in eval mode')
    return {'repeated_texts': len(texts), 'tokens_exact': True, 'direct_forward_exact': True, 'cls_exact': True}


def evaluate_features(cache, rows, head, ids):
    with torch.inference_mode():
        scores = {'bge_linear': head(cache, ids['vectors'])}
        scores.update({f'bge_{name}': cache[:, i] @ ids['vectors'].T
                       for i, name in enumerate(('contextual', 'isolated', 'sentence'))})
    return {name: predict(values, rows, ids['ids']) for name, values in scores.items()}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    contract = {'source_sha256': {p: digest(p) for p in SOURCES}, 'settings': SETTINGS}
    selected = json.loads(Path('reports/shared-matcher-v1/selection.json').read_text(encoding='utf-8'))
    validate_selection(selected)
    bank = definitions()
    ids = sorted(d['id'] for d in bank)
    require(bank == json.loads(Path('reports/shared-matcher-v1/definitions.json').read_text(encoding='utf-8')), 'Definitions changed')
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'BGE experiment sources changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(path) == sha, 'BGE experiment artifact changed')
        features = load_file(str(RAW / 'features.safetensors'))
        head, history = train_head(features, selected, ids)
        weights = load_file(str(RAW / 'linear.safetensors'))
        require(all(torch.equal(value, weights[k]) for k, value in head.state_dict().items()), 'BGE head retraining differs')
        require(history == json.loads((ROOT / 'training.json').read_text(encoding='utf-8')), 'BGE training history differs')
        counts = {}
        for name, path in FIXTURES.items():
            rows = rows_from_fixture(json.loads(path.read_text(encoding='utf-8')), set(ids))
            predictions = evaluate_features(features[name], rows, head, {'ids': ids, 'vectors': features['definitions']})
            report = json.loads((ROOT / f'{name}-evaluation.json').read_text(encoding='utf-8'))
            for method, values in predictions.items():
                require(values == json.loads((RAW / f'{name}-{method}.json').read_text(encoding='utf-8')), 'BGE score replay differs')
                require(summarize(values) == report[method], 'BGE metrics replay differs')
            counts[name] = len(rows)
        joint = json.loads((RAW / 'joint.json').read_text(encoding='utf-8'))
        for item in joint:
            require(decode_joint(item['baseline'], item['concept_table'], item['role_logits']) == item['joint'], 'BGE joint replay differs')
        write(ROOT / 'verification.json', {'head_weights_exact': True, 'head_history_exact': True,
                                          'score_rows_replayed': counts, 'joint_replayed': len(joint), **contract})
        print('BGE verification passed', flush=True)
        return
    ROOT.mkdir(parents=True, exist_ok=False)
    RAW.mkdir(parents=True, exist_ok=False)
    write(ROOT / 'protocol.json', contract)
    # Validate and hash prior raw evidence before loading any new model.
    prior_run = json.loads(Path('reports/joint-lexical-v2/run.json').read_text(encoding='utf-8'))
    for path, sha in prior_run['outputs_sha256'].items():
        require(digest(path) == sha, 'Previous joint evidence changed')
    with forbidden_paths() as guards:
        encoder = FrozenBGE()
        check = encoder_check(encoder)
        print('BGE loaded and forward checked', flush=True)
        index = DefinitionIndex(encoder, bank)
        features = {'definitions': index.vectors}
        for split in ('train', 'dev'):
            features[split] = query_features(encoder, selected[split])
            print('BGE features', split, len(selected[split]), flush=True)
        head, history = train_head(features, selected, ids)
        write(ROOT / 'training.json', history)
        save_file(head.state_dict(), str(RAW / 'linear.safetensors'))
        print('BGE selected epoch', history['selected_epoch'], flush=True)
        mini = SharedConceptMatcher()
        for name, path in FIXTURES.items():
            rows = rows_from_fixture(json.loads(path.read_text(encoding='utf-8')), set(ids))
            features[name] = query_features(encoder, rows)
            predictions = evaluate_features(features[name], rows, head, {'ids': ids, 'vectors': index.vectors})
            mini_features = query_features(mini.encoder, rows)
            with torch.inference_mode():
                predictions['minilm_linear'] = predict(mini.head(mini_features, mini.index.vectors), rows, ids)
            for method, values in predictions.items():
                write(RAW / f'{name}-{method}.json', values)
            write(ROOT / f'{name}-evaluation.json', {method: summarize(values) for method, values in predictions.items()})
            print('definition evaluation', name, {k: {lang: summarize(v)[lang]['supported']['correct'] for lang in ('ja', 'en')}
                                                  for k, v in predictions.items()}, flush=True)
        from types import SimpleNamespace
        matcher = SimpleNamespace(encoder=encoder, index=index, head=head)
        joint_records, joint_report = [], {}
        for group, fixture in (('regression', 'lexical-frames-v1'), ('confirmation', 'joint-lexical-v2')):
            cases = {'previous': [], 'bge': []}
            for row in json.loads(Path(f'data/{fixture}.json').read_text(encoding='utf-8')):
                prior = json.loads(Path(f'artifacts/joint-lexical-v2/{group}-{row["id"]}.json').read_text(encoding='utf-8'))['result']
                table = complete_concept_scores(matcher, row['text'], prior['concept_table']['spans'])
                result = decode_joint(prior['baseline'], table, prior['role_logits'])
                joint_records.append({'group': group, 'id': row['id'], 'baseline': prior['baseline'], 'concept_table': table,
                                      'role_logits': prior['role_logits'], 'joint': result})
                cases['previous'].append(assess_lexical_frames(row, prior['joint']))
                cases['bge'].append(assess_lexical_frames(row, result))
            joint_report[group] = {method: {'summary': summarize_lexical_frames(values), 'cases': values} for method, values in cases.items()}
            print('joint regression', group, {k: summarize_lexical_frames(v)['core_frames_exact'] for k, v in cases.items()}, flush=True)
        write(RAW / 'joint.json', joint_records)
        write(ROOT / 'joint-evaluation.json', joint_report)
        save_file(features, str(RAW / 'features.safetensors'))
        calls = [g.call_count for g in guards]
        require(not any(calls), 'Forbidden inference path used')
    outputs = [*sorted(ROOT.glob('*.json')), *sorted(RAW.glob('*'))]
    write(ROOT / 'run.json', {**contract, 'model': encoder.metadata, 'encoder_checks': check,
          'forbidden_path_calls': calls, 'trained_parameters': history['parameters'],
          'selected_epoch': history['selected_epoch'], 'confirmed_translations': 0,
          'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in outputs}})


if __name__ == '__main__':
    main()
