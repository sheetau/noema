"""Distinguish an announced issue's answer from a merely mentioned outside text."""
import argparse
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_dated_reading as reading
from scripts import check_unreceived_reference as receipt
from scripts.check_labeled_dates import labels
from scripts.check_class_restricted_roles import semantic_entry
from scripts.compose_subject_bound_departure import closure
from scripts.compose_announced_answer import ROOT,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,build,membership

REPORT=ROOT/'reports/announced-answer-v1.json'


def document(path=FULL,combined=False):
    doc=parse((ROOT/path).read_text(encoding='utf-8'))
    roots=['hzjt','hzju','hzkk'] if combined else ['hzkk']
    doc['declarations']=closure(doc,roots)
    doc['statements']=[s for s in doc['statements'] if s.get('body',{}).get('symbol') in roots]
    assert len(doc['statements'])==len(roots)
    return doc


def model(doc,variant='baseline',received='baseline'):
    old=receipt.model_for(doc,received);new=reading.model_for(doc,variant)
    values={n:(v if v is not reading.forbidden else old[n]) for n,v in new.items()}
    for n in ('dg','hzih'):
        a,b=old[n],new[n]
        values[n]=lambda *args,a=a,b=b:a(*args) or b(*args)
    values.update(labels('note',variant));base=values['hzjw']
    row=('answer','monthly_issue','note')
    if variant=='answer_in_weekly_only':row=('answer','weekly_issue','note')
    if variant=='other_answer':row=('other','monthly_issue','note')
    if variant=='other_issue':row=('answer','other','note')
    if variant=='other_context':row=('answer','monthly_issue','branch')
    if variant=='reversed_membership':row=('monthly_issue','answer','note')
    if variant=='announcement_in_monthly':row=('announcement','monthly_issue','note')
    def contains(text,issue,context):
        if (text,issue,context)==('answer','monthly_issue','note') and variant=='unknown_membership':return reading.forbidden()
        return base(text,issue,context) or variant!='missing_membership' and (text,issue,context)==row
    values['hzjw']=contains
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


def checks():
    old=document(PARENT);new=document();rows={}
    negatives=('missing_membership','answer_in_weekly_only','other_answer','other_issue','other_context','reversed_membership','announcement_in_monthly')
    for variant in ('baseline',*negatives):
        a=reading.evaluate(old,model(old,variant));b=reading.evaluate(new,model(new,variant))
        assert a==[True] and b==[variant=='baseline'],(variant,a,b)
        rows[variant]=dict(before=a,after=b)
    assert reading.evaluate(old,model(old,'unknown_membership'))==[True]
    try:reading.evaluate(new,model(new,'unknown_membership'))
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown membership must not be guessed')
    preserved={}
    for variant in ('same_instant','missing_read','other_reader','read_answer','read_carrier','other_read_context',
        'other_contained_text','other_carrier','other_announced_issue','names_on_read_act','other_named_series',
        'wrong_issue_series','wrong_issue_day','wrong_issue_month','read_outside_today','anchor_outside_today',
        'other_calendar','other_year','name_is_series','issue_is_series','wrong_month_label','wrong_day_label','ambiguous_month','ambiguous_day'):
        actual=reading.evaluate(new,model(new,variant));assert actual==[variant=='same_instant'],(variant,actual)
        preserved[variant]=actual
    combined=document(combined=True);combinations={}
    for variant,received,expected in [('baseline','baseline',[True,True,True]),('missing_membership','baseline',[True,True,False]),
        ('baseline','received_past',[True,False,True]),('read_answer','baseline',[True,True,False]),
        ('baseline','received_future',[True,True,True])]:
        actual=reading.evaluate(combined,model(combined,variant,received));assert actual==expected,(variant,received,actual)
        combinations[variant+'/'+received]=actual
    return dict(old_accepts_seven_missing_or_misbound_memberships=rows,unknown_membership_refused=True,
        preserved_contrasts=preserved,citation_nonreceipt_reading=combinations)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    before={d['name']:d for d in old.document['declarations']};after={d['name']:d for d in new.document['declarations']}
    assert before.keys()==after.keys()
    assert [n for n in before if before[n]!=after[n]]==['hzkk']
    assert after['hzkk']['body']==dict(kind='and',arguments=[before['hzkk']['body'],membership()])
    assert old.document['statements']==new.document['statements']
    for n in before:
        if n!='hzkk':assert semantic_entry(old.entries[n])==semantic_entry(new.entries[n]),n
    for index in (16,17):
        a=selection_binding(old,[index]);b=selection_binding(new,[index])
        assert a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        for n in a['dependencies']:assert semantic_entry(old.entries[n])==semantic_entry(new.entries[n]),n
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(
        ROOT,PARENT_BASIS,'data/dateline-reading-identifiers-v1.json').show()['entries']
    return dict(changed_definitions=['hzkk'],new_primitives=0,new_declarations=0,statements=23,
        reviewed_unit_meanings_preserved=True,identifiers_preserved=True,
        additional_manuscript_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    files=build()
    for p,b in files.items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    doc=parse(files[FULL])
    for notation in ('compact','full'):
        text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    prior=json.loads((ROOT/'reports/dateline-reading-v1.json').read_text(encoding='utf-8'))
    evidence=json.loads((ROOT/'data/announced-answer-evidence-v1.json').read_text(encoding='utf-8'))
    for record in (prior,evidence):validate_hashes(ROOT,record['source_sha256'])
    paths=set(prior['source_sha256'])|set(evidence['source_sha256'])|set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/dateline-reading-v1.json','data/announced-answer-evidence-v1.json','docs/announced-answer-v1.md',
        'scripts/compose_announced_answer.py','scripts/check_announced_answer.py','tests/test_announced_answer.py'}
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    start=unit['text'].index('die Anzeige');end=unit['text'].index('angeführt wird.')+len('angeführt wird.')
    alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=unit['text'][start:end],
        status='partial_cited_answer_in_announced_issue',definitions=['hzjt','hzkk'],
        remaining=['Whole footnote semantics, including naming and social register, remain under review.'])])
    return dict(status='announced_issue_membership_checked_partial_footnote',document=FULL,structure=structure(),checks=checks(),
        roundtrips=True,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Answer membership, seven old counterexamples, 24 regressions and five combined models checked')


if __name__=='__main__':main()
