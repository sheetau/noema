"""Content-based reuse of relevant evidence, with independent resumable units."""
import argparse, json
from pathlib import Path
from scripts.general_language_cases import cases
from scripts.general_language import entries, INVENTORY
from scripts.two_work_inventory import ROOT, read, sha
from scripts.two_work_fastparse import parse_source
from scripts.long_run import LongRun, atomic_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    selected=cases(); catalog=read(INVENTORY)
    paths={INVENTORY,'scripts/general_language_review.py','scripts/general_language_cases.py','scripts/two_work_fastparse.py',
           'noema/constructed_discourse.py','scripts/long_run.py'}
    for row in selected:
        paths.add(row['native'])
        if row['evidence']:
            paths.add(row['evidence']);paths.update(read(row['evidence']).get('source_sha256',{}))
    pins={path:sha(path) if (ROOT/path).is_file() else None for path in sorted(paths)}
    with LongRun(ROOT/args.run,dict(source_sha256=pins,output=args.out),resume=args.resume) as run:
        results=[]
        for i,row in enumerate(selected):
            run.emit('progress',stage=row['label'],completed=i,total=len(selected))
            def check():
                try:
                    document=parse_source((ROOT/row['native']).read_text(encoding='utf-8'))
                    unknown=set(row['entries'])-set(catalog['entries'])
                    if unknown:raise ValueError('Unpublished entries: '+str(unknown))
                    expected=read(row['evidence']).get('source_sha256',{}) if row['evidence'] else {}
                    differences=[path for path,digest in expected.items() if pins.get(path)!=digest]
                    return dict(**row,syntax='passed',declarations=len(document['declarations']),statements=len(document['statements']),
                        retained_evidence='input-identical' if expected and not differences else 'inputs-changed' if differences else 'separate-targeted-check',
                        native_in_evidence=row['native'] in expected,changed_inputs=differences)
                except Exception as error:return dict(**row,syntax='failed',error=str(error))
            results.append(run.step(row['id'],row,check))
        report=dict(schema='noema-general-language-review-1',source_sha256=pins,cases=results,
                    boundary='構文検査・既存証拠の入力照合。応用の設計例を新しい自然文の意味審査と数えない。',
                    failures=[r['id'] for r in results if r['syntax']!='passed'],
                    changed_evidence=[r['id'] for r in results if r.get('changed_inputs')])
        atomic_json(ROOT/args.out,report)
        print(json.dumps(dict(cases=len(results),failures=report['failures'],changed_evidence=report['changed_evidence']),ensure_ascii=False))


if __name__=='__main__':main()
