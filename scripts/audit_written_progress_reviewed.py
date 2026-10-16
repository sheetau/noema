"""Connect registered unit review judgments to the conservative draft audit."""
import argparse
from copy import deepcopy
import json

from noema.semantic_reviews import load_reviews,digest,require
from scripts.audit_written_progress_extended import ROOT,REPORT,build_report as build_partial_report

INDEX='data/semantic-review-index-v1.json'


def apply_reviews(partial,reviewed):
    report=deepcopy(partial)
    require(set(reviewed['works'])==set(report['works']),'Review works differ from source inventory')
    for work,rows in reviewed['works'].items():
        target=report['works'][work]
        require(target['verified_semantic_units']==0,'Base report already contains completion claims')
        by_id={u['unit']:u for u in target['units']}
        require(len(by_id)==target['author_unit_count'],'Aggregate unit count differs')
        seen=set()
        for row in rows:
            require(row['unit'] in by_id and row['unit'] not in seen,'Unknown or repeated reviewed aggregate unit')
            seen.add(row['unit']);by_id[row['unit']]['semantic_review']=row
        target['verified_semantic_units']=len(seen)
        target['verified_semantic_percent']=round(100*len(seen)/target['author_unit_count'],2)
    for name,value in reviewed['source_sha256'].items():
        require(name not in report['source_sha256'] or report['source_sha256'][name]==value,'Review input conflicts with draft audit')
        report['source_sha256'][name]=value
    report['status']='audited_draft_inventory_with_explicit_review_judgments_not_universal_expression_rate'
    report['method']['semantic_metric_limit']='Counts explicit whole-unit reviewer judgments for the pinned active manuscripts under their stated readings. Provenance is checked; semantic equivalence is not automatically proved. Units have unequal length.'
    report['semantic_reviews']={k:v for k,v in reviewed.items() if k!='source_sha256'}
    return report


def build_report(root=ROOT,index_path=INDEX):
    # Validate reviews first; do not spend minutes rebuilding a draft audit if
    # the active review/document registration is already stale.
    reviewed=load_reviews(root,index_path)
    for work,rows in reviewed['works'].items():
        for row in rows:
            require(row['source_inventory']=='artifacts/written-units-v1/'+work+'.json',
                'Reviewed source is not the inventory used by the draft audit')
    report=apply_reviews(build_partial_report(root),reviewed)
    for name in ('scripts/audit_written_progress_reviewed.py','noema/semantic_reviews.py',
        'tests/test_semantic_reviews.py','docs/unit-semantic-review-v1.md'):
        report['source_sha256'][name]=digest((root/name).read_bytes())
    return report


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--index',default=INDEX);cli.add_argument('--verify-only',action='store_true')
    args=cli.parse_args();report=build_report(index_path=args.index)
    if args.verify_only:require(json.loads(REPORT.read_text(encoding='utf-8'))==report,'Progress report differs')
    else:
        with REPORT.open('w',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Draft ranges and registered whole-unit review judgments audited separately')


if __name__=='__main__':main()
