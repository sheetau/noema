"""Verify scope, target identity, empty ranges and the outer norm distinction."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_policy_norms import seq
from scripts.check_rod_setup import guarded
from scripts.compose_scoped_liberty import ROOT, PARENT, BUILDERS, TRUE

REPORT=ROOT/'reports/scoped-liberty-v1.json'
SCENES=('now','elsewhere')
GENERIC_EXTRA='''r jva[] a.r jvb[] a.r jvc[] a.r jvd[] d.
r jve[a a a d] c.r jvf[a a a a i[h[a a] e] c d] c.r jvg[a a a a i[h[a a] e] c d] c.
r jvh[a i[h[a a] e] i[h[a a] e]] i[h[a a] e].r jvi[a a d] c.
d jvx[person a activity a] e[b point[k jvi[v person v activity v point]]].
d jvy[person a activity a] e[b point[k jvi[v person v activity v point]]].
'''
GENERIC_ARGS='k jva[] k jvb[] k jvc[] k jvd[] p jve i[act a][k jvh[v act r[p jvx] r[p jvy]]] p jvf p jvg'
GENERIC_DOMAIN=('source','person','role','acta','actb','other')


def generic_model(doc, states, mask=(True,True), variant='baseline'):
    model=guarded(doc)
    def norm(source,person,role,activity,description,sign,context,allowed):
        expected=['source','person','role','now']
        for i,name in enumerate(('source','person','role','context')):
            if variant=='norm_'+name:expected[i]='elsewhere' if name=='context' else 'other'
        if [source,person,role,context]!=expected or activity not in ('acta','actb'):return False
        index=('acta','actb').index(activity)
        target=('jvx','jvy')[index]
        if variant=='norm_alias':target=('jvy','jvx')[index]
        if symbol(description)!=target:return False
        return states[index][(2 if allowed else 0)+(0 if sign else 1)]
    def scope(person,activity,role,context):
        if variant=='scope_context':return False
        return (person,role,context)==('person','role','now') and any(flag and activity==name for flag,name in zip(mask,('acta','actb')))
    def choose(activity,left,right):
        # Values are issued by this interpretation from the two typed quotes.
        # Returning the received value preserves its identity and type checks.
        if variant=='unknown_target':raise ValueError('Unassessed target allocation')
        choice=left if activity=='acta' else right
        if variant=='swapped_targets':choice=right if activity=='acta' else left
        return choice
    model.update(jva=lambda:'source',jvb=lambda:'person',jvc=lambda:'role',jvd=lambda:'now',jve=scope,
        jvf=lambda *a:norm(*a,False),jvg=lambda *a:norm(*a,True),jvh=choose)
    return model


def expected(states,mask):
    selected=[state for state,on in zip(states,mask) if on]
    permitted=[];banned=[];conflicts=[];unclassified=[];choices=[]
    for rp,rn,ap,an in selected:
        p=ap and not rn
        b=rn and not rp and not ap
        conflict=(rp and rn) or (ap and rn) or (an and rp)
        permitted.append(p);banned.append(b);conflicts.append(conflict)
        unclassified.append(not conflict and not (p or b))
        choices.append(p and an and not rp)
    return [all(permitted),bool(selected) and all(permitted),any(banned),any(conflicts),any(unclassified),bool(selected) and all(choices)]


def generic_checks(texts):
    docs=[candidate(text,GENERIC_EXTRA+''.join('q[k '+name+'['+GENERIC_ARGS+']].' for name in ('rhi','rhj','rhk','rhl','rhm','rhn'))) for text in texts]
    def run(states,mask=(True,True),variant='baseline'):
        rows=[values(doc,generic_model(doc,states,mask,variant),GENERIC_DOMAIN,SCENES) for doc in docs]
        if any(row!=rows[0] for row in rows):raise ValueError('Generic and extracted liberty disagree')
        return rows[0]
    cases=[]
    for bits in product((False,True),repeat=8):
        states=(bits[:4],bits[4:]);row=run(states)
        if row!=expected(states,(True,True)):raise ValueError('Permission, prohibition, conflict or nonclassification collapsed')
        cases.append(dict(states=[list(s) for s in states],results=row))
    masks=[]
    for bits,mask in product(product((False,True),repeat=4),product((False,True),repeat=2)):
        states=((False,False,True,False),bits);row=run(states,mask)
        if row!=expected(states,mask):raise ValueError('Empty or selected liberty scope differs')
        masks.append(dict(states=[list(s) for s in states],selected=list(mask),results=row))
    contrasts={}
    states=((False,False,True,True),(False,False,True,True))
    for variant in ('norm_source','norm_person','norm_role','norm_context','norm_alias','swapped_targets','scope_context'):
        row=run(states,variant=variant)
        want=[True,False,False,False,False,False] if variant=='scope_context' else [False,False,False,False,True,False]
        if row!=want:raise ValueError('Normative target moved to a different binding: '+variant)
        contrasts[variant]=row
    for doc in docs:
        for name in ('jve','jvf','jvg','jvh'):
            model=generic_model(doc,states);model[name]=guarded(doc)[name]
            try:values(doc,model,GENERIC_DOMAIN,SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown normative interpretation supplied: '+name)
    return dict(norm_cases=cases,selection_cases=masks,binding_contrasts=contrasts,standalone_agrees=True,
                unknown_scope_norms_and_targets_refused=True,actual_target_truth_not_executed=True)


SOURCE_EXTRA='''r jva[] a.r jvb[] a.r jvc[] a.r jvd[] d.r jve[] a.r jvf[] a.
r jvg[] a.r jvh[] a.r jvi[] a.r jvj[] j[a].
d jvk[bindings j[a]] e[k hzcc[v bindings]].
d jvl[person a activity a] e[k zzq[v person v activity]].
'''
SOURCE_QUERIES=('q[k hzb6[k jva[] k jvb[] k jvc[] k jvd[]]].'
    'q[k hzb7[k jva[] k jvb[] k jvc[] k jvd[]]].'
    'q[k hzca[k jve[] k jvb[] k jvf[] k jvd[]]].'
    'q[k hzcb[k jva[] k jve[] k jvb[] k jvc[] k jvf[] k jvd[]]].'
    'q[k hzcd[k jvg[] k jvh[] k jvi[] k jva[] k jvb[] k jvc[] k jvd[]]].'
    'q[t[k hzcc[k jvj[]]][k jvd[]]].')
SOURCE_DOMAIN=('officesource','publicsource','person','officerole','publicrole','assessor','regulator','outeroffice',
               'oa','ob','pa','pb','audience','other')


def source_model(doc, private_allowed=True, private_banned=False, public_allowed=True, outer=True, variant='baseline',bindings=None):
    model=guarded(doc)
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='elsewhere' if label=='context' else 'other'
        return list(actual)==expected
    def norm(source,person,role,activity,desc,sign,context,allowed):
        if symbol(desc)!=('jvl' if variant=='inner_alias' else 'zzq'):return False
        office=activity in ('oa','ob');public=activity in ('pa','pb')
        if not (office or public):return False
        if not match((source,person,role,context),('officesource' if office else 'publicsource','person',
            'officerole' if office else 'publicrole','now'),'inner',('source','person','role','context')):return False
        if allowed:return sign and (private_allowed if office else public_allowed)
        return office and activity=='oa' and not sign and private_banned
    def outer_rule(source,person,role,desc,bindings,sign,context):
        target='jvk' if variant=='outer_alias' else 'hzcc'
        required_bindings=('officesource','person','officerole')
        if variant=='outer_reordered':required_bindings=('officesource','officerole','person')
        if variant=='outer_extra':required_bindings+=('other',)
        if variant=='outer_missing':required_bindings=required_bindings[:-1]
        return outer and sign==(variant=='outer_positive') and symbol(desc)==target and bindings.items==required_bindings and match(
            (source,person,role,context),('assessor','regulator','outeroffice','now'),'outer',('source','person','role','context'))
    model.update(jva=lambda:'officesource',jvb=lambda:'person',jvc=lambda:'officerole',jvd=lambda:'now',
        jve=lambda:'publicsource',jvf=lambda:'publicrole',jvg=lambda:'assessor',jvh=lambda:'regulator',jvi=lambda:'outeroffice',
        jvj=lambda:seq(bindings if bindings is not None else ('officesource','person','officerole')),
        ca=lambda person,act,context:(person,context)==('person','now') and (act in ('oa','ob') and variant!='empty_office' or act in ('pa','pb') and variant!='empty_public'),
        cb=lambda person,act,role,context:match((person,context),('person','now'),'position',('person','context')) and
            ((role=='officerole' and act in ('oa','ob')) or (role=='publicrole' and act in ('pa','pb'))),
        cf=lambda person,role,context:match((person,role,context),('person','officerole','now'),'delegation',('person','role','context')),
        cd=lambda role,context:(role,context)==('publicrole','now'),
        cc=lambda act,audience,context:act in ('pa','pb') and (audience,context)==('audience','now'),
        ce=lambda audience,context:(audience,context)==('audience','now'),
        h7a=lambda *a:norm(*a,False),h7b=lambda *a:norm(*a,True),h7k=outer_rule)
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:fn for n,fn in model.items() if n in used}


def source_checks(texts):
    docs=[candidate(text,SOURCE_EXTRA+SOURCE_QUERIES) for text in texts]
    def run(**options):
        rows=[values(doc,source_model(doc,**options),SOURCE_DOMAIN,SCENES) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Source and extracted norm scopes differ')
        return rows[0]
    cases=[]
    for pa,pb,pu,outer in product((False,True),repeat=4):
        freedom=pa and not pb;ban=pb and not pa
        row=run(private_allowed=pa,private_banned=pb,public_allowed=pu,outer=outer)
        if row!=[freedom,ban,pu,ban and pu,outer,freedom]:raise ValueError('Outer prohibition became actual restriction')
        cases.append(dict(private_allowed=pa,private_banned=pb,public_allowed=pu,outer=outer,results=row))
    contrasts={}
    for variant in ['outer_'+n for n in ('source','person','role','context','alias','reordered','extra','missing','positive')]:
        row=run(variant=variant)
        if row!=[True,False,True,False,False,True]:raise ValueError('Outer policy bindings collapsed: '+variant)
        contrasts[variant]=row
    for variant in ['inner_'+n for n in ('source','person','role','context','alias')]:
        row=run(variant=variant)
        if row!=[False,False,False,False,True,False]:raise ValueError('Inner norm target moved: '+variant)
        contrasts[variant]=row
    for variant,want in (
        ('empty_office',[True,False,True,False,True,True]),
        ('empty_public',[True,False,False,False,True,True]),
        ('delegation_person',[True,False,True,False,True,True]),
        ('delegation_role',[True,False,True,False,True,True]),
        ('delegation_context',[True,False,True,False,True,True])):
        row=run(variant=variant)
        if row!=want:raise ValueError('Source activity classification differs: '+variant)
        contrasts[variant]=row
    lengths=[]
    for bindings in ((),('officesource',),('officesource','person'),('officesource','person','officerole'),('officesource','person','officerole','other')):
        row=run(bindings=bindings)
        if row[-1]!=(len(bindings)==3):raise ValueError('Policy argument count truncated')
        lengths.append(dict(bindings=list(bindings),results=row))
    for doc in docs:
        outer_only={**doc,'statements':[doc['statements'][4]]}
        model=source_model(doc)
        for name in ('h7a','h7b','ca','cb','cf','cd','cc','ce'):model[name]=guarded(doc)[name]
        if values(outer_only,model,SOURCE_DOMAIN,SCENES)!=[True]:raise ValueError('Outer norm executed inner policy')
        for name in ('h7a','h7b','ca','cb','cf','cd','cc','ce','h7k'):
            model=source_model(doc);model[name]=guarded(doc)[name]
            try:values(doc,model,SOURCE_DOMAIN,SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown policy interpretation supplied: '+name)
    return dict(state_cases=cases,binding_contrasts=contrasts,length_cases=lengths,standalone_agrees=True,
        outer_norm_does_not_evaluate_inner_policy=True,execution_not_used_to_select_scope=True,unknown_relations_refused=True)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    segments=[]
    for excerpt,definitions in (
        ('als Priester, nicht frei, und darf es auch nicht sein',['hzb6','hzb7','hzcc','hzcd']),
        ('genießt einer uneingeschränkten Freiheit, sich seiner eigenen Vernunft zu bedienen',['rhi','rhj','rhn','hzca','hzcb'])):
        if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous scoped liberty source range')
        start=unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            definitions=definitions,status='explicit_interpretive_annotation',review_ja='自由の全意味を確定せず、活動範囲全体への許可と制限、およびその状態を対象とする外側の禁止として操作的な読みを部分記述する。原文の自由・自律・正当性・出所の同定は未完。'))
    return dict(segments=segments,semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored scoped liberty differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Scoped liberty roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_scoped_liberty.py','scripts/check_scoped_liberty.py','scripts/compose_described_norms.py',
        'scripts/check_conditional_release.py','scripts/check_described_appraisals.py','scripts/check_described_explanations.py',
        'scripts/check_policy_norms.py','scripts/check_rod_setup.py','noema/finite_semantics.py','noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_scoped_liberty_and_outer_negative_policy_requirement',documents=documents,sizes=sizes,
        generic=generic_checks(texts),source=source_checks(texts[1:]),alignment=alignment(),new_definitions=13,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args()
    report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Scoped liberty report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Scoped permissions, restrictions, unresolved classifications and outer policy requirement checked')


if __name__=='__main__':main()
