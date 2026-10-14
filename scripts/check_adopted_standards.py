"""Verify exact standard descriptions and their statically quotable instances."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts.check_closed_policies import quoted
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import callbacks
from scripts import check_prescribed_teaching as old
from scripts.compose_adopted_standards import ROOT,PARENT,BUILDERS,BOUND_SETTINGS,DESCRIPTION,DESCRIBED_ADOPTION
from scripts.compose_prescribed_teaching import ADOPTED,CRITERION,MESSAGE

REPORT=ROOT/'reports/adopted-standards-v1.json'
EXTRA=old.EXTRA.replace('r zw[] '+ADOPTED+'.','r zw[] '+DESCRIBED_ADOPTION+'.')+(
    'd zy[subject a message '+MESSAGE+'] e[k zt[v subject v message]].')


def source_setup(text,criteria=('zt','zu')):
    doc=candidate(text,EXTRA)
    list_text='l['+CRITERION+']['+' '.join('p '+n for n in criteria)+']'
    standard=description(doc,list_text)
    expected=description(doc,'l['+CRITERION+'][p zt p zu]')
    position=next(i for i,(name,_) in enumerate(BOUND_SETTINGS) if name=='standarddescription')
    specialized=specialize_definition(doc,'hzbi','hzbj',{position:standard})
    doc=specialized.document
    arguments=[quoted('call','zp'),quoted('call','zc'),quoted('call','zq'),
        quoted('function_ref','zr'),quoted('function_ref','zs'),quoted('call','zi'),
        description(doc,'r[p zm]'),quoted('call','zv'),quoted('call','zw')]
    teaching=apply_description(doc,quoted('function_ref','hzbj'),arguments)
    node=lambda n:quoted('call',n)['body']
    duty=[node(n) for n in ('za','zb','zc','zd')]+[teaching,node('zk')]
    public=[node(n) for n in ('ze','zf','zg','zh','zi')]+[quoted('function_ref','zm'),node('zj')]
    doc['statements']=[{'kind':'ask','body':{'kind':'call','symbol':name,'arguments':args}}
        for name,args in (('hzbf',duty),('hzbg',duty),('hzbh',duty+public))]
    probe=parse(format_graph(doc,'compact')+'q[t[c[s[r[p zo]]][k za[] k zb[]]][k zk[]]].')
    def replace(value):
        if isinstance(value,dict):
            if value==quoted('function_ref','zo'):return teaching
            return {k:replace(v) for k,v in value.items()}
        if isinstance(value,list):return [replace(v) for v in value]
        return value
    doc['statements'].append(replace(probe['statements'][-1]))
    direct='q[t[c[k hzbi[k zp[] k zc[] k zq[] p zr p zs k zi[] r[p zm] r['+list_text+'] k zv[] k zw[]]][k za[] k zb[]]][k zk[]]].'
    doc=parse(format_graph(doc,'compact')+direct)
    trace=dict(bound_positions=specialized.bound_positions,expanded_definitions=specialized.expanded_definitions,
        disquotations_removed=specialized.disquotations_removed,quotable_specialized_symbol=specialized.symbol)
    return doc,teaching,criteria,standard,expected,trace


def model_for(setup,bits=(True,True,False,True,True,True),variant='baseline',adoption=None):
    doc,teaching,criteria,standard,expected,_=setup
    model,_=old.model_for(doc,teaching,criteria,bits,variant if variant=='unknown_criterion' else 'baseline')
    adopted=adoption or expected
    observed=[]
    def relation(principal,rule,description,context):
        observed.append(description.syntax)
        wanted=['institution','standard','now']
        for i,field in enumerate(('principal','standard','context')):
            if variant=='adoption_'+field:wanted[i]='elsewhere' if field=='context' else 'other'
        return [principal,rule,context]==wanted and description.syntax==syntax(adopted) and variant!='unadopted'
    callbacks(doc,model,{'zw':relation})
    return model,observed


def identity_checks(texts):
    setups=[source_setup(text) for text in texts]
    cases=[]
    for bits in product((False,True),repeat=6):
        required,allowed,forbidden,delivered,first,second=bits
        actual=delivered and first and second
        expected=[required,required and not actual,required and allowed and not forbidden,actual,actual]
        rows=[old.evaluate(s[0],model_for(s,bits)[0]) for s in setups]
        if rows!=[expected]*2:raise ValueError('Described standard states differ: '+repr((bits,rows)))
        cases.append(dict(states=list(bits),results=rows[0]))
    variants=[]
    for selected in (('zu','zt'),('zt','zt'),('zu','zu'),('zy','zu'),('zt',),(),('zt','zu','zt')):
        alternative=[source_setup(text,selected) for text in texts]
        rejected=[old.evaluate(s[0],model_for(s)[0]) for s in alternative]
        if rejected!=[[True,True,True,False,False]]*2:raise ValueError('Another criterion description was accepted: '+repr(selected))
        accepted=[old.evaluate(s[0],model_for(s,adoption=s[3])[0]) for s in alternative]
        if accepted!=[[True,False,True,True,True]]*2:raise ValueError('Explicitly adopted alternative was rejected')
        variants.append(dict(criteria=list(selected),old_adoption=rejected[0],explicit_new_adoption=accepted[0]))
    bindings={}
    for variant in ('adoption_principal','adoption_standard','adoption_context','unadopted'):
        rows=[old.evaluate(s[0],model_for(s,variant=variant)[0]) for s in setups]
        if rows!=[[True,True,True,False,False]]*2:raise ValueError('Adoption binding differs')
        bindings[variant]=rows[0]
    observations=[]
    for s in setups:
        model,seen=model_for(s)
        if old.evaluate(s[0],model)!=[True,False,True,True,True]:raise ValueError('Unknown truth was executed')
        if not seen or any(value!=syntax(s[3]) for value in seen):raise ValueError('Adoption did not receive the evaluated description')
        observations.append(sorted(set(seen)))
        model,_=model_for(s,variant='unknown_criterion')
        normonly=json.loads(json.dumps(s[0]));normonly['statements']=normonly['statements'][:1]+normonly['statements'][2:3]
        if old.evaluate(normonly,model)!=[True,True]:raise ValueError('Norms evaluated the unknown criterion')
        try:old.evaluate(s[0],model)
        except ValueError as exc:
            if 'Criterion interpretation missing' not in str(exc):raise
        else:raise ValueError('Unknown criterion replaced')
    return dict(cases=cases,description_variants=variants,binding_contrasts=bindings,
        observed_adoption_descriptions=observations,standalone_agrees=True,dynamic_and_specialized_agree=True,
        specialization=[s[-1] for s in setups],exact_description_comparison=True,
        list_length_not_used_for_adoption=True,unknown_criterion_refused=True,norms_do_not_execute_target=True,
        unassessed_message_truth_and_personal_endorsement_not_executed=True,
        arbitrary_criterion_extensional_equivalence_decided=False)


def refusal_checks(text):
    results={}
    try:parse(text+'q[e[r[p hzbi]][r[p hzbi]]].')
    except ValueError as exc:
        if 'disquot' not in str(exc).lower():raise
        results['dynamic_constructor_cannot_be_quoted']=str(exc)
    else:raise ValueError('Dynamic disquotation became quotable')
    doc=candidate(text,EXTRA)
    try:specialize_definition(doc,'hzbi','hzbk',{})
    except ValueError as exc:
        if 'Disquotation is not statically' not in str(exc):raise
        results['unknown_standard_cannot_be_specialized']=str(exc)
    else:raise ValueError('Unknown standard was guessed')
    return results


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='nach dem Symbol der Kirche, der er dient'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous adopted standard range')
    start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['rfw','hzbi'],status='partial',review_ja='同じ組織の採用基準の記述を、そのまま評価対象の基準列にも使う。既知の閉じた記述で特殊化し、規範対象として引用する。具体的な教理、基準の正当性・完全性、全文意味一致は未完。')],
        semantic_completion=False,new_source_characters=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored adopted standard differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Standard roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_adopted_standards.py','scripts/check_adopted_standards.py','scripts/check_prescribed_teaching.py',
        'scripts/check_office_speech.py','noema/specialization.py','noema/description_templates.py','noema/finite_semantics.py',
        'noema/extraction.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_same_description_adoption_and_criterion_evaluation',documents=documents,sizes=sizes,
        identity=identity_checks(texts[1:]),refusals=refusal_checks(texts[2]),alignment=alignment(),
        new_definitions=2,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Adopted standard report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Exact adopted descriptions and statically quoted teaching targets checked')


if __name__=='__main__':main()
