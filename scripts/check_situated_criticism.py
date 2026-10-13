"""Check whole conditional bindings rather than disconnected clause predicates."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_public_assessment import syntax
from scripts.check_closed_policies import quoted
from scripts.compose_situated_criticism import ROOT,PARENT,BUILDERS,BASE,PREMISE,RESULT,ALL,CONTEXT,LINK

REPORT=ROOT/'reports/situated-criticism-v1.json'
SCENES=('now','causal','sanction','other')
CONSTANTS={'za':'authority','zb':'measure','zc':'person','zd':'speech','ze':'group','zm':'issuer','zn':'role',
    'zpa':'payment','zpc':'collector','zpd':'medium','zpf':'assessment'}
DOMAIN=tuple(CONSTANTS.values())+('reader','second','other')
PAYMENT='r[k hzah[k zpc[] k zpd[]]]'
CRITICISM='r[k rfd[l[h[a] e][p zpj] l[h[a] e][]]]'
EXPRESSIONS=dict(person='k zc[]',action='k zpa[]',role='k zn[]',issuer='k zm[]',payment=PAYMENT,
    speech='k zd[]',audience='p zpe',subject='k zpf[]',criticism=CRITICISM,charge='p zpg',quality='p zph',
    group='k ze[]',resistance='r[p zl]',authority='k za[]',measure='k zb[]',assessment='r[p zk]',
    adverse='p zh',intends='p zi',responds='p zj',causalprospects='p zg',sanctionprospects='p zpk',
    context='k zf[]',cases='p zpi')


def call(name,fields):
    return 'k '+name+'['+' '.join(EXPRESSIONS[n] for n,_ in fields)+']'


def setup(text):
    extra=''.join('r '+name+'[] a.' for name in CONSTANTS)+'''r zf[] d.
r zg[a d d] c.r zpk[a d d] c.r zh[a a d] c.r zi[a a a d] c.r zj[a a a a i[h[a] e] d] c.
r zk[a] e.r zl[a] e.r zpe[a] c.r zph[a] e.r zpi[d] c.r zpj[a] e.
r zpg[a a a a a i[h[a a] e] d] c.'''
    doc=candidate(text,extra)
    probe=parse(format_graph(doc,'compact')+'q[e['+PAYMENT+']['+PAYMENT+']].q[e['+CRITICISM+']['+CRITICISM+']].')
    payment,criticism=[syntax(s['body']['arguments'][0]) for s in probe['statements']]
    queries=[('hzax',BASE+CONTEXT),('hzay',PREMISE+CONTEXT),('hzaz',RESULT+CONTEXT),
        ('hza2',ALL+[('cases','h[d] c')]),('hza3',PREMISE+[('cases','h[d] c')])]
    return parse(format_graph(doc,'compact')+''.join('q['+call(name,fields)+'].' for name,fields in queries)),payment,criticism


def model_for(doc,payment,criticism,bits=(True,True,True,True,True,True),variant='baseline'):
    required,spoken,linked,quality,causal,sanction=bits
    model=guarded(doc)
    for name,value in CONSTANTS.items():model[name]=lambda value=value:value
    model['zf']=lambda:'now'
    contexts=('now','other') if variant=='mixed_cases' else ('now',)
    audience=() if variant=='empty_audience' else ('reader','second')
    model['zpe']=lambda person:person in audience
    model['zpi']=lambda context: context in (() if variant=='empty_cases' else ('other',) if variant=='inapplicable_cases' else contexts)
    model['h7a']=lambda issuer,person,role,action,desc,sign,context: required and sign and (
        issuer,person,role,action,desc.syntax)==('issuer','person','role','payment',payment) and context in contexts
    def charge(subject,issuer,person,role,action,desc,context):
        expected=['assessment','issuer','person','role','payment',payment]
        fields=('subject','issuer','person','role','action','description')
        if variant.startswith('charge_') and variant[7:] in fields:
            expected[fields.index(variant[7:])]='other'
        return linked and [subject,issuer,person,role,action,desc.syntax]==expected and context in (
            ('causal',) if variant=='charge_context' else contexts)
    model['zpg']=charge
    model['dg']=lambda act,scene:(spoken and (act,scene) in [('speech',ctx) for ctx in contexts]) or (
        causal and (act,scene)==('speech','causal'))
    model['f3']=lambda person,act,scene: spoken and (person,act)==(
        'other' if variant=='wrong_speaker' else 'person','speech') and scene in contexts
    def conveys(act,recipient,subject,desc,scene):
        expected_act='other' if variant=='split_speech' and recipient=='second' else 'speech'
        return spoken and (act,subject,desc.syntax)==(expected_act,
            'other' if variant=='wrong_topic' else 'assessment',
            syntax(quoted('function_ref','zk')) if variant=='wrong_message' else criticism) and recipient in audience and scene in (
                ('causal',) if variant=='speech_context' else contexts)
    model['f2']=conveys
    model['zph']=lambda act:Content(SCENES,tuple(quality and act==(
        'payment' if variant=='quality_of_other_action' else 'speech') and scene in contexts for scene in SCENES))
    model['zg']=lambda act,context,scene:causal and act==('payment' if variant=='causal_other_action' else 'speech') and context=='now' and scene=='causal'
    model['g3']=lambda act,group,desc,scene: causal and (act,group,desc.syntax,scene)==(
        'speech','group',syntax(quoted('function_ref','zl')),'causal')
    model['zl']=lambda group:Content(SCENES,tuple(causal and group=='group' and scene=='causal' for scene in SCENES))
    model['zpk']=lambda act,context,scene:sanction and (act,context,scene)==('measure','now','sanction')
    model['cg']=lambda person,act,scene:sanction and (person,act,scene)==('authority','measure','sanction')
    model['zh']=lambda act,person,scene:sanction and (act,person,scene)==('measure','person','sanction')
    model['zi']=lambda actor,act,person,scene:sanction and (actor,act,person,scene)==('authority','measure','person','sanction')
    model['zj']=lambda actor,act,person,offense,desc,scene:sanction and (actor,act,person,offense,desc.syntax,scene)==(
        'authority','measure','other' if variant=='sanction_other_person' else 'person',
        'payment' if variant=='sanction_other_offense' else 'speech',syntax(quoted('function_ref','zk')),'sanction')
    # Actual payment, truth of the criticism and punitive assessment, permission,
    # scholar role and public publication remain guarded and cannot be assumed.
    return model


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{k:v for k,v in model.items() if k in names},DOMAIN,SCENES)


def source_checks(texts):
    setups=[setup(text) for text in texts]
    rows=[]
    for bits in product((False,True),repeat=6):
        required,spoken,linked,quality,causal,sanction=bits
        base=required and spoken and linked; premise=base and quality; consequence=causal and sanction
        expected=[base,premise,consequence,not premise or consequence,premise]
        actual=[evaluate(doc,model_for(doc,payment,criticism,bits)) for doc,payment,criticism in setups]
        if actual!=[expected]*len(setups):raise ValueError('Whole-clause references changed: '+repr((bits,actual)))
        rows.append({'states':list(bits),'results':actual[0]})
    variants={name:[False,False,True,True,False] for name in (
        'empty_audience','wrong_speaker','wrong_topic','wrong_message','split_speech','speech_context',
        'charge_subject','charge_issuer','charge_person','charge_role','charge_action','charge_description','charge_context')}
    variants.update(quality_of_other_action=[True,False,True,True,False],causal_other_action=[True,True,False,False,True],
        sanction_other_person=[True,True,False,False,True],sanction_other_offense=[True,True,False,False,True],
        empty_cases=[True,True,True,False,False],inapplicable_cases=[True,True,True,True,False],
        mixed_cases=[True,True,True,False,True])
    contrasts={}
    for name,expected in variants.items():
        actual=[evaluate(doc,model_for(doc,payment,criticism,variant=name)) for doc,payment,criticism in setups]
        if actual!=[expected]*len(setups):raise ValueError('Situational binding contrast failed: '+name+repr(actual))
        contrasts[name]=actual[0]
    doc,payment,criticism=setups[0]
    model=model_for(doc,payment,criticism);model['zpg']=guarded(doc)['zpg']
    try:evaluate(doc,model)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):raise
    else:raise ValueError('Unknown levy-topic correspondence accepted')
    return {'cases':rows,'contrasts':contrasts,'standalone_agrees':True,
        'actual_payment_message_truth_permission_and_public_role_not_executed':True,
        'independent_causal_and_sanction_outcomes':True,'unknown_topic_correspondence_refused':True,
        'payment_description':json.loads(payment),'criticism_description':json.loads(criticism)}


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='ein vorwitziger Tadel solcher Auflagen, wenn sie von ihm geleistet werden sollen'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous situated criticism source range')
    start=unit['text'].index(excerpt)
    return {'segments':[{'unit':unit['id'],'unit_sha256':unit['text_sha256'],'range':[start,start+len(excerpt)],
        'text':excerpt,'definitions':['hzaw','hzax','hzay','hzaz','hza2','hza3'],'status':'partial',
        'review_ja':'同じ人・賦課・要求・批判・結果を仮定状況ごとに接続する。vorwitzigの評価性質を渡す位置を保持するが、その語義、Skandal、sogar、後続譲歩、制度の説明は未完。'}],
        'semantic_completion':False,'conditional_scope_is_explicit_interpretation':True}


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored situated criticism differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_situated_criticism.py','scripts/check_situated_criticism.py',
        'scripts/check_conditional_release.py','noema/finite_semantics.py','noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status':'partial_situated_criticism_conditional_with_shared_references',
        'documents':documents,'sizes':sizes,'source':source_checks(texts[1:]),'alignment':alignment(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Situated criticism report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Situated criticism, shared references and conditional scope checked')


if __name__=='__main__':main()
