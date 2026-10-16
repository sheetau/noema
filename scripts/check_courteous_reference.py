"""Check conventional reference style without inferring sincere feelings."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding,validate_hashes
from scripts import check_announced_answer as answer
from scripts import check_dated_reading as reading
from scripts.compose_courteous_reference import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure

REPORT=ROOT/'reports/courteous-reference-v1.json'
DOMAIN=reading.DOMAIN+('mention',)


def evaluate(doc,values):
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=reading.SCENES,
        primitives={n:values[n] for n in required},max_steps=500000,memoize_definitions=False,memoize_expressions=False)]


def document(combined=False):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'));roots=['hzjt','hzju','hzkk','hzlr'] if combined else ['hzlr']
    doc['declarations']=closure(doc,roots);doc['statements']=[s for s in doc['statements'] if s.get('body',{}).get('symbol') in roots]
    assert len(doc['statements'])==len(roots)
    return doc


def model(variant='baseline'):
    refs=dict(hzlp='citation' if variant=='same_use' else 'mention',hzjq='citation',hzjp='mendelssohn' if variant=='name_is_person' else 'name',hzjo='mendelssohn',hzjl='note')
    def names(use,name,target,context):
        return (use,name,target,context)==('citation' if variant=='citation_name_only' else refs['hzlp'],
            'other' if variant=='wrong_name' else refs['hzjp'],'other' if variant=='wrong_named_person' else 'mendelssohn',
            'branch' if variant=='wrong_name_context' else 'note')
    def courtesy(use,target,context):
        if variant=='unknown_courtesy':return reading.forbidden()
        return variant!='missing_courtesy' and (use,target,context)==('citation' if variant=='citation_courtesy_only' else refs['hzlp'],
            'other' if variant=='wrong_courtesy_person' else 'mendelssohn','branch' if variant=='wrong_courtesy_context' else 'note')
    values={n:(lambda v=v:v) for n,v in refs.items()}
    values.update(dg=lambda use,ctx:variant!='missing_occurrence' and (use,ctx)==(refs['hzlp'],'note'),hzih=names,hzlq=courtesy)
    return values


def checks():
    doc=document();rows={}
    for variant in ('baseline','missing_occurrence','missing_courtesy','wrong_name','wrong_named_person','wrong_name_context',
        'citation_name_only','citation_courtesy_only','wrong_courtesy_person','wrong_courtesy_context','same_use','name_is_person'):
        actual=evaluate(doc,model(variant));assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual
    try:evaluate(doc,model('unknown_courtesy'))
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown register must not be guessed')
    generic=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r juse[] a.r jname[] a.r jtarget[] a.r jcontext[] d.r joccurs[a d] c.r jnames[a a a d] c.r jstyle[a a d] c.'+
        'q[k rqsl[k juse[] k jname[] k jtarget[] k jcontext[] p joccurs p jnames p jstyle]].')
    for bits in product((False,True),repeat=3):
        values=dict(juse=lambda:'mention',jname=lambda:'name',jtarget=lambda:'mendelssohn',jcontext=lambda:'note')
        for n,b in zip(('joccurs','jnames','jstyle'),bits,strict=True):values[n]=lambda *args,b=b:b
        assert evaluate(generic,values)==[all(bits)]
    # Add an independent claim of sincere regard. Courtesy alone permits either value.
    feelings=deepcopy(doc);feelings['statements']=[]
    feelings=parse(format_graph(feelings,'compact')+'r jregard[] c.s[k hzlr[]].q[k jregard[]].')
    for feeling in (False,True):assert evaluate(feelings,dict(model(),jregard=lambda:feeling))==[True,feeling]
    return dict(source_contrasts=rows,generic_combinations=8,unknown_courtesy_refused=True,sincere_regard_not_entailed=True)


def combined_checks():
    doc=document(True);rows={}
    for variant,source_variant,received,expected in [('baseline','baseline','baseline',[True,True,True,True]),
        ('citation_courtesy_only','baseline','baseline',[True,True,True,False]),
        ('baseline','missing_membership','baseline',[True,True,False,True]),
        ('baseline','baseline','received_past',[True,False,True,True]),
        ('baseline','read_answer','baseline',[True,True,False,True])]:
        values=answer.model(doc,source_variant,received);own=model(variant)
        for n in ('dg','hzih'):
            a,b=values[n],own[n];own[n]=lambda *args,a=a,b=b:a(*args) or b(*args)
        values.update(own);actual=evaluate(doc,values);assert actual==expected,(variant,source_variant,received,actual)
        rows[variant+'/'+source_variant+'/'+received]=actual
    return rows


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    size=len(old.document['declarations'])
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==24
    for n,e in old.entries.items():assert e==new.entries[n],n
    for i in (16,17):assert selection_binding(old,[i])==selection_binding(new,[i])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(ROOT,PARENT_BASIS,'data/announced-answer-identifiers-v1.json').show()['entries']
    library=load_catalog(ROOT,BASIS,document_path=LIBRARY);assert set(library.entries)=={'rqsl'}
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),previous_statements_preserved=23,
        signature_and_dateline_bindings_identical=True,previous_meaning_entries_identical=True,
        generic_library_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        additional_manuscript_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    files=build()
    for p,body in files.items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    prior=json.loads((ROOT/'reports/announced-answer-v1.json').read_text(encoding='utf-8'))
    evidence=json.loads((ROOT/'data/courteous-reference-evidence-v1.json').read_text(encoding='utf-8'))
    for record in (prior,evidence):validate_hashes(ROOT,record['source_sha256'])
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    phrase='des Herrn Mendelssohn';start=unit['text'].index(phrase)
    paths=set(prior['source_sha256'])|set(evidence['source_sha256'])|set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/announced-answer-v1.json','data/courteous-reference-evidence-v1.json','docs/courteous-reference-v1.md',
        'scripts/compose_courteous_reference.py','scripts/check_courteous_reference.py','tests/test_courteous_reference.py'}
    return dict(status='partial_courteous_source_mention_distinct_from_embedded_citation',document=FULL,
        checks=checks(),combined=combined_checks(),structure=structure(),roundtrips=True,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],source=phrase,
            status='partial_conventional_courtesy',definitions=['rqsl','hzlr'],remaining=['Gendered/social convention and whole footnote reading remain incomplete.'])]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Courteous source mention, separate citation scope and absence of psychological entailment checked')


if __name__=='__main__':main()
