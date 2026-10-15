"""Check development, per-faculty opportunities and the connected liberty claim."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_faculty_opportunities import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,build,basis
from scripts.compose_qualified_utterance import closure
from scripts import check_assessed_barriers as previous

REPORT=ROOT/'reports/faculty-opportunities-v1.json'
DOMAIN=previous.DOMAIN+('fa','fb','a2','b2','ma2','mb2','da','db','dc')
SCENES=previous.SCENES+('growa','growb','growall','win_a2','win_b2')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def evaluate(doc,primitives,individuals,situations,*,memoize=True,budget=5_000_000):
    doc,primitives=lower(doc,primitives)
    return [row['value'] for row in evaluate_document(doc,individuals=individuals,situations=situations,primitives=primitives,
        max_steps=budget,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(maxsize=1)
def growth_fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jfgperson[] a.r jfgstart[] d.r jfgend[] d.
r jfgscope[a] c.r jfgearlier[d d] c.r jfgassessed[a a d] c.r jfgcapable[a a d] c.
q[k rwy[k jfgperson[] p jfgscope k jfgstart[] k jfgend[] p jfgearlier p jfgassessed p jfgcapable]].''')


def growth(first=1,last=3,*,assessed_before=True,assessed_after=True,ordered=True,variant='baseline',memoize=True):
    def capable(person,activity,scene):
        if variant=='unknown_capability':raise ValueError('Unknown capability')
        return person==('other' if variant=='wrong_person' else 'person') and activity in ('a','b') and bool((first if scene=='before' else last)&(1<<('a','b').index(activity)))
    primitives=dict(jfgperson=lambda:'person',jfgstart=lambda:'before',jfgend=lambda:'after',
        jfgscope=lambda a:a in ('a','b') and variant!='empty',jfgearlier=lambda a,b:ordered and (a,b)==('before','after'),
        jfgassessed=lambda p,a,s:assessed_before if s=='before' else assessed_after,jfgcapable=capable)
    return evaluate(growth_fixture(),primitives,('person','a','b','other'),('before','after'),memoize=memoize)


@lru_cache(maxsize=1)
def opportunities_fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jfoactor[] a.r jfostart[] d.r jfofaculties[a] c.
r jfotruth[a d] c.r jfoavailable[a a d] c.r jfooutcomes[a a d d] c.
d jfogoal[faculty a] e[b scene[k jfotruth[v faculty v scene]]].
q[k rwz[k jfoactor[] p jfofaculties p jfogoal k jfostart[] p jfoavailable p jfooutcomes p jfooutcomes]].
q[k rw2[k jfoactor[] p jfofaculties p jfogoal k jfostart[] p jfoavailable p jfooutcomes p jfooutcomes]].''')


def opportunities(*,first=True,second=True,joint=False,empty=False,memoize=True):
    methods={'m1':first,'m2':second,'mc':joint}
    primitives=dict(jfoactor=lambda:'person',jfostart=lambda:'start',jfofaculties=lambda f:not empty and f in ('f1','f2'),
        jfotruth=lambda f,s:s=='both' or (f,s) in (('f1','one'),('f2','two')),
        jfoavailable=lambda p,m,s:(p,s)==('person','start') and methods.get(m,False),
        jfooutcomes=lambda p,m,s,r:(p,s)==('person','start') and r=={'m1':'one','m2':'two','mc':'both'}.get(m))
    return evaluate(opportunities_fixture(),primitives,('person','f1','f2','m1','m2','mc'),('start','one','two','both'),memoize=memoize)


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(previous.fixture());doc['statements']=[];names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iaecontrast','iaetogether']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    questions=['k iaeindividual[k jalperson[] k jalanchor[] k iaclower[k jalanchor[]]]',
        'k iaetogether[k jalperson[] k jalanchor[] k iaclower[k jalanchor[]]]',
        'k iaeopportunities[k jalanchor[] k iaclower[k jalanchor[]]]','k iaeroom[k jalanchor[]]',
        't[k iaecontrast[]][k jalanchor[]]','e[r d[k iaecontrast[]]][r d[k iaecontrast[]]]']
    return parse(format_graph(doc,'compact')+''.join('q['+q+'].' for q in questions))


def model(*,first=True,second=True,joint=False,table=3,variant='baseline'):
    primitives=previous.model(table=table)
    old_available=primitives['iacavailable'];old_prospects=primitives['iacprospects'];old_evaluated=primitives['iacevaluated']
    def faculties(person,faculty,anchor):
        if variant=='unknown_faculties':raise ValueError('Unknown faculty scope')
        return person in ('p1','p2') and faculty in ('fa','fb') and anchor=='anchor' and variant!='empty_faculties' and not (variant=='missing_person_scope' and person=='p2')
    def tasks(person,faculty,activity,anchor):
        if variant=='unknown_tasks':raise ValueError('Unknown faculty tasks')
        if variant=='empty_tasks' and faculty=='fb':return False
        if variant=='wrong_task_anchor':return False
        return (anchor=='anchor' and person in ('p1','p2') and (faculty,activity) in (('fa','a'),('fa','a2'),('fb','b'),('fb','b2')))
    def available(person,method,scene):
        if variant=='unknown_methods':raise ValueError('Unknown method')
        if person in ('p1','p2'):
            if scene=='l0' and method in ('da','db','dc'):
                return {'da':first,'db':second,'dc':joint}[method] and not (variant=='other_person_lacks_room' and person=='p2' and method=='db')
            if scene in ('growa','growb','growall'):
                if method=='ma':return not (variant=='lost_old_ability' and scene in ('growa','growall'))
                if method=='mb':return person=='p1'
                if method=='ma2':return scene in ('growa','growall')
                if method=='mb2':return scene in ('growb','growall') and variant!='no_second_gain'
                if method=='unassessed':return variant in ('unknown_baseline','extra_unassessed_result_method') or variant=='first_person_unassessed_result_method' and person=='p1'
            if method=='unassessed' and scene=='l0' and variant=='unknown_baseline':return True
        return old_available(person,method,scene)
    def prospects(person,method,start,end):
        if method in ('da','db','dc'):return end=={'da':'growa','db':'growb','dc':'growall'}[method]
        if method in ('ma2','mb2'):return end=={'ma2':'win_a2','mb2':'win_b2'}[method]
        return old_prospects(person,method,start,end)
    def evaluated(person,method,start,end):
        if method=='unassessed':return False
        if variant=='unassessed_development' and method=='db':return False
        if method in ('da','db','dc','ma2','mb2'):return prospects(person,method,start,end)
        return old_evaluated(person,method,start,end)
    def earlier(start,end):
        if variant=='unknown_time':raise ValueError('Unknown time order')
        return variant!='reversed_time' and start=='l0' and end in ('growa','growb','growall')
    primitives.update(iaefaculties=faculties,iaetasks=tasks,iaeearlier=earlier,
        iacmentalactivities=lambda p,a:a in ('a','b','a2','b2') and not (variant=='task_outside_scope' and a=='b2'),
        iacavailable=available,iacprospects=prospects,iacevaluated=evaluated,
        jalgoal=lambda p,a,s:s=={'a':'win_a','b':'win_b','a2':'win_a2','b2':'win_b2'}.get(a))
    return primitives


def values(*,indices=(0,1,2,3,4,5),memoize=True,budget=10_000_000,**options):
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    return evaluate(doc,model(**options),DOMAIN,SCENES,memoize=memoize,budget=budget)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Attribution evaluated development or causal conditions')
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,code,scope,scene):
        return (node,author,scope,scene)==('node','author','scope','anchor') and code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol='iaecontrast',arguments=[])
    primitives.update(iacnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iacscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='anchor' else 'anchor',iaereport=report)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives)]


def alignment():
    units=json.loads((ROOT/previous.previous.UNITS).read_text(encoding='utf-8'))['units'];unit=next(u for u in units if u['id']=='kant-1784:u0017')
    phrase='ein Grad weniger von jener verschaft hingegen diesem Raum, sich nach allem seinen Vermögen auszubreiten'
    start=unit['text'].index(phrase)
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        segments=[dict(start=start,end=start+len(phrase),text=phrase)],definitions=['iaedevelopment','iaeopportunities','iaeroom','iaecontrast','iaeattribution'],
        semantic_completion=False,per_faculty_not_joint=True,development_reading='assessed_strict_inclusion_candidate')


CONTRASTS=('empty_faculties','missing_person_scope','empty_tasks','wrong_task_anchor','other_person_lacks_room',
    'lost_old_ability','no_second_gain','unknown_baseline','unassessed_development','reversed_time','task_outside_scope')
UNKNOWNS=('unknown_faculties','unknown_tasks','unknown_methods','unknown_time')


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for before,after in product(range(4),repeat=2):assert growth(before,after)==[before&~after==0 and before!=after]
    for a,b,t in product((False,True),repeat=3):assert growth(assessed_before=a,assessed_after=b,ordered=t)==[a and b and t]
    matrix=[]
    for first,second,joint in product((False,True),repeat=3):
        result=opportunities(first=first,second=second,joint=joint)
        assert result==[joint or first and second,joint]
        matrix.append(dict(first=first,second=second,joint=joint,result=result))
    assert values()==[True,False,True,True,True,True]
    assert values(joint=True)==[True]*6
    assert values(variant='first_person_unassessed_result_method')==[True,False,True,True,True,True]
    assert values(variant='extra_unassessed_result_method')==[True,False,False,False,False,True]
    assert growth(memoize=False)==growth() and opportunities(memoize=False)==opportunities()
    contrasts={name:values(variant=name,indices=(0,2,3)) for name in CONTRASTS}
    assert all(not row[-1] for row in contrasts.values()),contrasts
    assert values(table=2,indices=(0,2,3,4))==[True,True,False,False]
    for name in UNKNOWNS:
        assert values(variant=name,indices=(5,))==[True]
        try:values(variant=name,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','anchor'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,previous.previous.UNITS,'scripts/compose_faculty_opportunities.py',
        'scripts/check_faculty_opportunities.py','scripts/check_assessed_barriers.py','scripts/check_apparent_liberty.py',
        'tests/test_faculty_opportunities.py','noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='per_faculty_opportunities_for_assessed_growth',documents=documents,opportunity_matrix=matrix,contrasts=contrasts,
        source_alignment=alignment(),roundtrips=True,generic_uncached_checked=True,source_uncached_checked=False,source_step_budget=10_000_000,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Assessed development, per-faculty methods and the lower-regime opportunity verified')


if __name__=='__main__':main()
