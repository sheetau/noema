"""Check heading self-reference separately from answer content and correctness."""
import argparse
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog,_references
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_answer_heading import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,build

REPORT=ROOT/'reports/answer-heading-v1.json'
EVIDENCE='data/answer-heading-evidence-v1.json'
PEOPLE=('introduction','question','opening','document','prior','foot','citation','author','other')
SCENES=('context','note','other')


def unknown(*args):raise ValueError('Unknown heading interpretation')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=False,memoize_expressions=False,max_steps=2000000)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zintroduction[] a.r zdocument[] a.r zquestion[] a.r zcontext[] d.
q[k rqu5[k zintroduction[] k zdocument[] k zquestion[] k zcontext[]]].
''');count=0
    for distinct,occurs,inside,answer,before in product((False,True),repeat=5):
        question='question' if distinct else 'introduction'
        values=dict(zintroduction=lambda:'introduction',zdocument=lambda:'document',zquestion=lambda:question,zcontext=lambda:'context',
            dg=lambda n,c:occurs and (n,c)==('introduction','context'),
            hzjk=lambda n,d,c:inside and (n,d,c)==('introduction','document','context'),
            hzjj=lambda n,d,q,c:answer and (n,d,q,c)==('introduction','document',question,'context'),
            ue=lambda n,q,c:before and (n,q,c)==('introduction',question,'context'))
        assert evaluate(doc,values)==[all((distinct,occurs,inside,answer,before))];count+=1
    return dict(presentation_containment_response_order_and_distinctness_combinations=count,uncached_and_unlowered=True)


def document(combined=False):
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'))
    if not combined:doc['statements']=doc['statements'][-1:]
    return doc


def model(doc,variant='baseline'):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(hzs2=lambda:'question' if variant=='same_nodes' else 'introduction',hzik=lambda:'document',hzia=lambda:'question',
        wh=lambda:'context',wa=lambda:'author',wb=lambda:'opening',hzls=lambda:'foot',hzjl=lambda:'note',hzjq=lambda:'citation',hzjn=lambda:'prior')
    occurs={('foot','note')};inside={('foot','document','note')};answers={('foot','document','question','note')}
    order={('question','opening','context')}
    if variant!='missing_occurrence':occurs.add(('introduction','context'))
    if variant!='missing_containment':inside.add(('introduction','prior' if variant=='other_container' else 'document','context'))
    if variant not in ('missing_framing','opening_and_footnote_only'):
        answers.add(('other' if variant=='other_introduction' else 'introduction',
            'prior' if variant=='other_document' else 'document','opening' if variant=='other_question' else 'question',
            'other' if variant=='other_context' else 'context'))
    order.add(('question','introduction','context') if variant=='reverse_order' else ('introduction','question','context'))
    query=dict(kind='apply',function=dict(kind='function_ref',symbol='rqqq'),arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol='bi'))])
    values.update(dg=lambda *args:args in occurs,hzjk=lambda *args:args in inside,hzjj=lambda *args:args in answers,ue=lambda *args:args in order,
        hzib=lambda n,a,q,c:(n,a,c)==('question','author','context') and q.rank==1 and json.loads(q.syntax)==query,
        ua=lambda n,a,d,c:(n,a,c)==('opening','author','context') and d.rank==0 and json.loads(d.syntax)==dict(kind='function_ref',symbol='bi'),
        hzcs=lambda a,q,r,c:(a,q,r,c)==('author','question','opening','context'))
    return values


def source_checks():
    doc=document(True);rows={}
    for variant in ('baseline','missing_occurrence','missing_containment','missing_framing','other_introduction',
        'other_document','other_question','other_context','other_container','reverse_order','same_nodes','opening_and_footnote_only'):
        actual=evaluate(doc,model(doc,variant));assert actual==[True,True,variant=='baseline'],(variant,actual);rows[variant]=actual
    single=document()
    for name in ('dg','hzjk','hzjj','ue','hzs2','hzik','hzia','wh'):
        values=model(single);values[name]=unknown
        try:evaluate(single,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    # Neither the title's self-description nor the old response presentation
    # decides whether the answer is correct. Its property primitives stay unknown.
    base=deepcopy(doc);base['statements']=[]
    truth_doc=parse(format_graph(base,'compact')+'r zcorrect[] c.q[k zcorrect[]].')
    truth_doc['statements']=deepcopy(doc['statements'])+truth_doc['statements']
    for truth in (False,True):
        values=model(truth_doc);values['zcorrect']=lambda:truth
        assert evaluate(truth_doc,values)==[True,True,True,truth]
    return dict(three_statement_contrasts=rows,unknown_inputs_refused=8,
        question_and_current_document_shared=True,opening_and_footnote_cannot_replace_heading=True,
        correctness_and_explanation_adequacy_not_asserted=True,answer_content_not_executed=True,uncached_and_unlowered=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-3]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==35
    for name,entry in old.entries.items():assert new.entries[name]==entry
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    assert set(new.entries)-set(old.entries)=={'rqu5','hzs2','hzs3'}
    selected=selection_binding(new,[34]);assert not {'bi','rqqp','rqqq'}&set(selected['dependencies'])
    assert {'hzik','hzia','wh','hzjj','hzjk','ue','dg'}<=set(selected['dependencies'])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(
        ROOT,'data/cross-reference-basis-v1.json','data/cross-reference-identifiers-v1.json').show()['entries']
    return dict(new_definitions=2,new_local_references=1,new_primitive_relations=0,
        previous_statements_preserved=34,new_source_statements=1,seven_review_bindings_preserved=True,
        preceding_question_and_answer_content_not_redefined=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def alignment():
    from scripts.audit_written_progress_extended import collect_alignment
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));u=evidence['source']
    result=dict(unit=u['unit'],unit_sha256=u['unit_sha256'],start=0,end=len(u['text']),source=u['text'],
        definitions=['rqu5','hzs3'],status='partial_answer_heading_framing',full_semantic_equivalence=False)
    units={row['id']:row for row in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']}
    rows=collect_alignment(dict(alignment=result),units,{'rqu5','hzs3'},'reports/answer-heading-v1.json')
    assert len(rows)==1 and rows[0]['status']=='partial' and rows[0]['range']==[0,23]
    return result


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/shared-public-scope-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    results={}
    for name,fn in [('generic',generic_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)|set(previous['source_sha256'])|set(evidence['source_sha256'])|{
        'reports/shared-public-scope-v1.json',EVIDENCE,'data/cross-reference-identifiers-v1.json',
        'scripts/compose_answer_heading.py','scripts/check_answer_heading.py','scripts/audit_written_progress_extended.py',
        'tests/test_answer_heading.py','docs/answer-heading-v1.md'}
    return dict(status='current_document_answer_heading_checked',document=FULL,**results,roundtrips=True,
        new_covered_characters=0,alignment=alignment(),
        verified_full_units={'kant-1784':0,'einstein-1905':0},whole_unit_review_recorded_separately=True,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Heading, opening response and current document checked',flush=True)


if __name__=='__main__':main()
