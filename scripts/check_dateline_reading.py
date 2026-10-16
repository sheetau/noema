"""Check a convention-only revision; historical interpretation is reviewed separately."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding,validate_hashes
from scripts import check_calendar_dateline as dateline
from scripts.check_labeled_dates import labels,source_document
from scripts.check_class_restricted_roles import semantic_entry
from scripts.compose_dateline_reading import ROOT,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,MEANINGS,build

REPORT=ROOT/'reports/dateline-reading-v1.json'
EVIDENCE='data/dateline-calendar-evidence-v1.json'


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert old.document==new.document
    assert (ROOT/PARENT).read_bytes()==(ROOT/FULL).read_bytes()
    changed=[]
    for name,entry in old.entries.items():
        before=semantic_entry(entry);after=semantic_entry(new.entries[name])
        if before!=after:
            assert name in MEANINGS
            assert after==dict(before,meaning_ja=MEANINGS[name]),name
            changed.append(name)
    assert set(changed)==set(MEANINGS)
    before=load_annotations(ROOT,PARENT_BASIS,'data/gregorian-rules-identifiers-v1.json').show()['entries']
    after=load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries'];assert before==after
    for index in (16,17):
        a=selection_binding(old,[index]);b=selection_binding(new,[index])
        assert a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert a['dependency_sha256']!=b['dependency_sha256'] # Root basis changes provenance.
    return dict(changed_meanings=changed,declarations_and_statements_unchanged=True,
        statements=len(new.document['statements']),identifiers_preserved=True,
        signature_dependency_meanings_preserved=all(semantic_entry(old.entries[n])==semantic_entry(new.entries[n])
            for n in selection_binding(old,[16])['dependencies']),
        manuscript_characters=len((ROOT/FULL).read_text(encoding='utf-8')),additional_manuscript_characters=0)


def checks():
    doc=source_document('hzje',FULL)
    variants=('baseline','different_calendar','different_year','different_year_context',
        'missing_region_name','different_region','different_location_day','different_place_act',
        'different_place_document','different_date_document','different_display_day','different_date_context',
        'missing_occurrence','name_is_place','wrong_month_label','wrong_day_label',
        'ambiguous_month','ambiguous_day','ambiguous_year')
    rows={}
    for variant in variants:
        values=dateline.model(doc,variant);values.update(labels('dateline',variant))
        if variant=='ambiguous_year':
            original=values['hzir']
            values['hzir']=lambda c,p,n,x:original(c,p,n,x) or (c,p,n,x)==('calendar','other',Fraction(1784),'dateline')
        actual=dateline.evaluate(doc,values);assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual
    unknowns=('unknown_year','unknown_assignment','unknown_date','unknown_month_label','unknown_day_label')
    for variant in unknowns:
        values=dateline.model(doc,variant);values.update(labels('dateline',variant))
        try:dateline.evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    return dict(contrasts=rows,unknown_inputs_refused=list(unknowns),
        historical_calendar_identification_proved_by_models=False)


def build_report():
    files=build()
    for p,body in files.items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'))
    validate_hashes(ROOT,evidence['source_sha256'])
    doc=parse(files[FULL])
    for notation in ('compact','full'):
        text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    old=json.loads((ROOT/'reports/gregorian-rules-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT,old['source_sha256'])
    paths=set(old['source_sha256'])|set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(evidence['source_sha256'])|{
        'reports/gregorian-rules-v1.json',EVIDENCE,'docs/dateline-reading-v1.md',
        'scripts/compose_dateline_reading.py','scripts/check_dateline_reading.py','tests/test_dateline_reading.py'}
    alignment=deepcopy(old['alignment'])
    for row in alignment['segments']:
        row.update(status='partial_draft_with_explicit_calendar_reading',
            remaining=['Whole-unit judgments are separate registered reviews; footnote meaning remains incomplete.'])
    return dict(status='checked_convention_revision_historical_reading_is_explicit_judgment',document=FULL,
        structure=structure(),source=checks(),roundtrips=True,
        alignment=alignment, # Preserve draft association; judgments live in the registry.
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Dateline conventions, 19 contrasts, 5 unknown inputs and roundtrips checked')


if __name__=='__main__':main()
