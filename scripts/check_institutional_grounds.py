"""Check used grounds, supported grounds and nonfactive paired reports."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded,callbacks
from scripts.compose_institutional_voice import VOICE,TEACHES
from scripts.compose_institutional_grounds import ROOT,PARENT,BUILDERS,INSTITUTIONAL

REPORT=ROOT/'reports/institutional-grounds-v1.json'
EXTRA=('r za[] a.r zb[] a.r zc[] a.r zd[a] c.r ze[] d.r zf[] '+INSTITUTIONAL+'.r zg[a d] c.'
    'd zh[subject a] f[j s[b context[k zg[v subject v context]]]].'
    'd zi[subject a] f[j s[b context[k zg[v subject v context]]]].'
    'd zj[subject a] f[j q[b context[k zg[v subject v context]]]].'
    'r zk[] a.r zl[] a.r zm[] a.r zn[] a.r zo[a] c.r zp[] '+VOICE+'.r zq[] '+TEACHES+'.'
    'r zr[a a i[h[a] f] d] c.')
ARGS='k za[] k zb[] k zc[] r[p zh] p zd k ze[] k zf[]'
QUERIES=''.join('q[k '+name+'['+ARGS+']].' for name in ('hzbs','hzbt','hzbu'))
DOMAIN=('organization','judgment','topic','r1','r2','r3','other','speaker','teachingreport','groundsreport','office','listener')
SCENES=('now','elsewhere')


def replace(node,old,new):
    if node==old:return new
    if isinstance(node,dict):return {n:replace(x,old,new) for n,x in node.items()}
    if isinstance(node,list):return [replace(x,old,new) for x in node]
    return node


def call(name):return quoted('call',name)['body']


def model_for(doc,bits=(True,)*7,variant='baseline',members=('r1','r2'),third_used=False,third_support=False):
    institutional,about,examined,first,second,firstsupport,secondsupport=bits
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='elsewhere' if label=='context' else 'other'
        return list(actual)==expected
    def belongs(principal,judgment,context):
        return institutional and match((principal,judgment,context),('organization','judgment','now'),
            'institution',('principal','judgment','context'))
    def considered(judgment,subject,message,context):
        return examined and match((judgment,subject,context),('judgment','topic','now'),
            'examined',('judgment','subject','context')) and message.syntax==syntax(quoted('function_ref',
                'zi' if variant=='examined_alias' else 'zj' if variant=='examined_force' else 'zh'))
    def used(judgment,reason,context):
        if variant=='other_judgment_ground' and (judgment,reason,context)==('other','r3','now'):return True
        if variant=='other_context_ground' and (judgment,reason,context)==('judgment','r3','elsewhere'):return True
        if not match((judgment,context),('judgment','now'),'used',('judgment','context')):return False
        return first and reason=='r1' or second and reason==('r3' if variant=='used_reason' else 'r2') or third_used and reason=='r3'
    def support(reason,judgment,context):
        if not match((judgment,context),('judgment','now'),'support',('judgment','context')):return False
        return firstsupport and reason=='r1' or secondsupport and reason==('r3' if variant=='support_reason' else 'r2') or third_support and reason=='r3'
    model=guarded(doc)
    model.update(za=lambda:'organization',zb=lambda:'judgment',zc=lambda:'topic',zd=lambda reason:reason in members,
        ze=lambda:'now',fb=lambda judgment,subject,context:about and match((judgment,subject,context),
            ('judgment','topic','now'),'about',('judgment','subject','context')),hzv=considered,fc=used,fd=support,
        zk=lambda:'speaker',zl=lambda:'teachingreport',zm=lambda:'groundsreport',zn=lambda:'office',zo=lambda person:person=='listener')
    callbacks(doc,model,{'zf':belongs})
    return model


def evaluate(doc,model):
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{name:value for name,value in model.items() if name in used},DOMAIN,SCENES)


def grounds_checks(texts):
    docs=[candidate(text,EXTRA+QUERIES) for text in texts]
    cases=[]
    for bits in product((False,True),repeat=7):
        used=all(bits[:5]);supported=used and all(bits[5:])
        expected=[used,supported,used]
        rows=[evaluate(doc,model_for(doc,bits)) for doc in docs]
        if rows!=[expected]*2:raise ValueError('Use of grounds became support: '+repr((bits,rows)))
        cases.append(dict(states=list(bits),results=expected))
    variants=[category+'_'+field for category,fields in (
        ('institution',('principal','judgment','context')),('about',('judgment','subject','context')),
        ('examined',('judgment','subject','context')),('used',('judgment','reason','context')),
        ('support',('reason','judgment','context'))) for field in fields]+['examined_alias','examined_force',
        'other_judgment_ground','other_context_ground']
    contrasts={}
    for variant in variants:
        expected=[True,False,True] if variant.startswith('support_') else [True]*3 if variant.startswith('other_') else [False]*3
        rows=[evaluate(doc,model_for(doc,variant=variant)) for doc in docs]
        if rows!=[expected]*2:raise ValueError('Ground reference differs: '+repr((variant,rows)))
        contrasts[variant]=expected
    scopes=[]
    for members,third_used,third_support,expected in (
        ((),False,False,[False]*3),(('r1',),False,False,[True,True,False]),(('r2',),False,False,[True,True,False]),
        (('r1','r2'),False,False,[True]*3),(('r1','r2','r3'),False,False,[False]*3),
        (('r1','r2'),True,False,[True,True,False]),(('r1','r2','r3'),True,False,[True,False,True]),
        (('r1','r2','r3'),True,True,[True]*3)):
        rows=[evaluate(doc,model_for(doc,members=members,third_used=third_used,third_support=third_support)) for doc in docs]
        if rows!=[expected]*2:raise ValueError('Ground range/exhaustiveness differs')
        scopes.append(dict(members=list(members),third_used=third_used,third_support=third_support,results=expected))
    for doc in docs:
        m=model_for(doc);m['fd']=guarded(doc)['fd']
        selected={**doc,'statements':[doc['statements'][0],doc['statements'][2]]}
        if evaluate(selected,m)!=[True,True]:raise ValueError('Use/exhaustiveness evaluated support')
        for name in ('zf','fb','hzv','fc','fd'):
            missing=model_for(doc);missing[name]=guarded(doc)[name]
            try:evaluate(doc,missing)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown grounds relation replaced: '+name)
    return dict(cases=cases,binding_contrasts=contrasts,scope_cases=scopes,standalone_agrees=True,
        use_and_exhaustiveness_do_not_require_support=True,unknown_relations_refused=True,
        human_judgment_and_inner_truth_not_executed=True,logical_proof_validity_established=False)


def report_setup(text,inner='zh'):
    doc=candidate(text,EXTRA)
    teaching=apply_description(doc,quoted('function_ref','rgd'),
        [quoted('call','za'),description(doc,'r[p zh]'),quoted('call','zq')])
    grounds=apply_description(doc,quoted('function_ref','hzbv'),
        [quoted('call','za'),quoted('call','zb'),description(doc,'r[p '+inner+']'),quoted('function_ref','zd'),quoted('call','zf')])
    def presentation(activity,message):
        arguments=[call('zk'),call(activity),call('za'),call('zn'),quoted('function_ref','zo')['body'],call('zc'),message,call('ze'),call('zp')]
        return {'kind':'ask','body':{'kind':'call','symbol':'hzbp','arguments':arguments}}
    template=parse('n:'+EXTRA+'q[t[o[c[s[r[p zh]]][k zc[]]]][k ze[]]].')
    truth=template['statements'][0]
    force_template=candidate(text,EXTRA+'q[e[c[k hzbv[k za[] k zb[] r[p zh] p zd k zf[]]][k zc[]]]'
        '[j s[b context[k hzbu[k za[] k zb[] k zc[] r[p zh] p zd v context k zf[]]]]]].')
    unquote=truth['body']['content']['message']['function']
    direct={'kind':'call','symbol':'hzbv','arguments':[call('za'),call('zb'),quoted('function_ref','zh'),quoted('function_ref','zd')['body'],call('zf')]}
    force=replace(force_template['statements'][0],direct,replace(unquote,quoted('function_ref','zh'),grounds))
    # The expected assertion shares the chosen inner description as well.
    force=replace(force,quoted('function_ref','zh'),quoted('function_ref',inner))
    endorse=parse('n:'+EXTRA+'q[k zr[k zk[] k zc[] r[p zh] k ze[]]].')['statements'][0]
    doc['statements']=[presentation('zl',teaching),presentation('zm',grounds),
        replace(truth,quoted('function_ref','zh'),teaching),replace(truth,quoted('function_ref','zh'),grounds),truth,endorse,force]
    return parse(format_graph(doc,'compact')),teaching,grounds


def report_model(setup,bits=(True,)*4):
    doc,teaching,grounds=setup;taught,grounded,truth,endorsed=bits
    model=model_for(doc,(grounded,True,True,True,True,False,False))
    messages={'teachingreport':syntax(teaching),'groundsreport':syntax(grounds)}
    def voiced(person,activity,principal,role,subject,message,context):
        return (person,principal,role,subject,context)==('speaker','organization','office','topic','now') and messages.get(activity)==message.syntax
    callbacks(doc,model,{'zp':voiced,'zq':lambda principal,subject,message,context:taught and
        (principal,subject,context)==('organization','topic','now') and message.syntax==syntax(quoted('function_ref','zh'))})
    model.update(dg=lambda activity,context:activity in messages and context=='now',
        f3=lambda person,activity,context:person=='speaker' and activity in messages and context=='now',
        f2=lambda activity,recipient,subject,message,context:(recipient,subject,context)==('listener','topic','now') and messages.get(activity)==message.syntax,
        zg=lambda subject,context:truth and (subject,context)==('topic','now'),
        zr=lambda person,subject,message,context:endorsed and (person,subject,context)==('speaker','topic','now') and message.syntax==syntax(quoted('function_ref','zh')))
    # Even a true report of reasons must not run the support relation.
    model['fd']=guarded(doc)['fd']
    return model


def report_checks(texts):
    setups=[report_setup(text) for text in texts]
    cases=[]
    for bits in product((False,True),repeat=4):
        expected=[True,True,*bits,True]
        rows=[evaluate(s[0],report_model(s,bits)) for s in setups]
        if rows!=[expected]*2:raise ValueError('Paired reports became factive: '+repr((bits,rows)))
        cases.append(dict(states=list(bits),results=expected))
    contrasts={}
    for inner in ('zi','zj'):
        alternatives=[report_setup(text,inner) for text in texts]
        rows=[evaluate(s[0],report_model(s)) for s in alternatives]
        if rows!=[[True,True,True,False,True,True,True]]*2:raise ValueError('Different inner report borrowed the old grounds')
        contrasts[inner]=rows[0]
    for s in setups:
        doc=s[0];model=report_model(s)
        for name in ('zf','fb','hzv','fc','zg','zr','zq'):model[name]=guarded(doc)[name]
        if evaluate({**doc,'statements':doc['statements'][:2]},model)!=[True,True]:raise ValueError('Reporting ran reported relations')
        try:evaluate({**doc,'statements':doc['statements'][:4]},model)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown reported relations supplied')
        for name in ('zf','fb','hzv','fc'):
            missing=report_model(s);missing[name]=guarded(doc)[name]
            try:evaluate({**doc,'statements':[doc['statements'][3]]},missing)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown relation inside the grounds report replaced: '+name)
        model=report_model(s);model['zg']=guarded(doc)['zg'];model['zr']=guarded(doc)['zr']
        if evaluate({**doc,'statements':doc['statements'][:4]},model)!=[True]*4:
            raise ValueError('True reports executed inner truth or personal endorsement')
        model=report_model(s);model['dg']=lambda *args:False
        if evaluate(doc,model)!=[False,False,True,True,True,True,True]:raise ValueError('Facts created report acts')
    return dict(cases=cases,inner_description_contrasts=contrasts,exact_presented_descriptions_evaluated=True,
        grounds_report_is_assertion=True,support_not_evaluated_by_reports=True,
        unknown_reported_relations_not_filled=True,inner_truth_and_endorsement_may_remain_unknown=True,
        reported_facts_do_not_create_report_acts=True,standalone_agrees=True)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='das sind die Beweisgründe, deren sie sich bedient'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous institutional grounds passage')
    start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['hzbs','hzbt','hzbu','hzbv'],status='partial',
        review_ja='組織に帰属する同じ判断・対象・発話と理由範囲を結ぶ。用いること、支持、一覧の完全性、外側の報告を分ける。証明としての地位・具体的内容・集団意思と指示・全文意味一致は未完。')],semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored institutional grounds differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Grounds roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_institutional_grounds.py','scripts/check_institutional_grounds.py','scripts/compose_institutional_voice.py',
        'scripts/check_assessed_payments.py','scripts/check_closed_policies.py','scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/finite_semantics.py','noema/description_templates.py','noema/extraction.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_institutional_grounds_and_nonfactive_reports',documents=documents,sizes=sizes,
        grounds=grounds_checks(texts[1:]),reports=report_checks(texts[1:]),alignment=alignment(),
        new_definitions=8,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Institutional grounds report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Institutional grounds, support, exact ranges and nonfactive paired reports checked')


if __name__=='__main__':main()
