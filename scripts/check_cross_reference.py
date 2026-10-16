"""Check a reference directive, its descriptive address, and fulfillment separately."""
import argparse
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_publication_header as prior
from scripts.compose_subject_bound_departure import closure
from scripts.compose_cross_reference import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,build,num

REPORT=ROOT/'reports/cross-reference-v1.json'
DOMAIN=('year','month','issue','page','act','reader','series','calendar','scheme','other')
SCENES=('reference',)
PRESENTATION_VARIANTS=('baseline','missing_presentation','other_author','other_node','other_context','other_template')
ADDRESS_VARIANTS=('baseline','year_1784','month_9','page_515','wrong_calendar','wrong_series','wrong_scheme',
    'wrong_parent','duplicate_page','missing_year','missing_month','missing_series','missing_year_display',
    'missing_month_display','missing_page','split_issue','other_scheme_duplicate','other_parent_duplicate')
ADDRESS_TRUE={'baseline','other_scheme_duplicate','other_parent_duplicate'}


def unknown(*args):raise ValueError('Unknown reference or fulfillment')


@lru_cache(maxsize=2)
def document(combined=False):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    roots=([*prior.prior.previous.previous.previous.SYMBOLS,'hzlt','hzlz','hzmd',*prior.ROOTS] if combined else [])+['hzmu']
    doc['declarations']=closure(doc,roots)
    doc['statements']=doc['statements'][18:] if combined else doc['statements'][-1:]
    return doc


def presentation_model(doc,variant='baseline',combined=False,seen=None):
    values=prior.model(prior.document(True),combined=True) if combined else {}
    for d in doc['declarations']:
        if d['kind']=='primitive' and d['name'] not in values:values[d['name']]=unknown
    values.update(wa=lambda:'author',hzms=lambda:'reference_node',hzmv=lambda:'reference')
    def presented(node,author,template,context):
        if variant=='unknown_presentation':return unknown()
        syntax=json.loads(template.syntax)
        if seen is not None:seen.append(syntax)
        return variant!='missing_presentation' and (node,author,context)==(
            'other' if variant=='other_node' else 'reference_node',
            'other' if variant=='other_author' else 'author',
            'header' if variant=='other_context' else 'reference') and syntax=={
                'kind':'function_ref','symbol':'hzmc' if variant=='other_template' else 'hzmt'}
    values['hzmp']=presented
    return values


def evaluate(doc,values,individuals=DOMAIN,situations=SCENES):
    return [r['value'] for r in evaluate_document(doc,individuals=individuals,situations=situations,primitives=values,
        max_steps=12000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(maxsize=1)
def address_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r zpage[] a.r zseries[] a.r zcal[] a.r zscheme[] a.r zcontext[] d.'+
        'q[k rqsp[k zpage[] k zseries[] k zcal[] '+num(1783)+' '+num(12)+' '+num(516)+' k zscheme[] k zcontext[]]].')


def address_model(doc,variant='baseline'):
    def years(cal,year,number,ctx):
        if variant=='unknown_year':return unknown()
        return variant!='missing_year' and (cal,year,number,ctx)==(
            'other' if variant=='wrong_calendar' else 'calendar','year',1784 if variant=='year_1784' else 1783,'reference')
    def months(cal,year,month,number,ctx):
        return variant!='missing_month' and (cal,year,month,number,ctx)==('calendar','year','month',9 if variant=='month_9' else 12,'reference')
    def belongs(issue,series,ctx):
        return variant!='missing_series' and (issue,series,ctx)==('issue','other' if variant=='wrong_series' else 'series','reference')
    def dated(issue,period,ctx):
        rows=set()
        if variant!='missing_year_display':rows.add(('issue','year'))
        if variant!='missing_month_display':rows.add(('other' if variant=='split_issue' else 'issue','month'))
        return (issue,period) in rows and ctx=='reference'
    def numbered(scheme,page,parents,number,ctx):
        if variant=='unknown_page':return unknown()
        rows=set()
        if variant!='missing_page':rows.add((
            'other' if variant=='wrong_scheme' else 'scheme','page',
            ('other' if variant=='wrong_parent' else 'issue',),515 if variant=='page_515' else 516))
        if variant=='duplicate_page':rows.add(('scheme','other',('issue',),516))
        if variant=='other_scheme_duplicate':rows.add(('other','other',('issue',),516))
        if variant=='other_parent_duplicate':rows.add(('scheme','other',('other',),516))
        return (scheme,page,parents.items,number) in rows and ctx=='reference'
    refs=dict(zpage='page',zseries='series',zcal='calendar',zscheme='scheme',zcontext='reference',
        hzkg='series',hzix='calendar',hzmr='scheme',zreader='reader')
    values={n:lambda v=v:v for n,v in refs.items()}
    values.update(hzir=years,hzlm=months,hzka=belongs,hzjy=dated,hzmi=numbered,
        dg=lambda act,ctx:variant!='no_action' and (act,ctx)==('act','reference'),
        hzmq=lambda act,reader,page,ctx:variant!='no_consultation' and (act,reader,page,ctx)==(
            'act','other' if variant=='other_reader' else 'reader','other' if variant=='other_page' else 'page','reference'))
    if variant=='unknown_consultation':values['hzmq']=unknown
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


@lru_cache(maxsize=1)
def message_document():
    doc=deepcopy(document());doc['statements']=[];doc['declarations']=closure(doc,['hzmt'])
    return parse(format_graph(doc,'compact')+'r zreader[] a.l[k hzmt[k zreader[]]].')


def checks():
    doc=document();rows={};seen=[]
    individuals=prior.DOMAIN+('reference_node',)
    situations=prior.SCENES+SCENES
    for variant in PRESENTATION_VARIANTS:
        rows[variant]=evaluate(doc,presentation_model(doc,variant,seen=seen),individuals,situations)
        assert rows[variant]==[variant=='baseline'],(variant,rows[variant])
    assert all(s=={'kind':'function_ref','symbol':'hzmt'} for s in seen)
    # All address/consultation facts are unknown here. Merely presenting the
    # closed message template must not request or invent their interpretations.
    try:evaluate(doc,presentation_model(doc,'unknown_presentation'),individuals,situations)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown presentation accepted')
    addresses={};adoc=address_document()
    for variant in ADDRESS_VARIANTS:
        actual=evaluate(adoc,address_model(adoc,variant));assert actual==[variant in ADDRESS_TRUE],(variant,actual)
        addresses[variant]=actual
    for variant in ('unknown_year','unknown_page'):
        try:evaluate(adoc,address_model(adoc,variant))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    fulfilled={};mdoc=message_document()
    for variant in ('baseline','no_action','no_consultation','other_reader','other_page','page_515'):
        values=address_model(mdoc,variant)
        result=evaluate_document(mdoc,individuals=DOMAIN,situations=SCENES,primitives=values,
            max_steps=12000000,memoize_definitions=False,memoize_expressions=False)[0]
        message=result['value']
        assert message.force=='direct',result
        assert message.content.values==(variant=='baseline',),(variant,result)
        fulfilled[variant]=dict(force=message.force,content=list(message.content.values))
    try:evaluate(mdoc,address_model(mdoc,'unknown_consultation'))
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown consultation accepted')
    joined={};combined=document(True)
    for variant in ('baseline','missing_presentation','other_context'):
        actual=evaluate(combined,presentation_model(combined,variant,True),individuals,situations)
        assert actual==[True]*13+[variant=='baseline'],(variant,actual)
        joined[variant]=actual
    return dict(presentation_contrasts=rows,address_contrasts=addresses,fulfillment_contrasts=fulfilled,
        combined_fourteen_statement_contrasts=joined,unknown_inputs_refused=4,
        unknown_address_and_action_not_evaluated_by_presentation=True,semantic_evaluation_uncached=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-8]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]==e,n
    for i in (16,17,27,28,29,30):assert selection_binding(old,[i])==selection_binding(new,[i])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(ROOT,PARENT_BASIS,'data/publication-header-identifiers-v1.json').show()['entries']
    return dict(previous_statements_preserved=31,new_primitive_relations=2,new_local_references=3,new_definitions=3,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')),
        previous_meanings_names_and_six_review_bindings_preserved=True)


def build_report():
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text
    for name in (FULL,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    old=json.loads((ROOT/'reports/publication-header-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,old['source_sha256'])
    evidence=json.loads((ROOT/'data/cross-reference-evidence-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    inventory=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    u=next(u for u in inventory['units'] if u['id']=='kant-1784:u0007')
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],
        status='partial_reference_directive',definitions=['rqsp','hzmt','hzmu'],remaining=['Whole-unit review is recorded separately.'])
    paths=set(old['source_sha256'])|set(evidence['source_sha256'])|set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/publication-header-v1.json','data/cross-reference-evidence-v1.json','scripts/compose_cross_reference.py',
        'scripts/check_cross_reference.py','tests/test_cross_reference.py','docs/cross-reference-v1.md'}
    return dict(status='cross_reference_formal_checks_under_stated_reading',document=FULL,checks=checks(),structure=structure(),roundtrips=True,
        alignment=dict(segments=[segment]),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Reference directive, page address and consultation checked separately')


if __name__=='__main__':main()
