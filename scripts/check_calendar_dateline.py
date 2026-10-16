"""Check calendar positions and dateline bindings without a translation model."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import subprocess
import sys

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, SequenceValue
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.compose_calendar_dateline import ROOT, PARENT_BASIS, FULL, LIBRARY, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, build, closure, num

REPORT = ROOT/'reports/calendar-dateline-v1.json'
MONTHS = tuple('month'+str(i) for i in range(12))
DAYS = tuple('day'+str(i) for i in range(30))
DOMAIN = tuple(dict.fromkeys(('day29','year','month8','calendar','act','doc','place','region','place_name','region_name','other')+MONTHS+DAYS))
SCENES = ('dateline','other')


def forbidden(*args):
    raise ValueError('Unknown primitive interpretation')


def source_document():
    doc = parse((ROOT/FULL).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc,['hzje']); doc['statements'] = doc['statements'][-1:]
    return doc


def model(doc, variant='baseline'):
    values = {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    refs = dict(hzix='calendar', hziy='act', hzik='doc', hziz='dateline', hzja='place_name', hzjb='place', hzjc='region_name', hzjd='region', hzjf='year', hzjg='month8', hzjh='day29')
    if variant == 'name_is_place': refs['hzja']='place'
    values.update({name:(lambda value=value:value) for name,value in refs.items() if name in values})

    def year(calendar, period, label, context):
        if variant == 'unknown_year': return forbidden()
        return (calendar,period,label,context)==('other' if variant=='different_calendar' else 'calendar','year',
            Fraction(1785 if variant=='different_year' else 1784),'other' if variant=='different_year_context' else 'dateline')

    def months(calendar, period, context):
        if variant == 'unknown_months': return forbidden()
        if (calendar,period,context)!=('calendar','year','dateline'): return SequenceValue((), '"individual"')
        seq = list(MONTHS)
        if variant=='different_month': seq[8],seq[9]=seq[9],seq[8]
        if variant=='short_months': seq=seq[:8]
        return SequenceValue(tuple(seq),'"individual"')

    def days(calendar, month, context):
        if variant == 'unknown_days': return forbidden()
        seq = DAYS if (calendar,month,context)==('calendar','month8','dateline') else ()
        if variant=='short_days': seq=seq[:29]
        if variant=='different_day': seq=DAYS[:28]+('day29','day28') if seq else ()
        return SequenceValue(seq,'"individual"')

    def assigns(act, name, target, context):
        if variant=='unknown_assignment': return forbidden()
        if variant=='missing_region_name' and name=='region_name': return False
        return act=='act' and context=='dateline' and (name,target) in [(refs['hzja'],'place'),('region_name','region')]

    def location(place, region, day, context):
        return (place,region,day,context)==('place','other' if variant=='different_region' else 'region',
            'day28' if variant=='different_location_day' else 'day29','dateline')

    def display_place(act, document, place, context):
        return (act,document,place,context)==('other' if variant=='different_place_act' else 'act',
            'other' if variant=='different_place_document' else 'doc','place','dateline')

    def display_date(act, document, day, context):
        if variant=='unknown_date': return forbidden()
        return (act,document,day,context)==('act','other' if variant=='different_date_document' else 'doc',
            'day28' if variant=='different_display_day' else 'day29','other' if variant=='different_date_context' else 'dateline')

    values.update(hzir=year,hzis=months,hzit=days,hzih=assigns,hziw=location,hziu=display_place,hziv=display_date,
        dg=lambda act,context:variant!='missing_occurrence' and (act,context)==('act','dateline'))
    return {name:value for name,value in values.items() if name in {d['name'] for d in doc['declarations'] if d['kind']=='primitive'}}


def evaluate(doc, values):
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def date_fixture(month=8, day=29):
    doc=source_document();doc['statements']=[]
    def number(value):
        value=Fraction(value)
        from noema.grammar import number_word
        return 'n '+('u' if value<0 else 'p')+' '+number_word(abs(value.numerator))+' '+number_word(value.denominator)
    return parse(format_graph(doc,'compact')+'r jday[] a.q[k rqrm[k hzix[] k hzjf[] k hzjg[] k jday[] '+num(1784)+' '+number(month)+' '+number(day)+' k hziz[] p hzir p hzis p hzit]].')


def checks():
    doc=source_document()
    variants=('baseline','different_calendar','different_year','different_year_context','different_month','short_months',
        'short_days','different_day','missing_region_name','different_region','different_location_day',
        'different_place_act','different_place_document','different_date_document','different_display_day',
        'different_date_context','missing_occurrence','name_is_place')
    results={}
    for variant in variants:
        actual=evaluate(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual)
        results[variant]=actual
    unknowns=('unknown_year','unknown_months','unknown_days','unknown_assignment','unknown_date')
    for variant in unknowns:
        try: evaluate(doc,model(doc,variant))
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(variant)
    positions=[]
    for month,day,expected in [(8,29,True),(-1,29,False),(Fraction(17,2),29,False),(12,29,False),
                               (8,-1,False),(8,Fraction(59,2),False),(8,30,False),(8,28,False)]:
        fixture=date_fixture(month,day);values=model(fixture);values['jday']=lambda:'day29'
        actual=evaluate(fixture,values);assert actual==[expected],(month,day,actual)
        positions.append(dict(month_index=str(month),day_index=str(day),result=actual[0]))
    # A changed date is expressible: position 28 points to day28, not day29.
    fixture=date_fixture(8,28);values=model(fixture);values['jday']=lambda:'day28'
    assert evaluate(fixture,values)==[True]
    return dict(source_contrasts=results,unknown_inputs_refused=list(unknowns),positions=positions,
        adjacent_date_expressible=True,uncached=True)


def structure():
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    size=len(before.document['declarations']);added=after.document['declarations'][size:]
    assert after.document['declarations'][:size]==before.document['declarations']
    assert after.document['statements'][:-1]==before.document['statements']
    assert len(after.document['statements'])==18
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(after.document,['rqrm']) and len(lib.entries)==1
    names=load_annotations(ROOT,BASIS,ANNOTATIONS)
    for text,symbol in [('Königsberg','hzja'),('Preußen','hzjc'),('Immanuel Kant','hzif')]:
        assert names.find(text)['matches'][0]['symbol']==symbol
    return dict(previous_declarations_preserved=size,previous_statements_preserved=17,new_statements=1,
        new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),generic_calendar_has_no_primitives=True)


def source_unit():
    return next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0019')


def build_report():
    files=build()
    for name,body in files.items(): assert (ROOT/name).read_text(encoding='utf-8')==body,name
    finite=checks();structural=structure();unit=source_unit()
    for path in (FULL,LIBRARY):
        doc=parse(files[path])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    facsimile=json.loads((ROOT/'data/author-signature-facsimile-v1.json').read_text(encoding='utf-8'))
    for path,expected in facsimile['source_sha256'].items(): assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(facsimile['source_sha256'])|{
        'scripts/compose_calendar_dateline.py','scripts/check_calendar_dateline.py','scripts/compose_subject_bound_departure.py',
        'tests/test_calendar_dateline.py','docs/calendar-dateline-v1.md','data/author-signature-facsimile-v1.json',
        'data/conditional-imputation-identifiers-v1.json',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    # Pin the implementation used here, independent of modules imported by a
    # caller (for example a review builder or pytest plugin).
    paths.update('noema/'+name+'.py' for name in (
        'constructed','constructed_discourse','constructed_semantics','discourse','extraction','grammar',
        'guarded_ranked_semantics','identifiers','meaning_basis','meaning_catalog','ranked','ranked_discourse',
        'script','semantics'))
    parent_body=(ROOT/load_catalog(ROOT,PARENT_BASIS).document_path).read_text(encoding='utf-8')
    return dict(status='partial_calendar_address_and_dateline_checked',document=FULL,finite=finite,structure=structural,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],source=unit['text'],
            status='partial_calendar_dateline',definitions=['rqrm','hzje'],remaining=['Historical calendar identification and whole-unit semantic review remain open.'])]),
        roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len(parent_body),
            generic_library_characters=len(files[LIBRARY]),annotation_file_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Declarations, local references and identifier forms are counted separately; no compression claim.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Calendar positions, dateline bindings and source range checked')


if __name__=='__main__':main()
