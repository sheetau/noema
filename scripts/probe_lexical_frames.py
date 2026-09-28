"""Connect fixed structure and definition heads, retaining incomplete semantics."""
import argparse
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.lexical_frames import LexicalFrameAnalyzer, assemble_lexical_frames
from noema.lexical_frame_metrics import oracle_queries, assess_lexical_frames, summarize_lexical_frames
from noema.semantics import require
from scripts.prepare_reference_corpus import write
from scripts.train_mention_scope import forbidden_paths

DATA = Path('data/lexical-frames-v1.json')
ROOT = Path('reports/lexical-frames-v1')
CODE = ('noema/lexical_frames.py', 'noema/lexical_frame_metrics.py', 'scripts/probe_lexical_frames.py')


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    rows = json.loads(DATA.read_text(encoding='utf-8'))
    gold_queries = {row['id']: oracle_queries(row) for row in rows}
    require(len(gold_queries) == len(rows), 'Duplicate fixture ID')
    contract = {'fixture_sha256': digest(DATA), 'protocol_sha256': digest('docs/lexical-frames-v1-protocol.md'),
                'code_sha256': {p: digest(p) for p in CODE}}
    if args.verify_only:
        run = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
        require(all(run[k] == v for k, v in contract.items()), 'Lexical frame probe contract changed')
        for path, sha in run['outputs_sha256'].items():
            require(digest(ROOT / path) == sha, 'Lexical frame output changed')
        records = json.loads((ROOT / 'evidence.json').read_text(encoding='utf-8'))
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        records = []
        with forbidden_paths() as guards:
            analyzer = LexicalFrameAnalyzer()
            for i, row in enumerate(rows):
                result = analyzer.analyze(row['text'])
                repeated = i < 4
                if repeated:
                    require(result == analyzer.analyze(row['text']), 'Lexical frames are not repeatable')
                require(result['structure'] == analyzer.structure.analyze(row['text']), 'Joint path changed structure output')
                # Only this separate diagnostic receives human-annotated spans.
                oracle = analyzer.matcher.match(row['text'], gold_queries[row['id']])
                records.append({'id': row['id'], 'result': result, 'oracle': oracle, 'repeated_equal': repeated})
                print('lexical frames', i + 1, '/', len(rows), flush=True)
            metadata, counts = analyzer.metadata, [g.call_count for g in guards]
        write(ROOT / 'evidence.json', records)
    require([r['id'] for r in records] == [r['id'] for r in rows], 'Saved lexical inventory differs')
    cases, oracle_counts = [], {'known': 0, 'known_correct': 0, 'unknown': 0, 'unknown_forced_known': 0}
    for row, record in zip(rows, records, strict=True):
        result = record['result']
        replay = assemble_lexical_frames(result['structure'], result['concept_matches'])
        require(all(result[k] == v for k, v in replay.items()), 'Saved lexical assembly changed')
        cases.append(assess_lexical_frames(row, result))
        require(len(record['oracle']) == len(gold_queries[row['id']]), 'Oracle query count differs')
        for gold, prediction in zip(gold_queries[row['id']], record['oracle'], strict=True):
            require((gold['start'], gold['end']) == (prediction['start'], prediction['end']), 'Oracle positions changed')
            known = gold['expected'] is not None
            oracle_counts['known' if known else 'unknown'] += 1
            oracle_counts['known_correct' if known else 'unknown_forced_known'] += (
                prediction['top'][0]['concept'] == gold['expected'] if known else prediction['top'][0]['concept'] is not None)
    report = {'language': 'ja', 'summary': summarize_lexical_frames(cases), 'oracle_diagnostic': oracle_counts, 'cases': cases}
    if args.verify_only:
        require(report == json.loads((ROOT / 'evaluation.json').read_text(encoding='utf-8')), 'Lexical frame metrics changed')
        write(ROOT / 'verification.json', {'replayed': len(rows), **contract})
    else:
        write(ROOT / 'evaluation.json', report)
        write(ROOT / 'run.json', {**contract, 'metadata': metadata, 'training': False, 'model_or_threshold_selection': False,
              'forbidden_path_calls': counts, 'raw_structure_equal': len(rows),
              'outputs_sha256': {p: digest(ROOT / p) for p in ('evidence.json', 'evaluation.json')}})
    print(json.dumps({k: report[k] for k in ('summary', 'oracle_diagnostic')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
