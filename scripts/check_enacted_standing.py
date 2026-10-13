"""Separate a described role, its execution, appointment and evaluative conditions."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_rod_setup import guarded
from scripts import check_assumed_standing as assumed
from scripts.compose_assumed_standing import PREMISE_FIELDS,ALL_FIELDS,CONTEXT
from scripts.compose_enacted_standing import ROOT,PARENT,BUILDERS,generic_composed

REPORT=ROOT/'reports/enacted-standing-v1.json'


def setup(text):
    doc,payment,criticism=assumed.setup(text)
    for statement,target,fields in zip(doc['statements'],('hzba','hzbb','hzbc'),
        (PREMISE_FIELDS+CONTEXT,ALL_FIELDS+[('cases','h[d] c')],PREMISE_FIELDS+[('cases','h[d] c')])):
        call=statement['body'];call['symbol']=target
        del call['arguments'][[name for name,_ in fields].index('assumes')]
    doc=parse(format_graph(doc,'compact')+
        'q[k hza7[k zc[] k zd[] k zqa[] k zf[]]].q[k hzbd[k zc[] k zd[] k zqa[] k zf[]]].')
    return doc,payment,criticism


def model_for(doc,payment,criticism,bits=(True,True,False,True,True,True,True),variant='baseline'):
    positioned,executed,entrusted,failed,required,causal,sanction=bits
    model=assumed.model_for(doc,payment,criticism,(True,not failed,True,required,causal,sanction))
    model['zqb']=guarded(doc)['zqb']
    model['cb']=lambda person,activity,standing,context: positioned and (
        (person,activity,standing,context)==('other' if variant=='position_other_person' else 'person',
            'payment' if variant=='position_other_activity' else 'speech',
            'role' if variant=='position_other_standing' else 'standing',
            'causal' if variant=='position_other_context' else 'now') or
        variant=='additional_role' and (person,activity,standing,context)==('person','speech','role','now'))
    existing=model['cg']
    model['cg']=lambda person,activity,context: existing(person,activity,context) or executed and (
        person,activity,context)==('other' if variant=='execution_other_person' else 'person',
            'payment' if variant=='execution_other_activity' else 'speech',
            'causal' if variant=='execution_other_context' else 'now')
    model['cf']=lambda person,standing,context: entrusted and (person,standing,context)==(
        'other' if variant=='appointment_other_person' else 'person',
        'role' if variant=='appointment_other_standing' else 'standing',
        'causal' if variant=='appointment_other_context' else 'now')
    # The positive source models also keep the speech's presentation consistent
    # with actual execution; hypothetical later outcomes remain independent.
    for name in ('f2','f3'):
        inherited=model[name]
        model[name]=lambda *args,inherited=inherited:executed and inherited(*args)
    inherited_occurrence=model['dg']
    model['dg']=lambda act,scene:inherited_occurrence(act,scene) and (executed or (act,scene)!=('speech','now'))
    return model


def source_checks(texts):
    setups=[setup(text) for text in texts]
    rows=[]
    for bits in product((False,True),repeat=7):
        positioned,executed,entrusted,failed,required,causal,sanction=bits
        enacted=positioned and executed
        premise=enacted and failed and required
        expected=[premise,not premise or causal and sanction,premise,enacted,enacted and not entrusted]
        actual=[assumed.evaluate(doc,model_for(doc,payment,criticism,bits)) for doc,payment,criticism in setups]
        if actual!=[expected]*len(setups):raise ValueError('Role classification, execution or appointment collapsed: '+repr((bits,actual)))
        rows.append({'states':list(bits),'results':actual[0]})
    contrasts={}
    for name in ('position_other_person','position_other_activity','position_other_standing','position_other_context',
                 'execution_other_person','execution_other_activity','execution_other_context'):
        actual=[assumed.evaluate(doc,model_for(doc,payment,criticism,variant=name)) for doc,payment,criticism in setups]
        if actual!=[[False,True,False,False,False]]*len(setups):raise ValueError('Role enactment mismatch accepted: '+name+repr(actual))
        contrasts[name]=actual[0]
    for name in ('appointment_other_person','appointment_other_standing','appointment_other_context','additional_role'):
        bits=(True,True,name!='additional_role',True,True,True,True)
        actual=[assumed.evaluate(doc,model_for(doc,payment,criticism,bits,name)) for doc,payment,criticism in setups]
        if actual!=[[True]*5]*len(setups):raise ValueError('Appointment from another role/person/context was imported: '+name)
        contrasts[name]=actual[0]
    doc,payment,criticism=setups[0]
    model=model_for(doc,payment,criticism);model['cf']=guarded(doc)['cf']
    candidate={**doc,'statements':doc['statements'][:4]}
    if assumed.evaluate(candidate,model)!=[True]*4:raise ValueError('Criticism evaluation requires appointment information')
    candidate={**doc,'statements':doc['statements'][4:]}
    try:assumed.evaluate(candidate,model)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):raise
    else:raise ValueError('Unknown appointment silently treated as missing')
    unknowns=[]
    for name in ('cb','cg'):
        candidate={**doc,'statements':doc['statements'][3:4]}
        model=model_for(candidate,payment,criticism);model[name]=guarded(candidate)[name]
        try:assumed.evaluate(candidate,model)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
            unknowns.append(name)
        else:raise ValueError('Unknown role evidence silently replaced')
    parse(generic_composed()[0]+'q[e[r[p rfs]][r[p rfs]]].')
    return {'cases':rows,'contrasts':contrasts,'standalone_agrees':True,
        'old_assumption_and_quality_callbacks_not_executed':True,'evaluation_without_appointment_information':True,
        'unknown_appointment_refused_when_its_absence_is_queried':True,'unknown_role_evidence_refused':unknowns,
        'criticism_truth_and_normative_permission_not_executed':True,'role_enactment_can_be_quoted':True}


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='vorwitziger Tadel'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous source range')
    start=unit['text'].index(excerpt)
    return {'segments':[{'unit':unit['id'],'unit_sha256':unit['text_sha256'],'range':[start,start+len(excerpt)],
        'text':excerpt,'definitions':['hza7','hzba','hzbb','hzbc','hzbd'],'status':'partial',
        'review_ja':'立場を取る関係への入力を、既存の活動・立場の対応と本人の実行へ接続した読み。委任の有無を評価条件へ補わず、自発性・意図・語義の唯一性は未確定。'}],
        'semantic_completion':False,'voluntary_self_adoption_not_claimed':True}


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored enacted standing differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_enacted_standing.py','scripts/check_enacted_standing.py','scripts/check_assumed_standing.py',
        'scripts/check_situated_criticism.py','noema/finite_semantics.py','noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status':'partial_role_enactment_reading_distinct_from_appointment',
        'documents':documents,'sizes':sizes,'source':source_checks(texts[1:]),'alignment':alignment(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Enacted standing report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Role classification, actual execution and appointment checked independently')


if __name__=='__main__':main()
