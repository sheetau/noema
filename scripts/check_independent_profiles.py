"""Verify topic-bound profiles, incomplete evidence, and current-episode contrast."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
from noema.grammar import parse,format_graph
from noema.finite_semantics import SequenceValue,evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_independent_profiles import ROOT,PARENT,FULL,CORE,LIBRARY,PROFILE,MEANINGS,APPOINTS,build
from scripts.check_described_appraisals import candidate
from scripts.check_coordinate_correspondence import abstract
from scripts.check_scoped_counts import arithmetic
from scripts.check_rod_setup import guarded
from scripts.check_appointed_thinkers import judgment_checks

REPORT=ROOT/'reports/independent-profiles-v1.json'
SCENES=('now','future1','future2','a','b','c','outside')
DOMAIN=('p','q','r','topic','other','judgment','population','governed')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model,*,short=True,memoize=True):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    model={n:model[n] for n in names}
    if short:doc,model=lower(doc,model)
    return [x['value'] for x in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=10_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def generic_fixture():
    return candidate(text(LIBRARY),'''r jpfpoints[] j[d].r jpfcases[d] c.r jpfassessed[d] c.
r jpfresponse[d] c.r jpfweights[d] b.r jpfthreshold[] b.
q[k rqa[k jpfpoints[] p jpfcases p jpfassessed p jpfresponse p jpfweights k jpfthreshold[]]].''')


def generic_model(*,mask=3,classified=7,points=('a','b','c'),scope=('a','b','c'),weights=(1,1,1),threshold=Fraction(2,3),bad_indicator=False):
    model=guarded(generic_fixture());model.update(arithmetic(bad_indicator))
    model.update(jpfpoints=lambda:SequenceValue(points,'"situation"'),jpfcases=lambda s:s in scope,
        jpfassessed=lambda s:s in ('a','b','c') and bool(classified&(1<<('a','b','c').index(s))),
        jpfresponse=lambda s:s in ('a','b','c') and bool(mask&(1<<('a','b','c').index(s))),
        jpfweights=lambda s:Fraction(weights[('a','b','c').index(s)] if s in ('a','b','c') else 1),
        jpfthreshold=lambda:Fraction(threshold))
    return model


@lru_cache(None)
def generic_checks():
    count=0;doc=generic_fixture()
    for mask,classified in product(range(8),repeat=2):
        for weights in ((1,1,1),(2,1,1)):
            expected=classified==7 and sum(w for i,w in enumerate(weights) if mask&(1<<i))>=Fraction(2,3)*sum(weights)
            assert evaluate(doc,generic_model(mask=mask,classified=classified,weights=weights))==[expected]
            count+=1
    options={
        'one_success':({'mask':1},False),'all_success':({'mask':7},True),
        'boundary':({},True),'above_boundary':({'threshold':Fraction(3,4)},False),
        'zero_threshold':({'threshold':0},False),'over_one_threshold':({'threshold':Fraction(4,3)},False),
        'negative_threshold':({'threshold':-1},False),'missing_failed_case':({'points':('a','b')},False),
        'duplicate_success':({'points':('a','a','b','c')},False),'empty':({'points':(),'scope':()},False),
        'extra_case':({'points':('a','b','c','outside')},False),'unassessed_failure':({'classified':3},False),
        'zero_failed_weight':({'weights':(1,1,0)},False),'negative_weight':({'weights':(1,1,-1)},False),
        'bad_indicator':({'bad_indicator':True},False),'reverse_order':({'points':('c','b','a')},True),
        'scale_weights':({'weights':(5,5,5)},True),'fractional_scale':({'weights':(Fraction(1,3),)*3},True),
        'explicit_narrow_scope':({'points':('a',),'scope':('a',)},True),
    }
    rows={}
    for name,(kw,wanted) in options.items():
        actual=evaluate(doc,generic_model(**kw));assert actual==[wanted],(name,actual);rows[name]=wanted
    assert evaluate(doc,generic_model(),short=False,memoize=False)==[True]
    assert evaluate(doc,generic_model(mask=1),short=False,memoize=False)==[False]
    return dict(truth_cases=count,contrasts=rows,unlowered_uncached_positive_and_negative_agree=True,
        narrow_scope_not_generalized=True,nonphysics_example='responses to independently specified equipment test conditions')


@lru_cache(None)
def fixture(path=CORE):
    providers=''.join('r jpf'+n+t[1:]+'.' for n,t in PROFILE)
    extra='r jpfperson[] a.r jpfanchor[] d.r jpfpopulation[] a.r jpfgoverned[] a.r jpfappoint'+APPOINTS[1:]+'.r jpfguardian[a a d] c.'
    extra+='r jpffuture[d] c.r jpfhistory[d] c.r jpfbefore[d d] c.'
    profile=' '.join('p jpf'+n for n,t in PROFILE)
    group='k jpfpopulation[] k jpfgoverned[] k jpfanchor[] p jpfappoint p jpfguardian '+profile
    queries='q[k hzhh[k jpfperson[] k jpfanchor[] '+profile+']].q[k hzhc[k jpfperson[] k jpfanchor[]]].'
    queries+='q[k hzhi['+group+']].q[k hzhj['+group+' p jpffuture p jpfhistory p jpfbefore]].'
    # The judgment and appointment definitions are separately covered by the
    # pinned predecessor. All new profile, topic and quantifier bodies execute.
    return abstract(candidate(text(path),providers+extra+queries),{'h5c','hzhb'})


def model(doc,variant='baseline'):
    values=guarded(doc);values.update(arithmetic());people=('p','q','r')
    anchors=('now','future1','future2')
    def correct(person,anchor):return person in people and anchor in (('outside',) if variant=='wrong_anchor' else anchors)
    def points(person,anchor):
        base=('a','b','c')
        if variant=='omitted_failure':base=('a','b')
        if variant=='duplicate_success':base=('a','a','b','c')
        return SequenceValue(base,'"situation"')
    def assessed(person,anchor,scene):
        if variant=='unknown_assessment':raise ValueError('unknown assessment')
        return correct(person,anchor) and scene in ('a','b','c') and not(variant=='unassessed_failure' and scene=='c')
    def independent(person,judgment,scene):
        if variant=='unknown_judgment':raise ValueError('unknown judgment')
        if judgment!='judgment' or person not in people:return False
        if variant=='actual_only':return scene=='now'
        if variant=='wrong_person':return person=='r' and scene in ('a','b')
        if variant in ('one_profile','split_people') and person!='p':return False
        return scene in (('a',) if variant=='one_success' else ('a','b'))
    def appointed(person,governed,anchor,*args):
        return governed=='governed' and anchor in anchors and person in (('q',) if variant=='split_people' else
            ('p',) if variant=='one_appointed' else ('q','r') if variant=='changing_people' and anchor=='future2' else ('p','q'))
    values.update(jpfperson=lambda:'p',jpfanchor=lambda:'now',jpfpopulation=lambda:'population',jpfgoverned=lambda:'governed',
        jpfpoints=points,jpfcases=lambda p,a,s:correct(p,a) and s in ('a','b','c'),jpfassessed=assessed,
        jpfweights=lambda p,a,s:Fraction(0 if variant=='zero_failed_weight' and s=='c' else 1),
        jpfthreshold=lambda p,a:Fraction(3,4) if variant=='strict_threshold' or variant=='other_person_threshold' and p=='q' else Fraction(2,3),
        jpftopics=lambda p,a,s:'other' if variant=='wrong_topic' or variant=='lost_future_profile' and a=='future2' else 'topic',
        jpfpresented=lambda p,t,s:variant!='not_presented' and p in people and t=='topic' and s in ('a','b','c'),
        jpffuture=lambda s:s in (() if variant=='empty_future' else ('future1','future2')),
        jpfhistory=lambda s:s in anchors,jpfbefore=lambda a,b:a in anchors and b in anchors and anchors.index(a)<anchors.index(b),
        aa=lambda p:p in people,mp=lambda g:SequenceValue(('p','q','r') if variant=='changing_people' else ('p','q'),'"individual"'),
        hzhb=appointed,h5c=independent,fb=lambda j,t,s:j=='judgment' and t==('other' if variant=='judgment_other_topic' else 'topic'))
    # These parameters are passed through to the separately interpreted hzhb.
    values.update(jpfappoint=lambda *args:False,jpfguardian=lambda *args:False)
    return values


@lru_cache(None)
def source_checks():
    cases={n:[False,False,False,False] for n in ('wrong_anchor','wrong_person','wrong_topic','judgment_other_topic',
        'not_presented','one_success','omitted_failure','duplicate_success','unassessed_failure','zero_failed_weight','strict_threshold')}
    cases.update(baseline=[True,False,True,True],actual_only=[False,True,False,False],one_profile=[True,False,False,False],
        one_appointed=[True,False,False,False],split_people=[True,False,False,False],empty_future=[True,False,True,False],
        changing_people=[True,False,True,True],lost_future_profile=[True,False,True,False],other_person_threshold=[True,False,False,False])
    rows={}
    for path in (CORE,FULL):
        doc=fixture(path);rows[path]={}
        selected=cases if path==CORE else {n:cases[n] for n in ('baseline','actual_only','split_people','changing_people','lost_future_profile')}
        for name,wanted in selected.items():
            actual=evaluate(doc,model(doc,name));assert actual==wanted,(path,name,actual);rows[path][name]=actual
    refused=[];doc=fixture()
    for name in ('unknown_assessment','unknown_judgment'):
        try:evaluate(doc,model(doc,name))
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(name)
        else:raise AssertionError(name)
    # A direct profile uses the same stored definitions with no diagnostic
    # lowering; do not equate the lowerer's unused-error behavior with eager IO.
    direct=deepcopy(doc);direct['statements']=direct['statements'][:2]
    assert evaluate(direct,model(direct),short=False,memoize=False)==[True,False]
    return dict(cases=rows,unknown_inputs_refused=refused,unlowered_uncached_profile_agrees=True,
        integration_boundary='existing h5c judgment and hzhb appointment interpreted; all six new definitions execute',
        actual_anchor_episode_not_required=True)


def structure():
    old=parse(text(PARENT));doc=parse(text(FULL));assert doc['statements']==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)
    assert extract_document(doc,roots=['hzhc','hzhi','hzhj'],statement_indices=[]).document==parse(text(CORE))
    return dict(new_definitions=len(added),new_primitives=0,new_assertions=0,previous_15_statements_unchanged=True)


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    for p in (FULL,CORE,LIBRARY):
        doc=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('-basis-v1.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            formatted=format_graph(doc,notation);assert parse(formatted)==parse(transcribe(formatted,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    alignment=json.loads(text('reports/appointed-thinkers-v1.json'))['alignment']
    for row in alignment['segments']:
        row['definitions']=['hzhg','hzhh','hzhi','hzhj'];row['status']='partial_assessed_response_profile_candidate'
        row['remaining'].append('scope selection and counterfactual validity of the finite response profile')
    paths=set(files)|{PARENT,'data/kant-appointed-thinkers-basis-v1.json','reports/appointed-thinkers-v1.json',
        'examples/v014/appointed-thinkers-core.noema','data/appointed-thinkers-core-basis-v1.json',
        'artifacts/written-units-v1/kant-1784.json','tests/test_independent_profiles.py','docs/independent-profiles-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_independent_profiles','check_independent_profiles','compose_appointed_thinkers',
        'check_appointed_thinkers','compose_origin_clock','compose_limits','compose_situated_criticism','check_described_appraisals',
        'check_rod_setup','check_coordinate_correspondence','check_scoped_counts'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script',
        'diagnostic_short_circuit','constructed_discourse'))
    return dict(status='partial_assessed_response_profile_not_general_disposition',document=FULL,basis_audits=audits,
        generic=generic_checks(),source=source_checks(),actual_judgment=judgment_checks(),structure=structure(),alignment=alignment,
        diagnostic_lowering='pure total Boolean branches only; stored documents unchanged; eager uncached comparisons included',
        roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Assessed profiles, shared topics and current-episode separation checked',flush=True)


if __name__=='__main__':main()
