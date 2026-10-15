"""Check object continuity, latent features and cover persistence in the depiction."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_covered_unfolding import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,build,basis
from scripts.check_faculty_opportunities import evaluate
from scripts.check_apparent_liberty import UNITS

REPORT=ROOT/'reports/covered-unfolding-v1.json'
DOMAIN=('object','other','process','wrongprocess','cover','othercover','nature','f1','f2')
SCENES=('start','middle','end','outside')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    text=format_graph(doc,'compact')+'''
r juobject[] a.r juprocess[] a.r justart[] d.r juend[] d.r jucover[] a.
r jutargettruth[a d] c.
d jutarget[object a] e[b point[k jutargettruth[v object v point]]].
'''
    args='k juobject[] k juprocess[] k justart[] k juend[] '
    args+='i[point d][k iaghistory[k juobject[] k juend[] v point]] '
    args+='i[left d right d][k iagbefore[k juobject[] k juend[] v left v right]] '
    args+='p iagtransitions p iagaffected i[feature a][k iagfeatures[k juobject[] k juend[] v feature]] p iaglatent p iagmanifest'
    text+='q[k rw4['+args+']].q[k rw5['+args+' k jucover[] p iagsurrounds p iagresistant]].'
    text+='q[t[k iagdepiction[k juobject[]]][k juend[]]].'
    text+='q[k iagframe[r[p jutarget]]].'
    return parse(text)


def forbidden(*args):raise AssertionError('Attribution executed the depicted or intended content')


def model(*,latent=3,initial=0,final=3,cover=7,hard=7,variant='baseline'):
    positions={'start':0,'middle':1,'end':2,'outside':3}
    def history(obj,anchor,point):
        if variant=='unknown_history':raise ValueError('Unknown history')
        return obj=='object' and anchor=='end' and point!='outside' and not (variant=='missing_start' and point=='start')
    def before(obj,anchor,left,right):
        if variant=='unknown_time':raise ValueError('Unknown order')
        if variant=='cyclic_order' and (left,right)==('end','start'):return True
        if variant=='incomparable' and {left,right}=={'start','middle'}:return False
        if variant=='reflexive_order' and left==right:return True
        return positions[left]<positions[right]
    def features(obj,anchor,f):
        if variant=='unknown_features':raise ValueError('Unknown feature scope')
        return obj=='object' and anchor=='end' and f in ('f1','f2') and variant!='empty_features'
    def islatent(obj,f,point):
        if variant=='unknown_latent':raise ValueError('Unknown latent feature')
        return obj==('other' if variant=='other_latent_object' else 'object') and point=='start' and f in ('f1','f2') and bool(latent&(1<<('f1','f2').index(f)))
    def manifest(obj,f,point):
        if variant=='unknown_manifest':raise ValueError('Unknown manifested feature')
        if obj==('other' if variant=='other_manifest_object' else 'object') and f in ('f1','f2'):
            bits=initial if point=='start' else final if point=='end' else 0
            return bool(bits&(1<<('f1','f2').index(f)))
        return False
    def surrounds(wrapper,obj,point):
        if variant=='unknown_cover':raise ValueError('Unknown cover')
        expected='othercover' if variant=='switched_cover' and point=='middle' else 'cover'
        return wrapper==expected and obj==('other' if variant=='other_covered_object' else 'object') and bool(cover&(1<<positions[point]))
    def resistant(wrapper,point):
        if variant=='unknown_resistance':raise ValueError('Unknown material response')
        return wrapper==('othercover' if variant=='other_resistant_cover' else 'cover') and bool(hard&(1<<positions[point]))
    def affected(process,obj,start,end):
        if variant=='unknown_process':raise ValueError('Unknown affected object')
        return (process,obj,start,end)==('wrongprocess' if variant=='other_affected_process' else 'process',
            'other' if variant=='other_affected_object' else 'object','start','end')
    return dict(juobject=lambda:'object',juprocess=lambda:'process',justart=lambda:'end' if variant=='reverse_endpoints' else 'start',
        juend=lambda:'end',jucover=lambda:'object' if variant=='self_cover' else 'cover',
        iaghistory=history,iagbefore=before,iagfeatures=features,iaglatent=islatent,iagmanifest=manifest,
        iagtransitions=lambda p,a,b:(p,a,b)==('wrongprocess' if variant=='other_transition_process' else 'process','start','end'),
        iagaffected=affected,iagsurrounds=surrounds,iagresistant=resistant,qb=lambda:'nature',
        df=lambda p,a,s:(p,a,s)==('wrongprocess' if variant=='other_agent_process' else 'process',
            'other' if variant=='other_agent' else 'nature','end'),
        dg=lambda p,s:(p,s)==('wrongprocess' if variant=='other_occurrence' else 'process','end'),
        jutargettruth=forbidden)


def values(*,indices=(0,1,2),memoize=True,**options):
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    primitives.update(model(**options))
    return evaluate(doc,primitives,DOMAIN,SCENES,memoize=memoize,budget=3_000_000)


def mapping(variant='baseline'):
    doc=deepcopy(fixture());doc['statements']=doc['statements'][-1:]
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def relation(node,author,target,depiction,context):
        return (node,author,context)==('node','author','mapping') and target.rank==depiction.rank==0 and (
            json.loads(target.syntax)==dict(kind='function_ref',symbol='jutarget') and
            json.loads(depiction.syntax)==dict(kind='function_ref',symbol='iagdepiction'))
    primitives.update(iagnode=lambda:'node',wa=lambda:'other' if variant=='author' else 'author',
        wh=lambda:'other' if variant=='context' else 'mapping',qa=relation)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN+('node','author'),situations=SCENES+('mapping','other'),primitives=primitives)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','mapping') and code.rank==1 and json.loads(code.syntax)==dict(kind='function_ref',symbol='iagframe')
    primitives.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'mapping',iagreport=report)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN+('node','author','scope'),situations=SCENES+('mapping','other'),primitives=primitives)]


CONTRASTS=('empty_features','missing_start','cyclic_order','incomparable','reflexive_order','other_latent_object',
    'other_manifest_object','switched_cover','other_covered_object','other_resistant_cover','other_affected_process',
    'other_affected_object','other_transition_process','other_agent_process','other_agent','other_occurrence')
UNKNOWNS=('unknown_history','unknown_time','unknown_features','unknown_latent','unknown_manifest','unknown_cover','unknown_resistance','unknown_process')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iagdepiction','iagframe','iagattribution'],adds_new_text_coverage=False,semantic_completion=False,
        unfilled_target=True,description_only=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for latent,initial,final in product(range(4),repeat=3):
        expected=latent==3 and initial!=3 and final==3
        assert values(latent=latent,initial=initial,final=final,indices=(0,1))==[expected]*2
    for cover,hard in product(range(8),repeat=2):
        assert values(cover=cover,hard=hard,indices=(0,1))==[True,cover==hard==7]
    assert values()==[True]*3
    assert values(initial=1)==[True]*3
    assert values(memoize=False)==[True]*3
    contrasts={name:values(variant=name) for name in CONTRASTS}
    assert all(not result[-1] for result in contrasts.values()),contrasts
    for name in UNKNOWNS:
        try:values(variant=name,indices=(2,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    assert mapping()==[True]
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_covered_unfolding.py',
        'scripts/check_covered_unfolding.py','tests/test_covered_unfolding.py','noema/constructed.py',
        'noema/constructed_semantics.py','noema/diagnostic_short_circuit.py','data/unfolding-reading-review-v1.json',
        'artifacts/unfolding-reading-v1/keim.html']
    return dict(status='covered_unfolding_depiction_template',documents=documents,feature_combinations=64,cover_combinations=64,
        contrasts=contrasts,source_alignment=alignment(),roundtrips=True,uncached_checked=True,step_budget=3_000_000,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Covered unfolding and unasserted figurative template verified')


if __name__=='__main__':main()
