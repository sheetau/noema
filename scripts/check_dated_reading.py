"""Check the text/carrier/announced-issue distinction and shared calendar dates."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.compose_dated_reading import ROOT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure
from scripts import check_unreceived_reference as previous

REPORT=ROOT/'reports/dated-reading-v1.json'
MONTHS=tuple('month'+str(i) for i in range(12))
DAYS=tuple('day'+str(i) for i in range(30))
DOMAIN=tuple(dict.fromkeys(previous.DOMAIN+('read','naming','weekly_issue','weekly_series','weekly_name',
    'monthly_issue','monthly_series','monthly_name','calendar','year')+MONTHS+DAYS))
SCENES=previous.SCENES


def forbidden(*args):raise ValueError('Unknown interpretation')


def source_document(combined=False):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['hzjt','hzju','hzkk'] if combined else ['hzkk'])
    doc['statements']=doc['statements'][-3:] if combined else doc['statements'][-1:]
    return doc


def model_for(doc,variant='baseline'):
    refs=dict(wa='author',hzjr='announcement',hzjm='now',hzjl='note',hzix='calendar',hzjf='year',hzjg='month8',hzjh='day29',
        hzkb='read',hzkc='weekly_issue',hzkd='weekly_series',hzke='weekly_name',hzkf='monthly_issue',hzkg='monthly_series',
        hzkh='monthly_name',hzki='day12',hzkj='naming',hzkl='now' if variant=='same_instant' else 'past')
    if variant=='name_is_series':refs['hzke']='weekly_series'
    if variant=='issue_is_series':refs['hzkc']='weekly_series'
    values={n:(lambda v=v:v) for n,v in refs.items()}
    def occurred(act,ctx):return ctx=='note' and act in ('naming',) if variant=='missing_read' else ctx=='note' and act in ('read','naming')
    def reads(act,reader,text,moment,ctx):
        if variant=='unknown_read':return forbidden()
        return (act,reader,text,moment,ctx)==('read','other' if variant=='other_reader' else 'author',
            'answer' if variant=='read_answer' else 'weekly_issue' if variant=='read_carrier' else 'announcement',
            refs['hzkl'],'branch' if variant=='other_read_context' else 'note')
    def contains(text,issue,ctx):
        return (text,issue,ctx)==('other' if variant=='other_contained_text' else 'announcement',
            'monthly_issue' if variant=='other_carrier' else refs['hzkc'],'note')
    def announces(text,issue,ctx):
        return (text,issue,ctx)==('announcement','weekly_issue' if variant=='other_announced_issue' else 'monthly_issue','note')
    def names(act,name,series,ctx):
        return (act,ctx)==('read' if variant=='names_on_read_act' else 'naming','note') and (name,series) in [
            (refs['hzke'],'weekly_series'),('monthly_name','other' if variant=='other_named_series' else 'monthly_series')]
    def issue_series(issue,series,ctx):
        return ctx=='note' and (issue,series) in [(refs['hzkc'],'weekly_series'),
            ('monthly_issue','weekly_series' if variant=='wrong_issue_series' else 'monthly_series')]
    def issue_date(issue,period,ctx):
        if variant=='unknown_issue_date':return forbidden()
        return ctx=='note' and (issue,period) in [(refs['hzkc'],'day29' if variant=='wrong_issue_day' else 'day12'),
            ('monthly_issue','month9' if variant=='wrong_issue_month' else 'month8')]
    def within(moment,period,ctx):
        if variant=='unknown_day_membership':return forbidden()
        return ctx=='note' and period=='day29' and moment in (
            ('now',) if variant=='read_outside_today' else ('past',) if variant=='anchor_outside_today' else ('past','now'))
    def years(cal,year,label,ctx):
        return (cal,year,label,ctx)==('other' if variant=='other_calendar' else 'calendar','year',
            Fraction(1785 if variant=='other_year' else 1784),'note')
    def months(cal,year,ctx):
        seq=list(MONTHS) if (cal,year,ctx)==('calendar','year','note') else []
        if variant=='other_month' and seq:seq[8],seq[9]=seq[9],seq[8]
        return SequenceValue(tuple(seq),'"individual"')
    def days(cal,month,ctx):
        if variant=='unknown_calendar_days':return forbidden()
        seq=list(DAYS) if (cal,month,ctx)==('calendar','month8','note') else []
        if variant=='wrong_day_number' and seq:seq[12],seq[13]=seq[13],seq[12]
        return SequenceValue(tuple(seq),'"individual"')
    values.update(dg=occurred,hzjv=reads,hzjw=contains,hzjx=announces,hzih=names,hzka=issue_series,hzjy=issue_date,
        hzjz=within,hzir=years,hzis=months,hzit=days)
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:values.get(n,forbidden) for n in required}


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=500000,memoize_definitions=False,memoize_expressions=False)]


def generic_checks():
    doc=source_document();doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q[k rqrp[k hzkb[] k wa[] k hzjr[] k hzkc[] k hzkl[] k hzjl[] p dg p hzjv p hzjw]].')
    count=0
    for bits in product((False,True),repeat=3):
        values=model_for(doc)
        for name,bit in zip(('dg','hzjv','hzjw'),bits,strict=True):
            fn=values[name];values[name]=lambda *args,fn=fn,bit=bit:bit and fn(*args)
        assert evaluate(doc,values)==[all(bits)];count+=1
    return dict(condition_combinations=count)


def source_checks():
    doc=source_document();variants=('baseline','same_instant','missing_read','other_reader','read_answer','read_carrier',
        'other_read_context','other_contained_text','other_carrier','other_announced_issue','names_on_read_act',
        'other_named_series','wrong_issue_series','wrong_issue_day','wrong_issue_month','read_outside_today','anchor_outside_today',
        'other_calendar','other_year','other_month','wrong_day_number','name_is_series','issue_is_series')
    rows={}
    for variant in variants:
        actual=evaluate(doc,model_for(doc,variant));assert actual==[variant in ('baseline','same_instant')],(variant,actual)
        rows[variant]=actual
    for variant in ('unknown_read','unknown_issue_date','unknown_day_membership','unknown_calendar_days'):
        try:evaluate(doc,model_for(doc,variant))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    return dict(contrasts=rows,unknown_inputs_refused=True,separate_or_same_instants_supported=True)


def combined_checks():
    doc=source_document(True);rows={}
    for old_variant,new_variant,expected in [('baseline','baseline',[True,True,True]),
        ('received_past','baseline',[True,False,True]),('baseline','read_answer',[True,True,False]),
        ('received_future','baseline',[True,True,True])]:
        old=previous.model_for(doc,old_variant);new=model_for(doc,new_variant)
        values={n:(value if value is not forbidden else old[n]) for n,value in new.items()}
        for n in ('dg','hzih'):
            a,b=old[n],new[n];values[n]=lambda *args,a=a,b=b:a(*args) or b(*args)
        actual=evaluate(doc,values);assert actual==expected,(old_variant,new_variant,actual)
        rows[old_variant+'/'+new_variant]=actual
    return rows


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS);size=len(old.document['declarations'])
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==21
    added=new.document['declarations'][size:]
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new.document,['rqrp']) and len(lib.entries)==1
    names=load_annotations(ROOT,BASIS,ANNOTATIONS)
    for text,symbol in [('Büsching’schen wöchentlichen Nachrichten','hzke'),('Berlinischen Monatsschrift','hzkh')]:
        assert names.find(text)['matches'][0]['symbol']==symbol
    return dict(previous_statements_preserved=20,previous_declarations_preserved=size,new_primitives=len(PRIMITIVES),
        new_definitions=len(MEANINGS),new_statements=1)


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    text=unit['text'];start=text.index('In den');end=text.index('worin')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=text[start:end],
        status='partial_dated_reading',definitions=['rqrp','rqrm','hzkk'],
        remaining=['Weekly cadence, editorial association, historical calendar identity and whole-unit meaning review remain open.'])])


def build_report():
    files=build()
    for name,body in files.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    generic=generic_checks();source=source_checks();combined=combined_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    facsimile=json.loads((ROOT/'data/author-signature-facsimile-v1.json').read_text(encoding='utf-8'))
    for p,h in facsimile['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(facsimile['source_sha256'])|{
        'data/author-signature-facsimile-v1.json','data/unreceived-reference-identifiers-v1.json',
        'scripts/compose_dated_reading.py','scripts/check_dated_reading.py','scripts/compose_subject_bound_departure.py',
        'scripts/compose_calendar_dateline.py','scripts/compose_unreceived_reference.py','scripts/check_unreceived_reference.py',
        'docs/dated-reading-v1.md','tests/test_dated_reading.py','noema/__init__.py',
        'noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    paths.update('noema/'+n+'.py' for n in ('constructed','constructed_discourse','constructed_semantics','discourse','extraction',
        'grammar','guarded_ranked_semantics','identifiers','meaning_basis','meaning_catalog','ranked','ranked_discourse','script','semantics','diagnostic_short_circuit'))
    parent=(ROOT/load_catalog(ROOT,PARENT_BASIS).document_path).read_text(encoding='utf-8')
    return dict(status='partial_dated_reading_checked',document=FULL,generic=generic,source=source,combined=combined,
        structure=structural,alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len(parent),
            generic_library_characters=len(files[LIBRARY]),annotation_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Includes declarations and references, not a source compression ratio.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Reading object, carrier, announced issue and calendar periods checked')


if __name__=='__main__':main()
