"""Check cited-answer identity and absence of receipt over a history prefix."""
import argparse
import hashlib
from itertools import product
import json
import subprocess
import sys

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.compose_unreceived_reference import ROOT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure

REPORT=ROOT/'reports/unreceived-reference-v1.json'
DOMAIN=('author','answer','mendelssohn','name','citation','announcement','question','frame','other')
SCENES=('past','now','future','branch','note')


def forbidden(*args):raise ValueError('Unknown relation')


def source_document():
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['hzjt','hzju']);doc['statements']=doc['statements'][-2:]
    return doc


def generic_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r janchor[] d.r jhistory[d] c.r jbefore[d d] c.r jevent[d] c.'+
        'q[k rqrn[p jhistory p jbefore k janchor[] p jevent]].')


def evaluate(doc,model,diagnostic=False):
    if diagnostic:doc,model=lower(doc,model)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=500000,memoize_definitions=False,memoize_expressions=False)]


def order(variant='baseline'):
    def before(left,right):
        if variant=='reflexive' and left==right:return True
        if variant=='cyclic' and (left,right)==('future','past'):return True
        if variant=='nontransitive' and (left,right)==('past','future'):return False
        return SCENES.index(left)<SCENES.index(right)
    return before


def generic_checks():
    doc=generic_document();count=0
    for bits in product((False,True),repeat=4):
        model=dict(janchor=lambda:'now',jhistory=lambda t:t in SCENES[:3],jbefore=order(),
            jevent=lambda t:bits[SCENES.index(t)] if t in SCENES[:4] else False)
        expected=[not(bits[0] or bits[1])]
        assert evaluate(doc,model)==evaluate(doc,model,True)==expected,bits
        count+=1
    invalid={}
    for variant in ('empty','missing_anchor','reflexive','cyclic','nontransitive'):
        history=() if variant=='empty' else ('past','future') if variant=='missing_anchor' else SCENES[:3]
        model=dict(janchor=lambda:'now',jhistory=lambda t:t in history,jbefore=order(variant),jevent=lambda t:False)
        invalid[variant]=evaluate(doc,model);assert invalid[variant]==[False]
    # Logical scope does not require a future event value. The opt-in diagnostic
    # evaluator can skip it; the normal eager evaluator conservatively refuses.
    model=dict(janchor=lambda:'now',jhistory=lambda t:t in SCENES[:3],jbefore=order(),
        jevent=lambda t:forbidden() if t in ('future','branch','note') else False)
    assert evaluate(doc,model,True)==[True]
    try:evaluate(doc,model)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Eager interpreter unexpectedly skipped unknown future')
    for point in ('past','now'):
        model['jevent']=lambda t,point=point:forbidden() if t==point else False
        for diagnostic in (False,True):
            try:evaluate(doc,model,diagnostic)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError((point,diagnostic))
    return dict(event_patterns=count,invalid_histories=invalid,future_and_other_branch_do_not_affect_truth=True,
        unknown_past_and_anchor_refused=True,unknown_future_diagnostic_skipped=True,unknown_future_eager_refused=True)


def model_for(doc,variant='baseline'):
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    refs=dict(wa='author',hzia='question',hzjl='note',hzjm='now',hzjn='answer',hzjo='mendelssohn',hzjp='name',
        hzjq='citation',hzjr='announcement',hzjs='frame')
    if variant=='name_is_person':refs['hzjp']='mendelssohn'
    model.update({n:(lambda value=value:value) for n,value in refs.items()})
    def inside(act,medium,context):
        return (act,medium,context)==('citation','other' if variant=='other_medium' else 'announcement','note')
    def names(act,name,person,context):
        return (act,name,person,context)==('citation',refs['hzjp'],'other' if variant=='other_named_person' else 'mendelssohn','note')
    def credit(act,document,author,context):
        return (act,document,author,context)==('other' if variant=='other_credit_act' else 'citation',
            'other' if variant=='other_credit_document' else 'answer','mendelssohn','note')
    def cited(act,document,question,context):
        if variant=='unknown_citation':return forbidden()
        return (act,document,question,context)==('citation','other' if variant=='other_cited_document' else 'answer',
            'other' if variant=='other_question' else 'question','branch' if variant=='other_citation_context' else 'note')
    def history(frame,context,point):
        return variant!='empty_history' and (frame,context)==('frame','note') and point in SCENES[:3]
    def before(left,right,context):
        return context=='note' and order('cyclic' if variant=='cyclic' else 'baseline')(left,right)
    def received(person,item,point,context):
        if variant=='unknown_past' and point=='past':return forbidden()
        target=('author','answer','past','note')
        if variant=='received_now':target=('author','answer','now','note')
        if variant=='received_future':target=('author','answer','future','note')
        if variant=='received_other_branch':target=('author','answer','branch','note')
        if variant=='received_other_person':target=('other','answer','past','note')
        if variant=='received_other_item':target=('author','other','past','note')
        if variant=='received_other_context':target=('author','answer','past','branch')
        return variant.startswith('received_') and (person,item,point,context)==target
    model.update(dg=lambda act,context:variant!='missing_citation' and (act,context)==('citation','note'),
        hzjk=inside,hzih=names,hzij=credit,hzjj=cited,h7q=history,ic=before,hzji=received)
    return model


def source_checks():
    doc=source_document();rows={}
    citation_false=('other_medium','other_named_person','other_credit_act','other_credit_document',
        'other_cited_document','other_question','other_citation_context','missing_citation','name_is_person')
    receipt_false=('received_past','received_now','empty_history','cyclic')
    variants=('baseline',)+citation_false+receipt_false+('received_future','received_other_branch','received_other_person',
        'received_other_item','received_other_context')
    for variant in variants:
        expected=[variant not in citation_false,variant not in receipt_false]
        actual=evaluate(doc,model_for(doc,variant));assert actual==expected,(variant,actual)
        rows[variant]=actual
    for variant in ('unknown_past','unknown_citation'):
        try:evaluate(doc,model_for(doc,variant))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    return dict(contrasts=rows,citation_does_not_imply_receipt=True,unknown_inputs_refused=True)


def structure():
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    size=len(before.document['declarations']);added=after.document['declarations'][size:]
    assert after.document['declarations'][:size]==before.document['declarations']
    assert after.document['statements'][:-2]==before.document['statements'] and len(after.document['statements'])==20
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(after.document,['rqrn','rqro'])
    assert not any(d['kind']=='primitive' for d in lib.document['declarations'])
    assert before.entries['h7q']['arguments']==['temporal_frame','evaluation_context','point']
    names=load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert names.find('Mendelssohn')['matches'][0]['symbol']=='hzjp'
    return dict(previous_declarations_preserved=size,previous_statements_preserved=18,new_statements=2,
        new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),generic_library_primitives=0)


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    text=unit['text'];ranges=[(text.index('worin'),text.index('Mir ist')), (text.index('Mir ist'),text.index(';')+1)]
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=text[start:end],
        status='partial_cited_answer_and_nonreceipt',definitions=definitions,
        remaining=['Pronoun and relative-clause readings, honorific, temporal anchoring and full footnote remain unresolved.'])
        for (start,end),definitions in zip(ranges,[['hzjt'],['rqrn','rqro','hzju']],strict=True)])


def build_report():
    files=build()
    for p,body in files.items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    generic=generic_checks();source=source_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    facsimile=json.loads((ROOT/'data/author-signature-facsimile-v1.json').read_text(encoding='utf-8'))
    for p,h in facsimile['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(facsimile['source_sha256'])|{
        'data/author-signature-facsimile-v1.json','data/calendar-dateline-identifiers-v1.json',
        'scripts/compose_unreceived_reference.py','scripts/check_unreceived_reference.py','scripts/compose_subject_bound_departure.py',
        'scripts/compose_calendar_dateline.py','docs/unreceived-reference-v1.md','tests/test_unreceived_reference.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    paths.update('noema/'+name+'.py' for name in ('constructed','constructed_discourse','constructed_semantics','discourse','extraction',
        'grammar','guarded_ranked_semantics','identifiers','meaning_basis','meaning_catalog','ranked','ranked_discourse','script','semantics','diagnostic_short_circuit'))
    parent=(ROOT/load_catalog(ROOT,PARENT_BASIS).document_path).read_text(encoding='utf-8')
    return dict(status='partial_cited_answer_and_nonreceipt_checked',document=FULL,generic=generic,source=source,structure=structural,
        alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len(parent),
            generic_library_characters=len(files[LIBRARY]),annotation_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Includes declarations and references; this is not a source compression ratio.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Cited-answer identity and history-prefix nonreceipt checked')


if __name__=='__main__':main()
