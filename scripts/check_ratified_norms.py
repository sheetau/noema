"""Verify confirmation, normative absence, scope and hypothetical contexts."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_policy_norms import seq
from scripts.check_rod_setup import guarded
from scripts.check_coordinate_correspondence import abstract
from scripts.compose_ratified_norms import ROOT,PARENT,BUILDERS,DESCRIPTION,RULE

REPORT=ROOT/'reports/ratified-norms-v1.json'
SCENES=('now','first','second')
PEOPLE=('source','other','person','personb','role','entrya','entryb','acta','actb','authoritya','authorityb')
# Explicit signatures make the quotation targets available in each fixture.
EXTRA='r ja[] a.r jb[] a.r jc[] a.r jd[] d.r je[] j[a].'
EXTRA+='r jr[a a a '+DESCRIPTION+' j[a] c d] c.r js[a a a '+DESCRIPTION+' j[a] c d] c.'
EXTRA+='r jt[a] c.r ju[a] a.r jv[a] a.r jw[a '+DESCRIPTION+' '+DESCRIPTION+'] '+DESCRIPTION+'.r jx[a] j[a].'
EXTRA+='r jn[j[a] d] c.d jm[bindings j[a]] e[b scene[k jn[v bindings v scene]]].d jo[bindings j[a]] e[b scene[k jn[v bindings v scene]]].'
LOCAL='k ja[] k jb[] k jc[] r[p jm] k je[] k jd[] p jr p js'
SCOPED='k ja[] k jd[] p jr p js p jt p ju p jv i[entry a][k jw[v entry r[p jm] r[p jo]]] p jx'


def norm_model(doc,states=((False,)*4,(False,)*4),mask=(True,True),variant='baseline'):
    model=guarded(doc)
    def norm(source,person,role,description,bindings,sign,context,allowed):
        if (source,role,context)!=('source','role','now'):return False
        for i,(p,a,name) in enumerate((('person','acta','jm'),('personb','actb','jo'))):
            if person==p and symbol(description)==name and bindings.items==(p,a):return states[i][(2 if allowed else 0)+(0 if sign else 1)]
        return False
    def pick(entry,left,right):
        if variant=='unknown_allocation':raise ValueError('Target allocation missing')
        return right if (entry=='entryb')!=(variant=='alias') else left
    model.update(ja=lambda:'source',jb=lambda:'person',jc=lambda:'role',jd=lambda:'now',je=lambda:seq(('person','acta')),
        jr=lambda *a:norm(*a,False),js=lambda *a:norm(*a,True),
        jt=lambda entry:any(on and entry==name for on,name in zip(mask,('entrya','entryb'))),
        ju=lambda entry:('other' if variant=='person' else 'person') if entry=='entrya' else 'personb',
        jv=lambda entry:'other' if variant=='role' else 'role',jw=pick,
        jx=lambda entry:seq(('acta','person') if variant=='reordered' and entry=='entrya' else
            ('person','acta','other') if variant=='extra' and entry=='entrya' else
            ('person',) if variant=='missing' and entry=='entrya' else
            ('person','acta') if entry=='entrya' else ('personb','actb')))
    return model


def coverage_probe(text):
    doc=parse(text);decl=next(d for d in doc['declarations'] if d['name']=='rhs')
    body=decl['body'];parameters=deepcopy(decl['parameters'])
    for _ in range(4):
        if body['kind']!='forall':raise ValueError('Coverage lost a target quantifier')
        parameters.append(dict(name=body['variable'],sort=body['sort']));body=body['body']
    doc['declarations'].append(dict(kind='definition',name='jzz',parameters=parameters,result='truth',body=deepcopy(body)));doc['statements']=[]
    return parse(format_graph(doc,'compact')+EXTRA+'q[k jzz['+SCOPED+' k jb[] k jc[] r[p jm] k je[]]].')


def absence_checks(texts):
    docs=[candidate(text,EXTRA+'q[k rhp['+LOCAL+']].q[k rhr['+SCOPED+']].') for text in texts]
    cases=[]
    for bits in product((False,True),repeat=8):
        states=(bits[:4],bits[4:]);expected=[not any(states[0]),not any(bits)]
        rows=[values(doc,norm_model(doc,states),PEOPLE,SCENES) for doc in docs]
        if rows!=[expected]*len(docs):raise ValueError('Normative absence differs')
        cases.append(dict(states=[list(s) for s in states],results=expected))
    masks=[];states=((False,)*4,(False,False,True,False))
    for mask in product((False,True),repeat=2):
        rows=[values(doc,norm_model(doc,states,mask),PEOPLE,SCENES) for doc in docs]
        expected=[True,not mask[1]]
        if rows!=[expected]*len(docs):raise ValueError('Selected target scope ignored')
        masks.append(dict(selected=list(mask),results=expected))
    probes=[coverage_probe(text) for text in texts];coverage={}
    states=((True,False,False,False),(False,)*4)
    for variant in ('baseline','person','role','alias','reordered','extra','missing'):
        rows=[values(doc,norm_model(doc,states,variant=variant),PEOPLE,SCENES) for doc in probes]
        if rows!=[[variant=='baseline']]*len(docs):raise ValueError('Coverage target binding differs: '+variant)
        coverage[variant]=rows[0][0]
    for state in product((False,True),repeat=4):
        rows=[values(doc,norm_model(doc,(state,(False,)*4),mask=(False,False)),PEOPLE,SCENES) for doc in probes]
        if rows!=[[not any(state)]]*len(docs):raise ValueError('Missing requirement or permission was declared covered')
    for doc in docs:
        for primitive in ('jr','js','jt','jw'):
            model=norm_model(doc);model[primitive]=guarded(doc)[primitive]
            try:values(doc,model,PEOPLE,SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown norm or scope was filled in')
    return dict(cases=cases,selection=masks,coverage_contrasts=coverage,coverage_polarity_cases=16,
        coverage_clause_instantiated_not_full_completeness=True,standalone_agrees=True,
        target_truth_not_executed=True,unknown_norms_and_scope_refused=True)


CONFIRM_EXTRA='r jpa[] a.r jpb[] d.r jpc[a] c.r jpd[a a d] c.r jpe[d] c.r jpf[a d] c.'


def confirmation_checks(text):
    doc=candidate(text,CONFIRM_EXTRA+'q[k rhu[k jpa[] k jpb[] p jpc p jpd]].q[k rhv[k jpa[] p jpe p jpc p jpd p jpf]].q[k rhw[k jpa[] p jpe p jpc p jpd]].')
    rows=[]
    for approvals in product((False,True),repeat=4):
        for conditions in product((False,True),repeat=2):
            model=guarded(doc);confirmed=(approvals[0] and approvals[1],approvals[2] and approvals[3])
            model.update(jpa=lambda:'source',jpb=lambda:'first',jpc=lambda a:a in ('authoritya','authorityb'),
                jpd=lambda a,s,c:s=='source' and c in ('first','second') and a in ('authoritya','authorityb') and approvals[2*('first','second').index(c)+('authoritya','authorityb').index(a)],
                jpe=lambda c:c in ('first','second'),jpf=lambda s,c:s=='source' and c in ('first','second') and conditions[('first','second').index(c)])
            expected=[confirmed[0],all(not a or b for a,b in zip(confirmed,conditions)),any(confirmed)]
            actual=values(doc,model,PEOPLE,SCENES)
            if actual!=expected:raise ValueError('Confirmation became normative validity or actual fact')
            rows.append(dict(approvals=list(approvals),conditions=list(conditions),results=actual))
    contrasts={}
    for variant in ('empty_authorities','empty_candidates','other_source','one_candidate','unknown_confirmation','unknown_condition'):
        model=guarded(doc)
        model.update(jpa=lambda:'source',jpb=lambda:'first',jpc=lambda a:variant!='empty_authorities' and a in ('authoritya','authorityb'),
            jpd=lambda a,s,c:s==('other' if variant=='other_source' else 'source') and c in ('first','second'),
            jpe=lambda c:variant!='empty_candidates' and c in (('first',) if variant=='one_candidate' else ('first','second')),
            jpf=lambda s,c:c=='first')
        if variant.startswith('unknown_'):
            name='jpd' if variant=='unknown_confirmation' else 'jpf';model[name]=guarded(doc)[name]
            try:values(doc,model,PEOPLE,SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
                contrasts[variant]='refused';continue
            raise ValueError('Unknown concession condition filled in')
        actual=values(doc,model,PEOPLE,SCENES)
        expected=[False,True,False] if variant in ('empty_authorities','other_source') else [True,True,False] if variant=='empty_candidates' else [True,True,True]
        if actual!=expected:raise ValueError('Confirmation domain differs: '+variant)
        contrasts[variant]=actual
    return dict(cases=rows,contrasts=contrasts,no_actual_confirmation_inferred=True)


def source_checks(texts):
    extra='r jqa[] a.r jqe[] d.r jqb[d d] c.r jqc[a] c.r jqd[a a d] c.q[t[k hzcf[k jqa[] p jqb p jqc p jqd]][k jqe[]]].'
    docs=[abstract(candidate(text,extra),{'rhq'}) for text in texts];rows=[]
    for current,first,second,approved in product((False,True),repeat=4):
        results=[]
        for doc in docs:
            model=guarded(doc)
            model.update(jqa=lambda:'source',jqe=lambda:'now',jqb=lambda a,c:a=='now' and c in ('first','second'),jqc=lambda a:a in ('authoritya','authorityb'),
                jqd=lambda a,s,c:approved and s=='source' and c in ('first','second'),
                rhq=lambda source,context,required,allowed:source=='source' and dict(now=current,first=first,second=second)[context])
            results.append(values(doc,model,PEOPLE,SCENES))
        expected=[current and (not approved or first and second)]
        if results!=[expected]*len(docs):raise ValueError('Source concession differs')
        rows.append(dict(current=current,first=first,second=second,confirmed=approved,result=expected[0]))
    for doc in docs:
        model=guarded(doc);model.update(jqa=lambda:'source',jqe=lambda:'now',jqb=lambda a,c:True,jqc=lambda a:True,jqd=lambda *a:True)
        try:values(doc,model,PEOPLE,SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown full absence was certified')
    return dict(cases=rows,standalone_agrees=True,full_normative_absence_is_explicit_oracle=True,
        unknown_full_absence_refused=True,author_claim_added=False)


def structural_checks(doc):
    ds={d['name']:d for d in doc['declarations']}
    for symbol in ('rhq','rhs'):
        body=ds[symbol]['body']
        for _ in range(4):
            if body['kind']!='forall':raise ValueError('All normative targets must be quantified')
            body=body['body']
    refs=[dict(kind='variable',name=p['name']) for p in ds['hzce']['parameters']]
    expected=dict(kind='call',symbol='rhq',arguments=refs+[dict(kind='function_ref',symbol=n) for n in ('h7k','h7l')])
    if ds['hzce']['body']!=expected:raise ValueError('Source absence must cover required and allowed norms')
    refs=[dict(kind='variable',name=p['name']) for p in ds['rht']['parameters']]
    expected=dict(kind='and',arguments=[dict(kind='call',symbol=n,arguments=refs) for n in ('rhr','rhs')])
    if ds['rht']['body']!=expected:raise ValueError('Finite list lost its completeness condition')
    wrapped=ds['hzcf'];refs=[dict(kind='variable',name=p['name']) for p in wrapped['parameters']]
    content=wrapped['body']
    if content['kind']!='content':raise ValueError('Missing contextual content')
    body=content['body'];anchor=dict(kind='variable',name=content['variable'])
    if body['kind']!='and' or body['arguments'][1].get('symbol')!='rhv':raise ValueError('Missing hypothetical concession')
    scope=body['arguments'][1]['arguments'][1]
    if scope['kind']!='lambda' or len(scope['parameters'])!=1:raise ValueError('Missing anchored candidates')
    expected_scope=dict(kind='lambda',parameters=deepcopy(scope['parameters']),body=dict(kind='apply',function=refs[1],
        arguments=[anchor,dict(kind='variable',name=scope['parameters'][0]['name'])]))
    expected=dict(kind='and',arguments=[dict(kind='call',symbol='hzce',arguments=[refs[0],anchor]),
        dict(kind='call',symbol='rhv',arguments=[refs[0],expected_scope,refs[2],refs[3],dict(kind='function_ref',symbol='hzce')])])
    if body!=expected:raise ValueError('Concession changed source, anchor, authorities or condition')
    return dict(all_targets_quantified=True,complete_list_distinguished=True,source_norms_preserved=True,
        same_contract_and_anchored_candidates=True)


def unbounded_checks(text):
    rows={}
    for name,query in (('rhq','k rhq[k ja[] k jd[] p jr p js]'),('rhs','k rhs['+SCOPED+']'),('rht','k rht['+SCOPED+']')):
        doc=candidate(text,EXTRA+'q['+query+'].')
        try:values(doc,norm_model(doc),PEOPLE,SCENES)
        except ValueError as exc:
            if 'Cannot finitely quantify the description domain' not in str(exc):raise
            rows[name]=str(exc)
        else:raise ValueError('Full target domain replaced by a finite list')
    doc=parse(text);decl=next(d for d in doc['declarations'] if d['name']=='rhq');body=decl['body'];parameters=deepcopy(decl['parameters'])
    for _ in range(3):
        parameters.append(dict(name=body['variable'],sort=body['sort']));body=body['body']
    doc['declarations'].append(dict(kind='definition',name='jzz',parameters=parameters,result='truth',body=deepcopy(body)));doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+EXTRA+'q[k jzz[k ja[] k jd[] p jr p js k jb[] k jc[] r[p jm]]].')
    try:values(doc,norm_model(doc),PEOPLE,SCENES)
    except ValueError as exc:
        if 'Cannot finitely quantify the unbounded sequence domain' not in str(exc):raise
        rows['bindings']=str(exc)
    else:raise ValueError('All finite argument lists were sampled')
    return rows


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored ratified norms differ')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Ratified norm roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0013')
    segments=[]
    for phrase,names in (('null und nichtig',['hzce']),('und sollte er auch',['hzcf']),('bestätigt sein',['rhu','hzcf'])):
        if unit['text'].count(phrase)!=1:raise ValueError('Source phrase is not unique')
        start=unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=names))
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_ratified_norms.py','scripts/check_ratified_norms.py','noema/finite_semantics.py','noema/extraction.py',
        'scripts/check_conditional_release.py','scripts/check_described_appraisals.py','scripts/check_described_explanations.py',
        'scripts/check_policy_norms.py','scripts/check_rod_setup.py','scripts/check_coordinate_correspondence.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_confirmation_and_normative_absence',documents=documents,sizes=sizes,
        absence=absence_checks([texts[0],texts[2]]),confirmation=confirmation_checks(texts[0]),source=source_checks(texts[1:]),
        structure=structural_checks(doc),unbounded=unbounded_checks(texts[0]),alignment=dict(segments=segments,semantic_completion=False),
        new_definitions=10,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Ratified norms report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Confirmation, scoped normative absence, target completeness and hypothetical contexts checked')


if __name__=='__main__':main()
