"""Check receipt histories and nonvacuous, correctly scoped counterfactuals."""
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
from scripts.compose_counterfactual_withholding import ROOT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure

REPORT=ROOT/'reports/counterfactual-withholding-v1.json'
DOMAIN=('author','answer','document','actualframe','counterframe','withholding','other')
SCENES=('actual','casea','caseb','past','now','future')
POINTS=SCENES[3:]


def forbidden(*args):raise ValueError('Unknown interpretation')


def before(left,right):return left in POINTS and right in POINTS and POINTS.index(left)<POINTS.index(right)


def evaluate(doc,values,diagnostic=False):
    if diagnostic:doc,values=lower(doc,values)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def prefix_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r janchor[] d.r jhistory[d] c.r jbefore[d d] c.r jevent[d] c.'+
        'q[k rqrq[p jhistory p jbefore k janchor[] p jevent]].q[k rqrn[p jhistory p jbefore k janchor[] p jevent]].')


def prefix_checks():
    doc=prefix_document();count=0
    for bits in product((False,True),repeat=4):
        values=dict(janchor=lambda:'now',jhistory=lambda t:t in POINTS,jbefore=before,
            jevent=lambda t:bits[(POINTS+('actual',)).index(t)] if t in POINTS+('actual',) else False)
        expected=[bits[0] or bits[1],not(bits[0] or bits[1])]
        assert evaluate(doc,values)==expected,bits;count+=1
    invalid={}
    for variant in ('empty','missing_anchor','cyclic'):
        values=dict(janchor=lambda:'now',jhistory=lambda t:False if variant=='empty' else t in ('past','future') if variant=='missing_anchor' else t in POINTS,
            jbefore=lambda a,b:before(a,b) or variant=='cyclic' and (a,b)==('future','past'),jevent=lambda t:t=='past')
        invalid[variant]=evaluate(doc,values);assert invalid[variant]==[False,False]
    return dict(event_patterns=count,invalid_histories=invalid,complements_only_on_valid_histories=True)


def conditional_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r jactual[] d.r jante[d] c.r jcons[d] c.r jselect[d d] c.'+
        'q[k rqrs[k jactual[] p jante p jcons p jselect]].')


def conditional_checks():
    doc=conditional_document();count=0
    # Independently vary actuality, two selected worlds and their own outcomes.
    for bits in product((False,True),repeat=7):
        actual,sa,sb,pa,pb,qa,qb=bits
        values=dict(jactual=lambda:'actual',jante=lambda w:actual if w=='actual' else pa if w=='casea' else pb if w=='caseb' else False,
            jcons=lambda w:qa if w=='casea' else qb if w=='caseb' else False,
            jselect=lambda base,w:base=='actual' and (sa if w=='casea' else sb if w=='caseb' else False))
        expected=[not actual and (sa or sb) and (not sa or pa and qa) and (not sb or pb and qb)]
        assert evaluate(doc,values)==expected,bits;count+=1
    values=dict(jactual=lambda:'actual',jante=lambda w:w=='casea',jcons=lambda w:w in ('actual','casea'),
        jselect=lambda base,w:(base,w)==('actual','casea'))
    assert evaluate(doc,values)==[True]
    return dict(truth_combinations=count,actual_consequent_not_constrained=True)


def source_document():
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['hzkt']);doc['statements']=doc['statements'][-1:]
    return doc


def model_for(doc,variant='baseline',seen=None):
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    refs=dict(wa='author',hzjn='answer',hzik='answer' if variant=='same_documents' else 'document',hzjl='actual',hzjs='actualframe',hzjm='now')
    values.update({n:(lambda v=v:v) for n,v in refs.items()})
    def frame(ctx):
        if variant=='unknown_selected_frame' and ctx=='casea':return forbidden()
        return 'actualframe' if ctx=='actual' and variant!='wrong_actual_frame' else 'counterframe'
    def anchor(ctx):
        if variant=='wrong_actual_anchor' and ctx=='actual':return 'future'
        if variant=='different_selected_anchor' and ctx=='casea':return 'future'
        if variant=='invalid_selected_anchor' and ctx=='casea':return 'actual'
        return 'now'
    def history(frame,ctx,point):
        if variant=='empty_actual_history' and ctx=='actual':return False
        return frame==('actualframe' if ctx=='actual' else 'counterframe') and point in POINTS
    def received(person,item,point,ctx):
        if variant=='unknown_receipt' and ctx=='casea' and point=='past':return forbidden()
        who='other' if variant=='other_receiver' else 'author'
        which='other' if variant=='other_received_item' else 'answer'
        worlds=('casea','caseb') if variant=='second_bad_outcome' else ('actual','casea') if variant=='actually_received' else ('casea',)
        return (person,item,point)==(who,which,'past') and ctx in worlds
    def selected(person,description,base,candidate):
        if seen is not None:seen.append(json.loads(description.syntax))
        if variant=='unknown_selection':return forbidden()
        expected={'kind':'function_ref','symbol':'other' if variant=='other_antecedent_description' else 'hzkr'}
        cases=() if variant=='empty_selection' else ('caseb',) if variant=='selected_without_receipt' else ('casea','caseb') if variant in ('split_worlds','second_bad_outcome') else ('casea',)
        return (person,base)==('other' if variant=='other_viewpoint' else 'author','caseb' if variant=='other_actual_context' else 'actual') and json.loads(description.syntax)==expected and candidate in cases
    def occurs(act,ctx):return variant!='missing_action' and act=='withholding' and ctx in ('actual','casea','caseb')
    def withholds(act,person,document,ctx):
        if variant=='unknown_withholding' and ctx=='casea':return forbidden()
        worlds=('caseb',) if variant=='split_worlds' else ('actual','casea') if variant=='actual_withholding' else ('casea',)
        return (act,person,document)==('withholding','other' if variant=='other_withholder' else 'author',
            'other' if variant=='other_withheld_document' else refs['hzik']) and ctx in worlds
    def influences(document,act,ctx):
        return variant!='no_influence' and (document,act)==('other' if variant=='other_cause_document' else 'answer',
            'other' if variant=='other_cause_action' else 'withholding') and ctx in ('actual','casea','caseb')
    values.update(hzkm=frame,hzkn=anchor,h7q=history,ic=lambda a,b,ctx:before(a,b),hzji=received,hzko=selected,
        dg=occurs,hzkp=withholds,hzkq=influences)
    return values


def source_checks():
    doc=source_document();rows={}
    variants=('baseline','actual_withholding','different_selected_anchor','actually_received','empty_selection','selected_without_receipt','split_worlds',
        'second_bad_outcome','other_receiver','other_received_item','other_antecedent_description','other_viewpoint','other_actual_context',
        'missing_action','other_withholder','other_withheld_document','no_influence','other_cause_document','other_cause_action',
        'same_documents','wrong_actual_frame','wrong_actual_anchor','invalid_selected_anchor','empty_actual_history')
    seen=[]
    for variant in variants:
        values=model_for(doc,variant,seen);actual=evaluate(doc,values,True)
        assert actual==[variant in ('baseline','actual_withholding','different_selected_anchor')],(variant,actual)
        rows[variant]=actual
    assert seen and all(x=={'kind':'function_ref','symbol':'hzkr'} for x in seen)
    # Check key diagnoses on the stored graph with no lowering or memoization.
    for variant in ('baseline','actually_received','split_worlds','empty_actual_history'):
        assert evaluate(doc,model_for(doc,variant))==rows[variant],variant
    for variant in ('unknown_selected_frame','unknown_receipt','unknown_selection','unknown_withholding'):
        try:evaluate(doc,model_for(doc,variant),True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    return dict(contrasts=rows,antecedent_description_preserved=True,unknown_inputs_refused=True,
        diagnostic_cases=len(variants),stored_graph_uncached_comparisons=4)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS);size=len(old.document['declarations'])
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==22
    added=new.document['declarations'][size:]
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new.document,['rqrn','rqrq','rqrr','rqrs'])
    assert not any(d['kind']=='primitive' for d in lib.document['declarations'])
    old_names=load_annotations(ROOT,PARENT_BASIS,'data/dated-reading-identifiers-v1.json').show()['entries']
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==old_names
    return dict(previous_statements_preserved=21,previous_declarations_preserved=size,new_primitives=5,new_definitions=6,new_statements=1)


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    text=unit['text'];start=text.index('sonst');end=text.index(', die jetzt')+1
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=text[start:end],
        status='partial_counterfactual_withholding',definitions=['rqrq','rqrr','rqrs','hzkr','hzks','hzkt'],
        remaining=['Appropriateness of comparative scenarios, stage of withholding, causal mechanism and whole-unit meaning remain unresolved.'])])


def build_report():
    files=build()
    for name,body in files.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    prefix=prefix_checks();conditional=conditional_checks();source=source_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    facsimile=json.loads((ROOT/'data/author-signature-facsimile-v1.json').read_text(encoding='utf-8'))
    for p,h in facsimile['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(facsimile['source_sha256'])|{
        'data/author-signature-facsimile-v1.json','data/dated-reading-identifiers-v1.json',
        'scripts/compose_counterfactual_withholding.py','scripts/check_counterfactual_withholding.py','scripts/compose_subject_bound_departure.py',
        'scripts/compose_calendar_dateline.py','docs/counterfactual-withholding-v1.md','tests/test_counterfactual_withholding.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    paths.update('noema/'+n+'.py' for n in ('constructed','constructed_discourse','constructed_semantics','discourse','extraction',
        'grammar','guarded_ranked_semantics','identifiers','meaning_basis','meaning_catalog','ranked','ranked_discourse','script','semantics','diagnostic_short_circuit'))
    parent=(ROOT/load_catalog(ROOT,PARENT_BASIS).document_path).read_text(encoding='utf-8')
    return dict(status='partial_counterfactual_withholding_checked',document=FULL,prefix=prefix,conditional=conditional,source=source,
        structure=structural,alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len(parent),
            generic_library_characters=len(files[LIBRARY]),annotation_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Includes shared declarations; not a source compression ratio.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Receipt prefix and counterfactual withholding checked')


if __name__=='__main__':main()
