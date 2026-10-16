"""Check labeled dates, skipped labels and unique parent-scoped addressing."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding
from scripts import check_calendar_dateline as dateline
from scripts import check_dated_reading as reading
from scripts.check_class_restricted_roles import semantic_entry
from scripts.compose_labeled_dates import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,build,closure,replace_dates

REPORT=ROOT/'reports/labeled-dates-v1.json'


def source_document(name,path=FULL):
    doc=parse((ROOT/path).read_text(encoding='utf-8'));doc['declarations']=closure(doc,[name])
    doc['statements']=[s for s in doc['statements'] if s.get('body',{}).get('symbol')==name]
    assert len(doc['statements'])==1
    return doc


def labels(context,variant='baseline'):
    def months(calendar,year,month,label,ctx):
        if variant=='unknown_month_label':return dateline.forbidden()
        return (calendar,year,label,ctx)==('calendar','year',Fraction(9),context) and month in (
            ('month8','other') if variant=='ambiguous_month' else ('month9',) if variant=='wrong_month_label' else ('month8',))
    def days(calendar,month,day,label,ctx):
        if variant=='unknown_day_label':return dateline.forbidden()
        if (calendar,month,ctx)!=('calendar','month8',context):return False
        rows={('day12',Fraction(13)),('day29',Fraction(30))}
        if variant=='wrong_day_label':rows={('day13',Fraction(13)),('day28',Fraction(30))}
        if variant=='ambiguous_day':rows.add(('other',Fraction(30)))
        return (day,label) in rows
    return dict(hzlm=months,hzln=days)


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'r jcal[] a.r jyear[] a.r jmonth[] a.r jday[] a.r jctx[] d.'+
        'r jyears[a a b d] c.r jmonths[a a a b d] c.r jdays[a a a b d] c.'+
        'q[k rqsd[k jcal[] k jyear[] k jmonth[] k jday[] '+dateline.num(1784)+' '+dateline.num(9)+' '+dateline.num(30)+' k jctx[] p jyears p jmonths p jdays]].')
    count=0
    for bits in product((False,True),repeat=6):
        present=bits[:3];duplicate=bits[3:]
        def assigned(axis,period,witness):return present[axis] and period==witness or duplicate[axis] and period=='other'
        values=dict(jcal=lambda:'calendar',jyear=lambda:'year',jmonth=lambda:'month8',jday=lambda:'day29',jctx=lambda:'dateline',
            jyears=lambda c,p,n,x:(c,n,x)==('calendar',Fraction(1784),'dateline') and assigned(0,p,'year'),
            jmonths=lambda c,y,p,n,x:(c,y,n,x)==('calendar','year',Fraction(9),'dateline') and assigned(1,p,'month8'),
            jdays=lambda c,m,p,n,x:(c,m,n,x)==('calendar','month8',Fraction(30),'dateline') and assigned(2,p,'day29'))
        assert dateline.evaluate(doc,values)==[all(present) and not any(duplicate)],bits
        count+=1
    return dict(combinations=count,positive_assignments_and_uniqueness_checked=True)


def source_checks():
    rows={}
    for symbol,previous,context,variants in (
        ('hzje',dateline,'dateline',('baseline','different_calendar','different_year','different_year_context',
            'missing_region_name','different_region','different_location_day','different_place_act','different_place_document',
            'different_date_document','different_display_day','different_date_context','missing_occurrence','name_is_place')),
        ('hzkk',reading,'note',('baseline','same_instant','missing_read','other_reader','read_answer','read_carrier','other_read_context',
            'other_contained_text','other_carrier','other_announced_issue','names_on_read_act','other_named_series','wrong_issue_series',
            'wrong_issue_day','wrong_issue_month','read_outside_today','anchor_outside_today','other_calendar','other_year','name_is_series','issue_is_series'))):
        doc=source_document(symbol);factory=previous.model if symbol=='hzje' else previous.model_for
        for variant in (*variants,'wrong_month_label','wrong_day_label','ambiguous_month','ambiguous_day','ambiguous_year'):
            values=factory(doc,variant);values.update(labels(context,variant))
            if variant=='ambiguous_year':
                original=values['hzir'];values['hzir']=lambda c,p,n,x:original(c,p,n,x) or (c,p,n,x)==('calendar','other',Fraction(1784),context)
            actual=previous.evaluate(doc,values)
            assert actual==[variant in ('baseline','same_instant')],(symbol,variant,actual)
            rows[symbol+'/'+variant]=actual
        for variant in ('unknown_month_label','unknown_day_label'):
            values=factory(doc);values.update(labels(context,variant))
            try:previous.evaluate(doc,values)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError((symbol,variant))
        # Correct labels in another parent or context must not satisfy this date.
        values=factory(doc);values.update(labels('other'))
        assert previous.evaluate(doc,values)==[False]
        for name in ('hzlm','hzln'):
            values=factory(doc);values.update(labels(context));fn=values[name]
            values[name]=lambda c,parent,p,n,x,fn=fn:fn(c,'other',p,n,x)
            assert previous.evaluate(doc,values)==[False]
    return dict(contrasts=rows,unknown_labels_refused=True,other_context_and_parent_refused=True)


def gap_checks():
    rows={}
    for symbol,previous,context in (('hzje',dateline,'dateline'),('hzkk',reading,'note')):
        old=source_document(symbol,PARENT);new=source_document(symbol)
        factory=previous.model if symbol=='hzje' else previous.model_for
        old_values=factory(old);new_values=factory(new);new_values.update(labels(context))
        assert previous.evaluate(old,old_values)==previous.evaluate(new,new_values)==[True]
        # Synthetic omitted periods: the label 30 is retained while its rank moves.
        before=old_values['hzit']
        def skipped(c,m,x):
            seq=before(c,m,x)
            return SequenceValue(tuple(day for day in seq.items if day not in ('day4','day5')),'"individual"')
        old_values['hzit']=skipped
        old_result=previous.evaluate(old,old_values);new_result=previous.evaluate(new,new_values)
        assert old_result==[False] and new_result==[True]
        assert not {'hzis','hzit'}&{d['name'] for d in new['declarations']}
        rows[symbol]=dict(old_offset=old_result,new_label=new_result)
    return dict(synthetic_gap_contrasts=rows,not_a_claim_of_missing_days_in_1784=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    before={d['name']:d for d in old.document['declarations']};after={d['name']:d for d in new.document['declarations']}
    assert set(after)-set(before)==set(PRIMITIVES)|{'rqsd'} and not set(before)-set(after)
    assert [n for n in before if before[n]!=after[n]]==['hzje','hzkk']
    for name in before:
        if name in ('hzje','hzkk'):assert after[name]['body']==replace_dates(before[name]['body'])
        else:assert semantic_entry(old.entries[name])==semantic_entry(new.entries[name]),name
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==23
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(
        ROOT,PARENT_BASIS,'data/described-thoughts-identifiers-v1.json').show()['entries']
    binding_before=selection_binding(old,[16]);binding_after=selection_binding(new,[16])
    assert binding_before['statements']==binding_after['statements'] and binding_before['dependencies']==binding_after['dependencies']
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY);assert len(lib.entries)==1
    return dict(changed_definitions=['hzje','hzkk'],new_primitives=2,new_definitions=1,previous_statements_preserved=23,
        signature_before=binding_before,signature_after=binding_after,other_meanings_preserved=True)


def alignment():
    date=dateline.source_unit();note=reading.alignment()['segments'][0]
    return dict(segments=[dict(unit=date['id'],unit_sha256=date['text_sha256'],range=[0,len(date['text'])],source=date['text'],
        status='partial_labeled_calendar_address',definitions=['rqsd','hzje'],remaining=['Historical calendar identification and whole-unit semantic review.']),
        dict(note,status='partial_labeled_calendar_address',definitions=['rqsd','hzkk'])])


def build_report():
    files=build()
    for p,b in files.items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    generic=generic_checks();source=source_checks();gaps=gap_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)
    for prior in ('reports/described-thoughts-v1.json','reports/calendar-dateline-v1.json','reports/dated-reading-v1.json'):
        report=json.loads((ROOT/prior).read_text(encoding='utf-8'));paths.add(prior);paths.update(report['source_sha256'])
        for p,h in report['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    paths.update(('scripts/compose_labeled_dates.py','scripts/check_labeled_dates.py','tests/test_labeled_dates.py','docs/labeled-dates-v1.md'))
    reference_path='artifacts/labeled-dates-v1/manifest.json'
    reference=json.loads((ROOT/reference_path).read_text(encoding='utf-8'));paths.add(reference_path)
    for row in reference['sources']:
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256']
        paths.add(row['path'])
    return dict(status='partial_labeled_calendar_dates_checked',document=FULL,generic=generic,source=source,gaps=gaps,structure=structural,
        calendar_reference=reference,
        alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len((ROOT/PARENT).read_text(encoding='utf-8')),
            generic_library_characters=len(files[LIBRARY]),note='Definitions are included; no compression claim.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Calendar labels, unique addresses and skipped-period contrasts checked')


if __name__=='__main__':main()
