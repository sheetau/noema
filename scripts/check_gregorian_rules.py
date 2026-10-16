"""Check arithmetic certificates and Gregorian labels without a leap-year oracle."""
import argparse
import calendar
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding
from scripts.compose_gregorian_rules import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,FIELDS,MEANINGS,build,closure,certificate,digits

REPORT=ROOT/'reports/gregorian-rules-v1.json'
SCALARS=dict(ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b)


def sequence(values):return SequenceValue(tuple(Fraction(x) for x in values),'"number"')


def evaluate(doc,values,individuals=('item','other'),situations=('actual',)):
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=individuals,situations=situations,
        primitives={n:values[n] for n in required},max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def fixture(root,extra=''):
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'));doc['declarations']=closure(doc,[root]);doc['statements']=[]
    return parse(format_graph(doc,'compact')+extra)


def numeral_checks():
    doc=fixture('rqse','r jdigits[] j[b].q[k rqse[k jdigits[]]].')
    for value in range(32):assert evaluate(doc,dict(jdigits=lambda value=value:sequence([value])))==[True]
    for values in ([],[-1],[32],[Fraction(1,2)],[1,0,Fraction(5,2)]):
        assert evaluate(doc,dict(jdigits=lambda:sequence(values)))==[False],values
    assert evaluate(doc,dict(jdigits=lambda:sequence([0,0,1])))==[True]
    # Compute the expected literal through the grammar, independent of digit folding.
    from scripts.compose_calendar_dateline import num
    value_doc=fixture('rqsf','r jdigits[] j[b].q[e[k rqsf[k jdigits[]]]['+num(1784)+']].')
    assert evaluate(value_doc,dict(SCALARS,jdigits=lambda:sequence([1,23,24])))==[True]
    div=fixture('rqsg','r jvalue[] j[b].r jdivisor[] j[b].r jquotient[] j[b].r jremainder[] j[b].'+
        'q[k rqsg[k jvalue[] k jdivisor[] k jquotient[] k jremainder[]]].')
    variants=dict(valid=(1784,100,17,84),wrong_sum=(1784,100,18,84),too_large_remainder=(1784,100,16,184),zero_divisor=(0,0,0,0))
    for name,values in variants.items():
        model=dict(SCALARS)
        for key,value in zip(('jvalue','jdivisor','jquotient','jremainder'),values):model[key]=lambda value=value:sequence(digits(value))
        assert evaluate(div,model)==[name=='valid'],name
    return dict(valid_digits=32,invalid_numerals=5,leading_zeros_allowed=True,division_contrasts=list(variants),value_1784_checked=True)


def year_fixture(root='rqsi',date=False):
    fields=''.join('r j'+n+'[] j[b].' for n in FIELDS)
    args=' '.join('k j'+n+'[]' for n in FIELDS)
    if date:fields+='r jmonth[] b.r jday[] b.';args+=' k jmonth[] k jday[]'
    return fixture(root,fields+'q[k '+root+'['+args+']].')


def year_model(year,proof=None,month=None,day=None):
    values=dict(SCALARS)
    for name,ds in zip(FIELDS,proof if proof is not None else certificate(year),strict=True):
        values['j'+name]=lambda ds=tuple(ds):sequence(ds)
    if month is not None:values['jmonth']=lambda:Fraction(month)
    if day is not None:values['jday']=lambda:Fraction(day)
    return values


def leap_checks():
    doc=year_fixture();leaps=[]
    for year in range(1600,2000):
        actual=evaluate(doc,year_model(year));assert actual==[calendar.isleap(year)],year
        if actual[0]:leaps.append(year)
    assert len(leaps)==97
    boundary={}
    for year in (1,4,100,400,1784,1900,2000,2100,2400,10000,123456789012345600):
        boundary[str(year)]=evaluate(doc,year_model(year));assert boundary[str(year)]==[calendar.isleap(year)]
    return dict(cycle=[1600,1999],years=400,leap_count=97,boundary_cases=boundary,integer_or_modulo_callbacks_used=False)


def date_checks():
    doc=year_fixture('rqsj',True);count=0
    for year in (1784,1785,1900,2000):
        for month in range(1,13):
            last=calendar.monthrange(year,month)[1]
            for day in (0,1,28,29,30,31,32,last,last+1):
                actual=evaluate(doc,year_model(year,month=month,day=day))
                assert actual==[1<=day<=last],(year,month,day,actual)
                count+=1
    for month,day in ((0,1),(-1,1),(13,1),(Fraction(3,2),1),(9,Fraction(59,2)),(9,-1)):
        assert evaluate(doc,year_model(1784,month=month,day=day))==[False]
    assert evaluate(doc,year_model(0,month=1,day=1))==[False]
    return dict(month_day_cases=count,invalid_noninteger_or_outside_labels=6,zero_year_refused=True)


def corruption_checks():
    valid=year_fixture('rqsh');leap=year_fixture();date=year_fixture('rqsj',True);count=0
    for slot in range(7):
        for bad in ([],[-1],[32],[Fraction(1,2)]):
            proof=certificate(1784);proof[slot]=bad
            for doc in (valid,leap,date):assert evaluate(doc,year_model(1784,proof,1,1))==[False],(slot,bad)
            count+=1
    for slot in range(1,7):
        proof=certificate(1784);proof[slot]=digits(999)
        assert evaluate(valid,year_model(1784,proof))==[False],slot
        assert evaluate(date,year_model(1784,proof,1,1))==[False],slot
    leading=certificate(1784)
    for row in leading:row.insert(0,0)
    assert evaluate(leap,year_model(1784,leading))==[True]
    values=year_model(1784);values['ha']=lambda *args:(_ for _ in ()).throw(ValueError('Unknown arithmetic'))
    try:evaluate(leap,values)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown arithmetic was replaced')
    return dict(invalid_digit_certificates=count,wrong_quotient_or_remainder=6,invalid_certificate_not_a_common_year=True,
        equivalent_leading_zero_certificates=True,unknown_arithmetic_refused=True)


def source_checks():
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'));doc['declarations']=closure(doc,['hzlo']);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q[k hzlo[]].')
    rows={}
    for variant in ('baseline','other_year','other_month','other_day','missing_note','ambiguous_day'):
        values=dict(SCALARS)
        refs=dict(hzix='calendar',hzjf='year',hzjg='month',hzjh='day30',hzki='day13',hziz='dateline',hzjl='note')
        values.update({n:(lambda x=x:x) for n,x in refs.items()})
        values['hzir']=lambda c,y,n,x:(c,y,n)==('calendar','year',Fraction(1785 if variant=='other_year' else 1784)) and x in ('dateline','note')
        values['hzlm']=lambda c,y,m,n,x:(c,y,m,n)==('calendar','year','month',Fraction(10 if variant=='other_month' else 9)) and x in ('dateline','note')
        def days(c,m,d,n,x):
            if variant=='missing_note' and x=='note':return False
            return (c,m)==('calendar','month') and x in ('dateline','note') and (d,n) in (
                {('day30',Fraction(29)),('day13',Fraction(12))} if variant=='other_day' else
                {('day30',Fraction(30)),('day13',Fraction(13))}|({('other',Fraction(30))} if variant=='ambiguous_day' else set()))
        values['hzln']=days
        rows[variant]=evaluate(doc,values,('calendar','year','month','day30','day13','other'),('dateline','note'))
        assert rows[variant]==[variant=='baseline'],(variant,rows[variant])
    return dict(contrasts=rows,source_year_1784_certificate_written_in_noema=True,historical_calendar_not_identified=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS);size=len(old.document['declarations'])
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==23
    added=new.document['declarations'][size:];assert {d['name'] for d in added}==set(MEANINGS)
    assert all(d['kind']=='definition' for d in added)
    for n in old.entries:assert old.entries[n]==new.entries[n],n
    assert selection_binding(old,[16])==selection_binding(new,[16])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(
        ROOT,PARENT_BASIS,'data/labeled-dates-identifiers-v1.json').show()['entries']
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert {d['name'] for d in lib.document['declarations'] if d['kind']=='primitive'}=={'ha','hb','hc'}
    return dict(new_definitions=8,new_primitives=0,previous_statements_preserved=23,old_meanings_and_signature_binding_unchanged=True)


def alignment():
    previous=json.loads((ROOT/'reports/labeled-dates-v1.json').read_text(encoding='utf-8'))['alignment']
    result=deepcopy(previous)
    for row in result['segments']:
        row.update(status='partial_explicit_gregorian_validity_condition',definitions=['rqsh','rqsi','rqsj','rqsk','hzlo'],
            remaining=['Calendar historical identification, epoch/day boundaries and whole-unit meaning review.'])
    return result


def build_report():
    files=build()
    for p,b in files.items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    numerals=numeral_checks();leaps=leap_checks();dates=date_checks();corrupt=corruption_checks();source=source_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    old=json.loads((ROOT/'reports/labeled-dates-v1.json').read_text(encoding='utf-8'))
    paths=set(old['source_sha256'])|set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/labeled-dates-v1.json','scripts/compose_gregorian_rules.py','scripts/check_gregorian_rules.py',
        'tests/test_gregorian_rules.py','docs/gregorian-rules-v1.md',
        'artifacts/gregorian-rules-v1/page-597.png','artifacts/gregorian-rules-v1/page-599.png'}
    for p,h in old['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    return dict(status='gregorian_numeric_rules_checked_not_historical_calendar_identification',document=FULL,
        numerals=numerals,leaps=leaps,dates=dates,corruption=corrupt,source=source,structure=structural,
        reference=dict(url='https://aa.usno.navy.mil/downloads/c15_usb_online.pdf',pages=[597,599],visually_checked=True),
        alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len((ROOT/PARENT).read_text(encoding='utf-8')),
            generic_library_characters=len(files[LIBRARY]),note='Includes definitions and source certificates; no compression claim.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Base-32 certificates and Gregorian year/month/day rules checked')


if __name__=='__main__':main()
