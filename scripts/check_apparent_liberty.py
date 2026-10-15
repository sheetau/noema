"""Check fixed scopes and nonfactive opportunity comparisons in Kant's clause."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from noema.diagnostic_short_circuit import lower
from scripts.compose_apparent_liberty import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,build,basis

REPORT=ROOT/'reports/apparent-liberty-v1.json'
UNITS='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('p1','p2','a','b','ma','mb','higher','lower','role','assessor','node','author','scope','other')
SCENES=('anchor','view','other','h0','l0','h1','l1','h2','l2','win_a','win_b')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def inclusion(first,second,*,empty=False):
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''r japeople[a] c.r jaactivities[a a] c.
r jafirst[a a d] c.r jasecond[a a d] c.r jaanchor[] d.
q[k rwu[p japeople p jaactivities p jafirst p jasecond k jaanchor[]]].
q[k rwv[p japeople p jaactivities p jafirst p jasecond k jaanchor[]]].'''
    pairs=[('p1','a'),('p1','b'),('p2','a'),('p2','b')]
    def option(mask,person,activity,scene):
        return (person,activity) in pairs and bool(mask&(1<<pairs.index((person,activity))))
    primitives=dict(japeople=lambda p:not empty and p in ('p1','p2'),jaactivities=lambda p,a:a in ('a','b'),
        jafirst=lambda p,a,s:option(first,p,a,s),jasecond=lambda p,a,s:option(second,p,a,s),jaanchor=lambda:'anchor')
    return [r['value'] for r in evaluate_document(parse(text),individuals=('p1','p2','a','b'),situations=('anchor',),primitives=primitives)]


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    helper=parse('''p:r jaltruth[a a d] c.r jalgoal[a a d] c.r jalanchor[] d.r jalperson[] a.r jalactivity[] a.
d jaltarget[person a activity a] e[b scene[k jaltruth[v person v activity v scene]]].
d iactarget[activity a] i[h[a a] e][r[p jaltarget]].
d iacgoal[person a activity a] e[b scene[k jalgoal[v person v activity v scene]]].''')
    doc['declarations']=helper['declarations']+[d for d in doc['declarations'] if d['name'] not in ('iactarget','iacgoal')]
    text=format_graph(doc,'compact')
    questions=['k iaccivilgain[k jalanchor[]]','k iacmentalgain[k jalanchor[]]',
        't[k iacappearance[]][k jalanchor[]]','t[k iacadvantage[]][k jalanchor[]]',
        'e[r d[k iacappearance[]]][r d[k iacappearance[]]]',
        'k iachighermental[k jalperson[] k jalactivity[] k jalanchor[]]']
    return parse(text+''.join('q['+q+'].' for q in questions))


def model(*,civil_actual=True,civil_view=True,mental_actual=False,mental_view=True,selected=True,variant='baseline'):
    def forbidden(*args):raise AssertionError('Permission target or unrelated primitive evaluated')
    result={d['name']:forbidden for d in fixture()['declarations'] if d['kind']=='primitive'}
    pairs={'anchor':('h0','l0'),'view':('h1','l1'),'other':('h2','l2')}
    def point(view,side):return pairs.get(view,('h2','l2'))[side]
    def norm(source,person,role,activity,code,sign,scene):
        if variant=='unknown_norm':raise ValueError('Unknown permission')
        if json.loads(code.syntax)!=dict(kind='function_ref',symbol='jaltarget'):return False
        expected='other' if variant=='wrong_norm_source' else 'higher' if scene.startswith('h') else 'lower'
        if (source,role,sign)!=(expected,'other' if variant=='wrong_norm_role' else 'role',True):return False
        gain=civil_actual if scene in ('h0','l0') else civil_view if scene in ('h1','l1') else False
        return person in ('p1','p2') and (activity=='a' or activity=='b' and person=='p1' and scene.startswith('h') and gain)
    def available(person,method,scene):
        if variant=='unknown_methods':raise ValueError('Unknown methods')
        gain=mental_actual if scene in ('h0','l0') else mental_view if scene in ('h1','l1') else False
        return person in ('p1','p2') and scene in ('h0','l0','h1','l1','h2','l2') and (method=='ma' or method=='mb' and person=='p1' and scene.startswith('h') and gain)
    def outcome(person,method,start,end):return end==('win_a' if method=='ma' else 'win_b')
    def evaluated(person,method,start,end):
        return not (variant=='unassessed_new_method' and method=='mb') and outcome(person,method,start,end)
    def alternatives(person,code,anchor,candidate):
        if variant=='unknown_views':raise ValueError('Unknown appearance alternatives')
        expected='other' if variant=='wrong_assessor' else 'assessor'
        code_name='iacappearance' if variant=='wrong_description' else 'iacadvantage'
        return selected and person==expected and anchor==('other' if variant=='wrong_anchor' else 'anchor') and \
            json.loads(code.syntax)==dict(kind='call',symbol=code_name,arguments=[]) and \
            (candidate=='view' or variant=='mixed_views' and candidate=='other')
    result.update(iacpeople=lambda p:p in ('p1','p2') and variant!='empty_people',
        iaccivilactivities=lambda p,a:a in ('a','b'),iacmentalactivities=lambda p,a:a in ('a','b') and not (variant=='scope_excludes_gain' and a=='b'),
        iachigher=lambda view:point(view,1 if variant=='identical_sides' else 0),iaclower=lambda view:point(view,1),
        iacsource=lambda scene:'higher' if scene.startswith('h') else 'lower',iacrole=lambda p,a:'role',
        iacrequired=lambda *args:variant=='opposed' and args[3]=='b' and args[5] is False,
        iacallowed=norm,iacavailable=available,iacprospects=outcome,iacevaluated=evaluated,
        iacassessor=lambda:'assessor',iacalternatives=alternatives,
        jalgoal=lambda p,a,scene:scene==('win_a' if a=='a' else 'win_b'),
        jalanchor=lambda:'anchor',jalperson=lambda:'p1',jalactivity=lambda:'b')
    return result


def values(*,indices=(0,1,2,3,4,5),memoize=True,**options):
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    doc,primitives=lower(doc,model(**options))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives,
        max_steps=2_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Attribution evaluated its content')
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,code,scope,scene):
        return (node,author,scope,scene)==('node','author','scope','anchor') and code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol='iacappearance',arguments=[])
    primitives.update(iacnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iacscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='anchor' else 'anchor',iacreport=report)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives)]


def alignment():
    units=json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'];unit=next(u for u in units if u['id']=='kant-1784:u0017')
    phrase='Ein größerer Grad bürgerlicher Freiheit scheint der Freiheit des Geistes des Volks vortheilhaft'
    start=unit['text'].index(phrase)
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        segments=[dict(start=start,end=start+len(phrase),text=phrase)],definitions=['iaccivilgain','iacmentalgain','iacappearance','iacattribution'],
        semantic_completion=False,degree_reading='proper_inclusion_candidate',causal_benefit_not_established=True)


CONTRASTS=('empty_people','scope_excludes_gain','identical_sides','wrong_norm_source','wrong_norm_role','opposed',
    'wrong_assessor','wrong_description','wrong_anchor','mixed_views','unassessed_new_method')


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for first,second in product(range(16),repeat=2):assert inclusion(first,second)==[first&~second==0,first&~second==0 and first!=second]
    matrix=[]
    for flags in product((False,True),repeat=5):
        ca,cv,ma,mv,selected=flags;result=values(civil_actual=ca,civil_view=cv,mental_actual=ma,mental_view=mv,selected=selected)
        assert result==[ca,ma,ca and cv and mv and selected,ca and ma,True,ma],(flags,result)
        matrix.append(dict(flags=list(flags),result=result))
    contrasts={v:values(variant=v) for v in CONTRASTS};assert all(not row[2] for row in contrasts.values())
    for name in ('unknown_norm','unknown_methods','unknown_views'):
        assert values(variant=name,indices=(4,))==[True]
        try:values(variant=name,indices=(2,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','anchor'):assert attribution(path,variant)==[False]
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_apparent_liberty.py','scripts/check_apparent_liberty.py',
        'tests/test_apparent_liberty.py','noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='nonfactive_partial_inclusion_reading',documents=documents,inclusion_pairs_checked=256,matrix=matrix,contrasts=contrasts,
        roundtrips=True,source_alignment=alignment(),limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Fixed option inclusion, apparent advantage and actual opportunity distinguished')


if __name__=='__main__':main()
