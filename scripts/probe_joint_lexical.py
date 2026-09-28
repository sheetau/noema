"""Compare fixed independent and constrained joint decisions on raw Japanese text."""
import argparse
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.joint_lexical import JointLexicalAnalyzer, decode_joint
from noema.lexical_frame_metrics import oracle_queries, assess_lexical_frames, summarize_lexical_frames
from noema.semantics import require
from scripts.prepare_reference_corpus import write
from scripts.train_mention_scope import forbidden_paths

ROOT = Path('reports/joint-lexical-v2')
RAW = Path('artifacts/joint-lexical-v2')
FIXTURES = {'regression': 'data/lexical-frames-v1.json', 'confirmation': 'data/joint-lexical-v2.json'}
SCORE_TOLERANCE = 1e-5
# Include the transitive local inference code, schema, and weights' selection records.
CODE = tuple(str(p).replace('\\', '/') for p in sorted(Path('noema').glob('*.py'))) + (
    'scripts/probe_joint_lexical.py', 'scripts/train_mention_scope.py',
    'scripts/prepare_reference_corpus.py', 'docs/joint-lexical-v2-protocol.md',
    'reports/event-gate-v6/selection.json', 'reports/multi-frame-v5/selection.json',
    'reports/shared-matcher-v1/run.json', 'reports/shared-matcher-v1/linear-training.json',
    'reports/shared-matcher-v1/definitions.json',
) + tuple(str(p).replace('\\', '/') for p in sorted(Path('noema/resources').glob('*.json')))


def evaluate(groups, records):
    reports = {}
    for name, rows in groups.items():
        cases = {'baseline': [], 'joint': []}
        for row, record in zip(rows, records[name], strict=True):
            require(record['id'] == row['id'], 'Joint record ID differs')
            result = record['result']
            require(decode_joint(result['baseline'], result['concept_table'], result['role_logits']) == result['joint'],
                    'Joint score replay differs')
            for method in cases:
                cases[method].append(assess_lexical_frames(row, result[method]))
        reports[name] = {method: {'summary': summarize_lexical_frames(values), 'cases': values}
                         for method, values in cases.items()}
        reports[name]['core_changes'] = {
            'improved': [a['id'] for a, b in zip(cases['baseline'], cases['joint'], strict=True) if not a['core_frames_exact'] and b['core_frames_exact']],
            'regressed': [a['id'] for a, b in zip(cases['baseline'], cases['joint'], strict=True) if a['core_frames_exact'] and not b['core_frames_exact']]}
        reports[name]['cross_frame_conflict_documents'] = sum(bool(r['result']['joint']['cross_frame_concept_conflicts']) for r in records[name])
    return reports


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    groups = {name: json.loads(Path(path).read_text(encoding='utf-8')) for name, path in FIXTURES.items()}
    for rows in groups.values():
        require(len(rows) == len({r['id'] for r in rows}), 'Duplicate fixture ID')
        for row in rows:
            oracle_queries(row)  # Validate evaluation annotations; never passed to inference.
    contract = {'source_sha256': {p: digest(p) for p in (*CODE, *FIXTURES.values())}}
    records = {name: [] for name in groups}
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(run['source_sha256'] == contract['source_sha256'], 'Joint experiment sources changed')
        for p, sha in run['outputs_sha256'].items():
            require(digest(p) == sha, 'Joint evidence changed')
        for name, rows in groups.items():
            records[name] = [json.loads((RAW / f'{name}-{row["id"]}.json').read_text(encoding='utf-8')) for row in rows]
    else:
        prior_root = Path('reports/lexical-frames-v1')
        prior_run = json.loads((prior_root / 'run.json').read_text(encoding='utf-8'))
        for p, sha in prior_run['outputs_sha256'].items():
            require(digest(prior_root / p) == sha, 'Independent baseline evidence changed')
        prior = {r['id']: r['result'] for r in json.loads((prior_root / 'evidence.json').read_text(encoding='utf-8'))}
        ROOT.mkdir(parents=True, exist_ok=False)
        RAW.mkdir(parents=True, exist_ok=False)
        write(ROOT / 'protocol.json', contract)  # Persist the contract before any predictions.
        with forbidden_paths() as guards:
            analyzer = JointLexicalAnalyzer()
            for name, rows in groups.items():
                for i, row in enumerate(rows):
                    result = analyzer.analyze(row['text'])
                    table = result['concept_table']
                    lookup = {(s['start'], s['end']): values for s, values in zip(table['spans'], table['scores'], strict=True)}
                    maximum_delta = 0.
                    for match in result['baseline']['concept_matches']:
                        values = lookup[match['start'], match['end']]
                        ranked = sorted(zip(table['ids'], values, strict=True), key=lambda item: (-item[1], item[0]))[:3]
                        require([c for c, _ in ranked] == [v['concept'] for v in match['top']], 'Full-score ranking differs')
                        maximum_delta = max(maximum_delta, *(abs(score - old['score']) for (_, score), old in zip(ranked, match['top'], strict=True)))
                    require(maximum_delta <= SCORE_TOLERANCE, 'Full-score batch changed concept scores')
                    repeated = name == 'regression' and i < 4
                    if repeated:
                        require(result == analyzer.analyze(row['text']), 'Joint inference repetition differs')
                    require(result['baseline']['structure'] == analyzer.base.structure.analyze(row['text']), 'Joint path changed raw structure')
                    if name == 'regression':
                        require(result['baseline'] == prior[row['id']], 'Independent baseline changed')
                    record = {'id': row['id'], 'result': result, 'repeated_equal': repeated, 'structure_equal': True,
                              'common_top3_max_score_delta': maximum_delta}
                    records[name].append(record)
                    write(RAW / f'{name}-{row["id"]}.json', record)
                    print(name, i + 1, '/', len(rows), flush=True)
            metadata, calls = analyzer.metadata, [g.call_count for g in guards]
        require(not any(calls), 'Forbidden inference path used')
    report = evaluate(groups, records)
    if args.verify_only:
        require(report == json.loads((ROOT / 'evaluation.json').read_text(encoding='utf-8')), 'Joint evaluation replay differs')
        write(ROOT / 'verification.json', {'replayed': sum(map(len, records.values())), **contract})
    else:
        write(ROOT / 'evaluation.json', report)
        paths = [ROOT / 'protocol.json', ROOT / 'evaluation.json', *sorted(RAW.glob('*.json'))]
        write(ROOT / 'run.json', {**contract, 'metadata': metadata, 'forbidden_path_calls': calls,
              'independent_regression_equal': 18, 'raw_structure_equal': 32, 'repeated_equal': 4,
              'training': False, 'model_or_threshold_selection': False,
              'outputs_sha256': {str(p).replace('\\', '/'): digest(p) for p in paths}})
    print(json.dumps({name: {k: v['summary'] for k, v in value.items() if k in ('baseline', 'joint')}
                      for name, value in report.items()}, indent=2), flush=True)


if __name__ == '__main__':
    main()
