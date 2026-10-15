"""Verify whole-draft dependency extraction without claiming source equivalence."""
import argparse
import hashlib
import json
import subprocess
import sys

from noema.closed_document import verify_certificate, prune_document
from noema.constructed import parse, format_graph
from noema.manuscript_obligations import audit
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_manuscript_pruning import ROOT, SOURCES, MANIFEST, REVIEW, BASIS, PREVIOUS_REVIEW, PREVIOUS_BASIS, ROOTS, alignment_inventory, build

REPORT = ROOT/'reports/manuscript-pruning-v1.json'
AUDIT = ROOT/'reports/kant-manuscript-obligations-v12.json'


def build_report():
    files=build()
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in files.items())
    manifest=json.loads(files[MANIFEST]);documents={}
    for work,(source,path) in SOURCES.items():
        record=manifest['works'][work]
        original=parse((ROOT/source).read_text(encoding='utf-8'));doc=parse(files[path])
        extraction=verify_certificate(original,doc,record['certificate'])
        assert prune_document(doc,roots=record['source_aligned_roots']).document==doc
        assert record['document_sha256']==hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        for notation in ('full','compact'):
            text=format_graph(doc,notation)
            assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        output=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],
            check=True,capture_output=True,text=True,encoding='utf-8')
        assert json.loads(output.stdout)==doc
        documents[path]=dict(source=source,statements=len(doc['statements']),
            declarations_before=len(original['declarations']),declarations_after=len(doc['declarations']),
            removed_declarations=len(extraction.removed_symbols),retained_primitives=len(record['certificate']['retained_primitives']),
            before_characters=record['before_characters'],after_characters=record['after_characters'],
            reduction_percent=record['reduction_percent'],all_statement_asts_preserved=True,
            source_aligned_roots_preserved=len(record['source_aligned_roots']),
            source_aligned_symbols_absent_from_input=record['source_aligned_symbols_absent_from_input'],
            all_retained_declaration_asts_preserved=True,roundtrips=True,cli_parse=True)
    review=json.loads(files[REVIEW])
    units=json.loads((ROOT/review['source_units']).read_text(encoding='utf-8'))
    unit=next(u for u in units['units'] if u['id']==review['unit'])
    inspected=audit(parse(files[review['document']]),unit,review)
    assert all(not row['unconnected_candidate_roots'] for row in inspected['obligations'])
    assert len(inspected['templates'][0]['parameters'])==8 and not inspected['semantic_completion']
    audit_basis(parse(files[SOURCES['einstein-1905'][1]]),json.loads(files[BASIS]))
    paths=set(files)|{s for s,p in SOURCES.values()}|set(review['evidence_files'])|{
        PREVIOUS_REVIEW,PREVIOUS_BASIS,ROOTS,review['source_units'],
        'noema/closed_document.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/extraction.py','noema/meaning_basis.py','noema/manuscript_obligations.py',
        'scripts/compose_manuscript_pruning.py','scripts/check_manuscript_pruning.py',
        'tests/test_closed_document.py','docs/manuscript-pruning-v1.md'}
    paths.update(alignment_inventory()['reports_sha256'])
    report=dict(status=manifest['status'],documents=documents,
        semantic_completion=False,adds_new_text_coverage=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        limitations=manifest['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
    inspected.update(document=review['document'],input_sha256=report['source_sha256'])
    return report,inspected


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true');args=parser.parse_args(argv)
    report,inspected=build_report()
    outputs=((REPORT,report),(AUDIT,inspected))
    if args.verify_only:
        for path,value in outputs:assert json.loads(path.read_text(encoding='utf-8'))==value,path
    else:
        assert not any(path.exists() for path,value in outputs),'Report already exists; use --verify-only'
        for path,value in outputs:
            with path.open('x',encoding='utf-8',newline='\n') as stream:
                stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    for path,value in report['documents'].items():
        print(path,value['statements'],'statements preserved;',value['reduction_percent'],'percent shorter')
    print('All source-linked candidates remain connected; 8 template parameters remain open')


if __name__=='__main__':main()
