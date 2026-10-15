"""Check requirement identity, prospective compliance and explicit coverage limits."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_scoped_obedience import ROOT, LIBRARY, EXAMPLE, BASIS, INHERITED, PARENT, build, basis

REPORT=ROOT/'reports/scoped-obedience-v1.json'
DOMAIN=('p','q','x','y','c','d','e','f')
SCENES=('anchor','later')

@lru_cache(maxsize=2)
def setup(restricted=False):
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))
    if restricted:
        # This diagnostic limits only the description quantifier. The stored
        # Noema retains its full domain; a direct evaluation must be refused.
        alias=deepcopy(next(d for d in doc['declarations'] if d['name']=='joa'));alias['name']='joalias'
        doc['declarations'].append(alias)
        prefix=[d for d in doc['declarations'] if d['kind']=='primitive' or d['name'] in ('joa','job','joalias')]
        doc['declarations']=prefix+[d for d in doc['declarations'] if d not in prefix]
        node=next(d for d in doc['declarations'] if d['name']=='rtx')['body']['body']['body']
        assert node['kind']=='forall' and node['sort']['kind']=='description'
        instances=[]
        for symbol in ('joa','job','joalias'):
            instances.append(dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],
                body=deepcopy(node['body'])),arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=symbol))]))
        node.clear();node.update(kind='and',arguments=[instances[0],dict(kind='and',arguments=instances[1:])])
        doc=parse(format_graph(doc,'compact'))
    return doc

def values(bits=(True,True,True,False,True,False),variant='baseline',*,restricted=False,indices=(0,1,2,5),memoize=True):
    doc=deepcopy(setup(restricted));doc['statements']=[doc['statements'][i] for i in indices]
    existsa,existsb,nowa,nowb,latera,laterb=bits
    def forbidden(*args):raise AssertionError('Unrelated permission or action primitive executed')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def code_name(code):return json.loads(code.syntax)['symbol']
    def action(item):return 'c' if item=='x' or variant=='conflicting' else 'd'
    def requirement(source,person,role,activity,code,sign,point):
        if variant=='unknown_requirement':raise ValueError('Unknown requirement')
        rows=[]
        if existsa:rows.append(('q','p','q','c','joa',True,'anchor'))
        if existsb:rows.append(('q','p','q','c' if variant=='conflicting' else 'd','joa' if variant=='conflicting' else 'job',False,'anchor'))
        changes={'wrong_source':(0,'x'),'wrong_person':(1,'x'),'wrong_role':(2,'x'),
                 'wrong_activity':(3,'e'),'wrong_description':(4,'joalias'),'wrong_sign':(5,False),'wrong_anchor':(6,'later')}
        if variant in changes and rows:
            index,value=changes[variant];row=list(rows[0]);row[index]=value;rows[0]=tuple(row)
        extras={'unlisted_activity':(3,'e'),'unlisted_description':(4,'joalias'),'unlisted_sign':(5,False),
                'other_source':(0,'x'),'other_person':(1,'x'),'other_context':(6,'later'),'outside_role':(2,'x'),'unlisted_role':(2,'x')}
        if variant in extras:
            row=list(('q','p','q','c','joa',True,'anchor'));index,value=extras[variant];row[index]=value;rows.append(tuple(row))
        return (source,person,role,activity,code_name(code),sign,point) in rows
    def actual(which,person,activity,point):
        if variant=='unknown_execution':raise ValueError('Unknown execution')
        if (person,activity)!=('p','c' if which==0 else 'd'):return False
        return ((nowa,latera) if which==0 else (nowb,laterb))[SCENES.index(point)]
    model.update(jdsource=lambda:'q',joperson=lambda:'p',jdanchor=lambda:'anchor',jolater=lambda:'later',
        joscope=lambda role:role=='q' or (variant=='unlisted_role' and role=='x'),
        joitems=lambda item:variant!='empty_items' and item in ('x','y'),joroles=lambda item:'q',joactions=action,
        josigns=lambda item:item=='x',jochoose=lambda item,first,second:first if item=='x' or variant=='conflicting' else second,
        jorequired=requirement,jofirst=lambda person,activity,point:actual(0,person,activity,point),
        josecond=lambda person,activity,point:actual(1,person,activity,point))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=30_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]

def full_domain_refused():
    for index in (3,4):
        try:values(indices=(index,))
        except ValueError as error:
            assert 'description domain' in str(error),str(error)
        else:raise AssertionError('Full description domain was silently limited')
    return True

def build_report():
    documents={}
    for name,text in build().items():
        assert (ROOT/name).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[name]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for bits in product((False,True),repeat=6):
        a,b,na,nb,la,lb=bits;result=values(bits)
        assert result==[True,a and b and na and not nb,a and b and la and not lb,True]
        matrix.append(dict(bits=bits,result=result))
    contrasts={name:values(variant=name) for name in ('wrong_source','wrong_person','wrong_role','wrong_activity','wrong_description','wrong_sign','wrong_anchor','conflicting')}
    assert all(r==[True,False,False,True] for r in contrasts.values())
    coverage={}
    for name,expected in [('baseline',True),('empty_items',False),('unlisted_activity',False),('unlisted_description',False),
        ('unlisted_sign',False),('unlisted_role',False),('other_source',True),('other_person',True),('other_context',True),('outside_role',True)]:
        result=values(variant=name,restricted=True,indices=(3,));assert result==[expected],(name,result);coverage[name]=result
    combined=[]
    for a,b,la,lb in product((False,True),repeat=4):
        result=values((a,b,True,False,la,lb),restricted=True,indices=(3,4))
        assert result==[True,a and b and la and not lb]
        combined.append(dict(requirements=[a,b],execution=[la,lb],result=result))
    for actual in (False,True):
        assert values((True,True,actual,False,actual,False),variant='conflicting',restricted=True,indices=(3,4))==[True,False]
    empty=values((False,False,False,False,False,False),variant='empty_items',restricted=True,indices=(3,4))
    assert empty==[True,True]
    assert values(variant='unknown_execution',restricted=True,indices=(3,))==[True]
    for variant in ('unknown_execution','unknown_requirement'):
        assert values(variant=variant,indices=(0,5))==[True,True]
    assert values(memoize=False)==values()
    paths=[LIBRARY,EXAMPLE,BASIS,INHERITED,PARENT,'scripts/compose_scoped_obedience.py','scripts/check_scoped_obedience.py',
        'tests/test_scoped_obedience.py','noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    result=dict(status='explicit_scoped_compliance_not_complete_obedience_semantics',documents=documents,new_definitions=4,new_primitives=0,
        roundtrips=True,matrix=matrix,contrasts=contrasts,coverage=dict(restricted_descriptions=['joa','job','joalias'],
        cases=coverage,combined_content=combined,known_empty_requirements=empty,full_domain_refused=full_domain_refused(),full_domain_verified=False),
        limitations=basis()['limitations'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Scoped requirements, compliance, quotation and explicit full-domain refusal verified')

if __name__=='__main__':main()
