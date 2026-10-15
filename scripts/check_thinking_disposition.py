"""Verify weighted orientation, its description identity, and two development readings."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_thinking_disposition import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,build,basis
from scripts.check_scoped_counts import arithmetic
from scripts.check_faculty_opportunities import evaluate
from scripts.check_apparent_liberty import UNITS

REPORT=ROOT/'reports/thinking-disposition-v1.json'
DOMAIN=('person','other','process','lean','call','norm','faculty','judgment','matter','reason','node','author','scope')
SCENES=('start','end','old','one','two','three','outside')
CASES=('one','two','three')
def forbidden(*args):raise AssertionError('Nonfactive orientation or attribution evaluated thinking or depiction')
def code_is(code,name,rank=0):return code.rank==rank and json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    return parse(format_graph(doc,'compact')+'''
r jtperson[] a.r jtanchor[] d.
q[k iahorientation[k jtperson[] k jtanchor[] u[e[n p a b][n p a b]]]].
q[t[k iahinner[k jtperson[]]][k jtanchor[]]].
q[t[k iahvocation[k jtperson[]]][k jtanchor[]]].
q[t[k iahthinking[k jtperson[]]][k jtanchor[]]].
q[k iahfamily[r b[p iahinner]]].q[k iahfamily[r b[p iahvocation]]].
q[k iahfamily[r b[p iahthinking]]].''')


def model(*,hits=3,classified=7,weights=(2,1,1),threshold=Fraction(1,2),urge=True,assigned=True,variant='baseline'):
    def points(person,anchor):
        if anchor=='start':return ('old',)
        if anchor!='end':return ()
        if variant=='empty':return ()
        if variant=='duplicate':return CASES+('one',)
        if variant=='omitted':return CASES[:2]
        if variant=='extra':return CASES+('outside',)
        return tuple(reversed(CASES)) if variant=='reordered' else CASES
    def correct(person,target):return person=='person' and code_is(target,'iahthinking')
    def scope(person,target,anchor,point):
        if variant=='unknown_scope':raise ValueError('Unknown occasion scope')
        if variant=='wrong_scope_target':return False
        return correct(person,target) and point in (('old',) if anchor=='start' else CASES if anchor=='end' else ())
    def assessed(person,target,anchor,point,impulse):
        if variant=='unknown_assessment':raise ValueError('Unknown orientation assessment')
        if variant=='unassessed_urge' and impulse:return False
        return correct(person,target) and (point=='old' or point in CASES and bool(classified&(1<<CASES.index(point))))
    def weight(person,target,anchor,point):
        if variant=='unknown_weight':raise ValueError('Unknown occasion weight')
        return Fraction(weights[CASES.index(point)] if point in CASES else 1)
    def orientation(person,target,point,impulse=False):
        if variant=='unknown_orientation':raise ValueError('Unknown orientation')
        if variant=='wrong_attitude_person':return person=='other'
        if variant=='wrong_attitude_target':return code_is(target,'iagdepiction')
        mask=(3 if urge else 0) if impulse else hits
        return correct(person,target) and point in CASES and bool(mask&(1<<CASES.index(point)))
    def relation(node,author,target,picture,context):
        if variant=='unknown_mapping':raise ValueError('Unknown figurative mapping')
        return (node,author,context)==('node','author','end') and any(code_is(target,n,1) for n in ('iahinner','iahvocation')) and code_is(picture,'iagdepiction',1)
    p={d['name']:forbidden for d in fixture()['declarations'] if d['kind']=='primitive'}
    p.update(arithmetic(variant=='bad_indicator'))
    p.update(jtperson=lambda:'person',jtanchor=lambda:'end',iahpoints=lambda p,a:SequenceValue(points(p,a),'"situation"'),
        iahscope=scope,iahclassified=assessed,iahweights=weight,
        iahfavor=lambda p,t,s:orientation(p,t,s),iahurge=lambda p,t,s:orientation(p,t,s,True),
        iahthreshold=lambda p,t,a,m:Fraction(threshold),iahsource=lambda:'norm',
        iahassigned=lambda source,p,t,a:assigned and (source,p,a)==('other' if variant=='other_assignment_source' else 'norm','person','end') and code_is(t,'iahthinking'),
        iahleanfeature=lambda:'lean',iahcallfeature=lambda:'lean' if variant=='same_features' else 'call',
        iahhistory=lambda p,a,t:(p,a)==('person','end') and t in ('start','end'),
        iahbefore=lambda p,a,l,r:(l,r)==('start','end'),
        iahtransitions=lambda p,l,r:(p,l,r)==('process','start','end'),
        iahaffected=lambda process,p,l,r:(process,p,l,r)==('process','other' if variant=='other_growth_person' else 'person','start','end'),
        iahlatent=lambda p,f,s:variant!='missing_latent' and p=='person' and f in ('lean','call') and s=='start',
        iahpresents=relation,iagnode=lambda:'node',wa=lambda:'author',wh=lambda:'end')
    return p


def values(*,indices=(0,1,2),memoize=True,**options):
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    return evaluate(doc,model(**options),DOMAIN,SCENES,memoize=memoize,budget=5_000_000)


def thinking(variant='baseline'):
    p=model();end='end'
    p.update(aa=lambda person:person=='person' and variant!='nonhuman',
        ab=lambda f,person,s:(f,person,s)==('faculty','other' if variant=='other_owner' else 'person',end),
        ac=lambda person,f,j,s:(person,f,j,s)==('person','faculty','judgment',end),
        fa=lambda person,j,s:variant!='no_judgment' and (person,j,s)==('person','judgment',end),
        fb=lambda j,m,s:(j,m,s)==('judgment','matter',end),
        fc=lambda j,r,s:(j,r,s)==('judgment','reason',end),
        fd=lambda r,j,s:variant!='unsupported' and (r,j,s)==('reason','judgment',end),
        ad=lambda other,person,j,s:variant=='guided' and (other,person,j,s)==('other','person','judgment',end))
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][3]]
    return evaluate(doc,p,DOMAIN,SCENES)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iahreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and code_is(code,'iahfamily',2))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=p)]


CONTRASTS=('empty','duplicate','omitted','extra','wrong_scope_target','wrong_attitude_person','wrong_attitude_target','bad_indicator')
UNKNOWNS=('unknown_scope','unknown_assessment','unknown_weight','unknown_orientation')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iahthinking','iahorientation','iahdevelopment','iahinner','iahvocation','iahfamily','iahattribution'],
        adds_new_text_coverage=False,semantic_completion=False,reading_unresolved=True,target_candidates=2)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for hits,classified in product(range(8),repeat=2):
        expected=classified==7 and sum(w for i,w in enumerate((2,1,1)) if hits&(1<<i))>=2
        assert values(hits=hits,classified=classified,indices=(0,))==[expected]
    candidates=[]
    for urge,assigned in product((False,True),repeat=2):
        result=values(urge=urge,assigned=assigned)
        assert result==[True,urge,assigned]
        candidates.append(dict(urge=urge,assigned=assigned,result=result))
    assert values(indices=(4,5,6))==[True,True,False]
    assert values(memoize=False)==values()
    for name in CONTRASTS:assert values(variant=name,indices=(0,))==[False],name
    for name in UNKNOWNS:
        try:values(variant=name,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    assert thinking()==[True]
    for variant in ('nonhuman','other_owner','no_judgment','unsupported','guided'):assert thinking(variant)==[False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_thinking_disposition.py','scripts/check_thinking_disposition.py',
        'tests/test_thinking_disposition.py','noema/constructed.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py',
        'data/thinking-disposition-reading-review-v1.json','artifacts/thinking-disposition-reading-v1/hang.html','artifacts/thinking-disposition-reading-v1/beruf.html']
    return dict(status='graded_orientation_and_two_nonfactive_development_readings',documents=documents,orientation_combinations=64,
        candidates=candidates,source_alignment=alignment(),roundtrips=True,uncached_baseline_checked=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Graded orientation and both development candidates verified; interpretation remains unresolved')


if __name__=='__main__':main()
