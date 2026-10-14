"""Audit fixed interpretations, existential derivatives and quoted presentation."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded,callbacks
from scripts.compose_equation_presentation import ROOT,PARENT,BUILDERS,RELATIONS,FIXED,CUT,CASES,BINDINGS,INPUTS,QUOTE,SOURCE_ASSERTION

REPORT=ROOT/'reports/equation-presentation-v1.json'
DOMAIN=('author','earlier','node','scope','other')


def structural_checks(doc):
    defs={d['name']:d for d in doc['declarations']}
    witness=defs['senw'];body=witness['body']
    if body['kind']!='exists' or body['body']['kind']!='call' or body['body']['symbol']!='senv':raise ValueError('Derivative witness must be existential')
    mapping={name:p['name'] for (name,_),p in zip(BINDINGS,witness['parameters'],strict=True)}
    mapping['newelectricjet']=body['variable']
    expected=[dict(kind='variable',name=mapping[name]) for name,_ in INPUTS]
    if body['body']['arguments']!=expected:raise ValueError('Existential witness lost shared referents')
    content=defs['senx'];relations={name:p['name'] for (name,_),p in zip(FIXED,content['parameters'],strict=True)}
    if content['result']!='content' or content['body']['kind']!='content':raise ValueError('Presentation needs content, not truth')
    mapping=relations|{'context':content['body']['variable']};body=content['body']['body'];count=0
    sorts={name:p['sort'] for (name,_),p in zip(BINDINGS,witness['parameters'],strict=True)}
    for name,_ in CASES:
        if body['kind']!='forall' or body['sort']!=sorts[name] or body['variable'] in relations.values():raise ValueError('Interpretations became quantified cases')
        mapping[name]=body['variable'];count+=1;body=body['body']
    expected=[dict(kind='variable',name=mapping[name]) for name,_ in BINDINGS]
    if body!=dict(kind='implies',arguments=[dict(kind='call',symbol=s,arguments=expected) for s in ('senu','senw')]):
        raise ValueError('Source scope lost its conditional or shared parameters')
    return dict(case_parameters=count,fixed_interpretations=[n for n,_ in RELATIONS],fixed_light=True,existential_derivative_table=True,
        no_universal_claim_over_arbitrary_assignments=True,conditional_case_scope=True)


def generic_checks(text):
    fixture='r ja[] a.r jb[] a.r jc[] a.r jd[] a.r je[] d.r jf[d] c.d jg[] e[b ctx[k jf[v ctx]]].d jh[] e[b ctx[k jf[v ctx]]].'
    query=lambda content:'q[k seny[k jb[] k ja[] k jc[] k jd[] k je[] r[k '+content+'[]]]].'
    doc=candidate(text,fixture+query('jg')+query('jh')+'q[t[k jg[]][k je[]]].q[t[k jh[]][k je[]]].')
    rows=[]
    for present,explain,order,truth in product((False,True),repeat=4):
        model=dict(ja=lambda:'author',jb=lambda:'node',jc=lambda:'earlier',jd=lambda:'scope',je=lambda:'text',jf=lambda context:truth,
            uh=lambda node,author,content,scope,context:present and (node,author,scope,context)==('node','author','scope','text') and json.loads(content.syntax)==dict(kind='call',symbol='jg',arguments=[]),
            uf=lambda author,earlier,node,context:explain and (author,earlier,node,context)==('author','earlier','node','text'),
            ue=lambda earlier,node,context:order and (earlier,node,context)==('earlier','node','text'))
        actual=values(doc,model,DOMAIN)
        if actual!=[present and explain and order,False,truth,truth]:raise ValueError('Presentation became factive or extensional')
        rows.append(dict(present=present,explain=explain,order=order,truth=truth,results=actual))
    selfdoc=candidate(text,fixture+'q[k seny[k jb[] k ja[] k jb[] k jd[] k je[] r[k jg[]]]].')
    model.update(uh=lambda *a:True,uf=lambda *a:True,ue=lambda *a:True)
    if values(selfdoc,model,DOMAIN)!=[False]:raise ValueError('Self explanation passed a strict earlier-node condition')
    return dict(cases=rows,same_node_rejected=True,coextensive_descriptions_not_substituted=True)


def source_checks(text):
    doc=parse(text);statement=doc['statements'][-1]
    expected=statement['body']['arguments'][-1]['body']
    variants=('baseline','present_node','present_author','present_scope','present_context',
        'explain_author','explain_earlier','explain_node','explain_context','order_earlier','order_node','order_context')
    queries=SOURCE_ASSERTION.replace('s[','q[',1)
    for symbol,(_,sort) in zip(('jma','jmb','jmc'),RELATIONS):queries='r '+symbol+'[] '+sort+'.'+queries
    for old,new in (('zqd','jma'),('zqe','jmb'),('zqf','jmc')):
        queries+=SOURCE_ASSERTION.replace('s[','q[',1).replace('k '+old+'[]','k '+new+'[]')
    queries='r jmd[] '+CUT+'.'+queries+SOURCE_ASSERTION.replace('s[','q[',1).replace('k tc[]','k jmd[]')
    doc=candidate(text,queries);rows={}
    def model_for(variant):
        model=guarded(doc);model.update(rd=lambda:'author',zqa=lambda:'earlier',zqb=lambda:'node',zqc=lambda:'scope',ri=lambda:'text')
        def match(actual,want,category,labels):
            want=list(want)
            for i,label in enumerate(labels):
                if variant==category+'_'+label:want[i]='other'
            return list(actual)==want
        model.update(
            uh=lambda node,author,content,scope,context:match((node,author,scope,context),('node','author','scope','text'),'present',('node','author','scope','context')) and json.loads(content.syntax)==expected,
            uf=lambda author,earlier,node,context:match((author,earlier,node,context),('author','earlier','node','text'),'explain',('author','earlier','node','context')),
            ue=lambda earlier,node,context:match((earlier,node,context),('earlier','node','text'),'order',('earlier','node','context')))
        return model
    for variant in variants:
        actual=values(doc,model_for(variant),DOMAIN)
        if actual!=[variant=='baseline',False,False,False,False]:raise ValueError('Wrong source presentation binding: '+variant)
        rows[variant]=actual
    for name in ('uh','uf','ue'):
        model=model_for('baseline');model[name]=guarded(doc)[name]
        try:values(doc,model,DOMAIN)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unspecified discourse relation invented')
    return dict(cases=rows,quoted_quantity_electric_and_frame_relations_distinguished=True,
        content_and_physical_relations_not_executed=True,unknown_discourse_relations_refused=True)


def unbounded_check(text):
    query='q[t[k senx[k tc[] k zqd[] k zqe[] k zqf[]]][k ri[]]].'
    doc=candidate(text,query);model=guarded(doc);model['ri']=lambda:'text'
    def refuse(*args):raise ValueError('Physical relation executed before full-domain enumeration refusal')
    from scripts.check_tau_differential import ConstructedCuts
    cuts=ConstructedCuts();model['tc']=lambda:cuts.make(5)
    callbacks(doc,model,{name:refuse for name in ('zqd','zqe','zqf')})
    try:values(doc,model,DOMAIN)
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        return dict(rejected=True,reason=str(exc),finite_samples_not_a_universal_proof=True)
    raise ValueError('Unbounded physical content was finitely certified')


def source_alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    units={u['id']:u for u in source['units']};intro=units['einstein-1905:u0235']
    if intro['text']!='wobei':raise ValueError('Source introduction changed')
    old=json.loads((ROOT/'reports/density-referents-v1.json').read_text(encoding='utf-8'))
    formula=deepcopy(old['alignment']['segments'][0]);formula.update(definitions=['senw','senx','seny'],review_ja='固定した帰属の解釈と微分表の存在を持つ内容を、著者の範囲内提示へ結ぶ。現実の物理概念と単位全体の意味確認は未完。')
    return dict(segments=[dict(unit=intro['id'],unit_sha256=intro['text_sha256'],range=[0,len(intro['text'])],text=intro['text'],
        definitions=['seny'],status='explicit_interpretive_annotation',review_ja='先行の式へ付随関係を添えて説明する談話上の読み。wobeiの全用法を一つの関係に固定せず、先行式の内容や導出全体の完了には数えない。'),formula],semantic_completion=False)


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored presentation differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Presentation roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements'][:-1]!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_equation_presentation.py','scripts/check_equation_presentation.py','scripts/compose_kant_discourse.py',
        'scripts/compose_density_referents.py','scripts/check_comoving_labels.py','scripts/check_described_appraisals.py',
        'scripts/check_rod_setup.py','noema/finite_semantics.py','noema/extraction.py',
        'reports/density-referents-v1.json','artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_accompanying_equation_presentation',documents=documents,sizes=sizes,
        structure=structural_checks(doc),generic=generic_checks(texts[0]),source=source_checks(texts[1]),unbounded=unbounded_check(texts[1]),
        alignment=source_alignment(),new_definitions=3,new_primitives=8,new_author_statements=1,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Presentation report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Existential derivatives, fixed interpretations and accompanying presentation checked')


if __name__=='__main__':main()
