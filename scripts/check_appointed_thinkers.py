"""Check shared people, appointment witnesses and changing future witnesses."""
import argparse,hashlib,json,subprocess,sys
from functools import lru_cache
from fractions import Fraction
from itertools import product
from noema.grammar import parse,format_graph
from noema.finite_semantics import SequenceValue,evaluate_document
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_appointed_thinkers import ROOT,PARENT,FULL,CORE,LIBRARY,MEANINGS,APPOINTS,build
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_coordinate_correspondence import abstract

REPORT=ROOT/'reports/appointed-thinkers-v1.json'
DOMAIN=('p','q','issuer','role','event','judgment','population','governed','other')
SCENES=('past','anchor','first','second','outside')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model,domain=DOMAIN):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,
        primitives={n:model[n] for n in names},max_steps=10_000_000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def generic_checks():
    extra='r jm[a d] c.r js[a d] c.r jp[a d] c.r jt[d] c.r jzc[] d.'
    queries='q[k rpv[k jzc[] p jm p js p jp]].q[k rpw[k jzc[] p jm p js p jp]].'
    queries+=''.join('q[k '+n+'[p jt p jm p js p jp]].' for n in ('rpx','rpy','rpz'))
    doc=candidate(text(LIBRARY),extra+queries);rows=[]
    for bits in product((False,True),repeat=6):
        selected={person for i,person in enumerate(('p','q')) if all(bits[3*i:3*i+3])}
        model=guarded(doc);model.update(jzc=lambda:'first',jt=lambda s:s in ('first','second'))
        for name,index in (('jm',0),('js',1),('jp',2)):
            model[name]=lambda person,scene,index=index:person in ('p','q') and bits[3*('p','q').index(person)+index]
        wanted=[bool(selected),len(selected)>=2,bool(selected),bool(selected),len(selected)>=2]
        actual=evaluate(doc,model,('p','q'));assert actual==wanted;rows.append(actual)
    def run(scope,at):
        model=guarded(doc);model.update(jzc=lambda:'first',jt=lambda s:s in scope,
            jm=lambda person,scene:person in ('p','q'),js=lambda person,scene:person in ('p','q'),jp=lambda person,scene:person in at.get(scene,set()))
        return evaluate(doc,model,('p','q'))
    changing=run({'first','second'},{'first':{'p'},'second':{'q'}});assert changing==[True,False,True,False,False]
    empty=run(set(),{'first':{'p','q'}});assert empty==[True,True,False,False,False]
    missing=run({'first','second'},{'first':{'p','q'}});assert missing==[True,True,False,False,False]
    return dict(truth_cases=len(rows),changing_people=changing,empty_scope=empty,missing_later_witness=missing,
        domain_example='different qualified technicians on successive shifts')


@lru_cache(None)
def source_fixture(path=CORE):
    extra='r jza[] a.r jzb[] a.r jzc[] d.r jzd[d] c.r jze[d] c.r jzf[d d] c.r jzg['+APPOINTS[2:-3]+'] c.r jzh[a a d] c.'
    # h5c and ta have their own unabstracted checks below. This integration
    # layer executes all new appointment and quantifier definitions.
    queries='q[k hzhd[k jza[] k jzb[] k jzc[] p jzg p jzh]].q[k hzhe[k jza[] k jzb[] k jzc[] p jzg p jzh]].'
    queries+='q[k hzhf[k jza[] k jzb[] k jzi[] p jzd p jze p jzf p jzg p jzh]].'
    return abstract(candidate(text(path),extra+'r jzi[] d.'+queries),{'h5c','ta'})


def finite_order(history,before):
    points=tuple(p for p in SCENES if history(p))
    edges={(a,b) for a in points for b in points if before(a,b)}
    return bool(points) and all((p,p) not in edges for p in points) and all(
        (a,b) in edges or (b,a) in edges for a in points for b in points if a!=b) and all(
        (a,c) in edges for a,b in edges for b2,c in edges if b==b2)


def source_model(doc,variant):
    model=guarded(doc);population=('p','q')
    persons=('p','q','other') if variant=='changing_plural_people' else ('p','q')
    if variant=='changing_plural_people':population=persons
    if variant=='one_person':population=('p',)
    if variant=='duplicate_population':population=('p','p')
    if variant=='empty_population':population=()
    chronology=SCENES[:4];history=set(chronology)
    if variant=='missing_history_point':history.remove('first')
    scope={'first','second'}
    if variant=='empty_future_scope':scope=set()
    if variant=='scope_includes_anchor':scope.add('anchor')
    def before(a,b):
        if variant=='reflexive_order' and a==b=='past':return True
        if variant=='cyclic_order' and (a,b)==('second','past'):return True
        if variant=='incomparable_order' and {a,b}=={'first','second'}:return False
        return a in chronology and b in chronology and chronology.index(a)<chronology.index(b)
    def appoints(event,issuer,person,role,point):
        expected=('event','issuer',person,'role','past')
        if variant=='late_appointment':expected=('event','issuer',person,'role','anchor')
        if variant=='present_only_appointment':expected=('event','issuer',person,'role','first')
        if variant=='wrong_role':expected=('event','issuer',person,'other','past')
        if variant=='split_event':expected=('other','issuer',person,'role','past')
        if variant=='split_time':expected=('event','issuer',person,'role','anchor')
        return person in persons and (event,issuer,person,role,point)==expected and not(variant=='split_people' and person=='p')
    def entrusted(person,role,point):
        if person not in persons or role!='role':return False
        if variant=='past_only_role' and point!='past':return False
        if variant=='no_past_delegation' and point in ('past','anchor'):return False
        return point in chronology
    def thinking(person,judgment,point):
        if variant=='unknown_judgment':raise ValueError('missing judgment interpretation')
        if person not in persons or judgment!='judgment' or point not in ('first','second'):return False
        if variant=='split_people':return person=='p'
        if variant=='one_thinker':return person=='p'
        if variant=='lost_future_thinkers':return point=='first'
        if variant=='changing_people':return (person,point) in (('p','first'),('q','second'))
        if variant=='changing_plural_people':return (point=='first' and person in ('p','q')) or (point=='second' and person in ('q','other'))
        return True
    model.update(jza=lambda:'population',jzb=lambda:'governed',jzc=lambda:'first',jzi=lambda:'anchor',
        ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)),
        ta=finite_order,aa=lambda person:person in persons,mp=lambda group:SequenceValue(population if group=='population' else ('other',),'"individual"'),
        jzd=lambda point:point in scope,jze=lambda point:point in history,jzf=before,
        ia=lambda person,anchor,point:person in persons and point in history,
        ic=lambda first,last,anchor:before(first,last),
        dg=lambda event,point:event=='event' and point==('anchor' if variant=='late_appointment' else 'first' if variant=='present_only_appointment' else 'past'),
        cf=entrusted,jzg=appoints,jzh=lambda role,group,point:(role,group)==('role','other' if variant=='wrong_governed_group' else 'governed'),h5c=thinking)
    if variant=='unknown_appointment':model['jzg']=lambda *args:(_ for _ in ()).throw(ValueError('missing appointment interpretation'))
    return model


@lru_cache(None)
def source_checks():
    cases={n:[True,True,True] for n in ('baseline','late_appointment','changing_plural_people')}
    cases.update({n:[False,False,False] for n in ('duplicate_population','empty_population','wrong_role','split_event','split_time',
        'split_people','wrong_governed_group','past_only_role','no_past_delegation','present_only_appointment','missing_history_point',
        'reflexive_order','cyclic_order','incomparable_order')})
    cases.update({n:[True,False,False] for n in ('one_person','one_thinker','changing_people')})
    cases.update({n:[True,True,False] for n in ('empty_future_scope','scope_includes_anchor','lost_future_thinkers')})
    rows={}
    for path in (CORE,FULL):
        doc=source_fixture(path);rows[path]={}
        selected=cases if path==CORE else {n:cases[n] for n in ('baseline','split_people','split_time','changing_plural_people')}
        for name,wanted in selected.items():
            actual=evaluate(doc,source_model(doc,name));assert actual==wanted,(path,name,actual);rows[path][name]=actual
    refused=[];doc=source_fixture()
    for name in ('unknown_judgment','unknown_appointment'):
        try:evaluate(doc,source_model(doc,name))
        except ValueError as exc:assert 'missing' in str(exc);refused.append(name)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=refused,integration_boundary='h5c judgment and ta finite-order interpretations supplied; actual definitions separately executed below',
        appointing_event_and_current_role_executed=True,governed_group_not_identified_with_population=True)


@lru_cache(None)
def appointment_checks():
    extra='r jza[] a.r jzb[] a.r jzc[] a.r jzd[] d.r jzg['+APPOINTS[2:-3]+'] c.'
    doc=candidate(text(CORE),extra+'q[k hzha[k jza[] k jzb[] k jzc[] k jzd[] p jzg]].');rows={}
    interpreted=abstract(parse(format_graph(doc)),{'ta'})
    cases=('baseline','late_appointment','wrong_role','split_event','split_time','past_only_role',
        'no_past_delegation','present_only_appointment','missing_history_point',
        'reflexive_order','cyclic_order','incomparable_order')
    for name in cases:
        model=source_model(doc,name);model.update(jza=lambda:'p',jzb=lambda:'issuer',jzc=lambda:'role',jzd=lambda:'first')
        actual=evaluate(doc,model);assert actual==[name in ('baseline','late_appointment')],(name,actual)
        assert evaluate(interpreted,model)==actual
        rows[name]=actual[0]
    # Include an empty history explicitly: an order cannot be inferred from
    # vacuous pair/triple checks, even when no appointment is being tested.
    orderdoc=candidate(text(LIBRARY),'r jza[d] c.r jzb[d d] c.q[k ta[p jza p jzb]].')
    model=guarded(orderdoc);model.update(jza=lambda p:False,jzb=lambda a,b:False)
    assert evaluate(orderdoc,model)==[False] and not finite_order(model['jza'],model['jzb'])
    return dict(cases=rows,actual_hzha_rpt_ta_executed=True,finite_order_interpretation_agrees=True,empty_history_rejected=True)


@lru_cache(None)
def judgment_checks():
    doc=candidate(text(CORE),'r jza[] a.r jzb[] d.q[k hzhc[k jza[] k jzb[]]].');rows={}
    cases=('baseline','no_judgment','wrong_owner','missing_reason','wrong_supported_judgment','guided_by_other','self_guidance')
    for name in cases:
        model=guarded(doc);model.update(jza=lambda:'p',jzb=lambda:'first',aa=lambda person:person in ('p','q'),
            ab=lambda faculty,person,point:(faculty,person,point)==('role','q' if name=='wrong_owner' else 'p','first'),
            ac=lambda person,faculty,judgment,point:(person,faculty,judgment,point)==('p','role','judgment','first'),
            fa=lambda person,judgment,point:name!='no_judgment' and (person,judgment,point)==('p','judgment','first'),
            fb=lambda judgment,matter,point:(judgment,matter,point)==('judgment','governed','first'),
            fc=lambda judgment,reason,point:name!='missing_reason' and (judgment,reason,point)==('judgment','event','first'),
            fd=lambda reason,judgment,point:(reason,judgment,point)==('event','other' if name=='wrong_supported_judgment' else 'judgment','first'),
            ad=lambda guide,person,judgment,point:name in ('guided_by_other','self_guidance') and
                (guide,person,judgment,point)==('p' if name=='self_guidance' else 'q','p','judgment','first'))
        actual=evaluate(doc,model);assert actual==[name in ('baseline','self_guidance')],(name,actual);rows[name]=actual[0]
    return dict(cases=rows,actual_h5c_and_rcr_executed=True,habitual_disposition_not_claimed=True)


def structure():
    old=parse(text(PARENT));doc=parse(text(FULL));assert doc['statements']==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)
    core=extract_document(doc,roots=['hzhd','hzhe','hzhf'],statement_indices=[]).document;assert core==parse(text(CORE))
    return dict(previous_15_statements_unchanged=True,new_assertions=0,new_primitives=0,new_definitions=len(added),actual_dependencies_extracted=True)


def alignment():
    source=json.loads(text('artifacts/written-units-v1/kant-1784.json'))
    unit=next(x for x in source['units'] if x['id']=='kant-1784:u0011')
    assert hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()==unit['text_sha256']
    segments=[]
    for phrase in ('werden sich immer einige Selbstdenkende','unter den eingesetzten Vormündern'):
        start=unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=start+len(phrase),source=phrase,
            definitions=['hzhb','hzhc','hzhe','hzhf'],status='partial_appointed_independent_judgment_and_future_scope',full_semantic_equivalence=False,
            remaining=['habitual independent thought','guardian role concept and appointment institution','future scope and freedom condition',
                'scalar sogar background and causal discourse','public/crowd meanings and whole paragraph']))
    return dict(segments=segments)


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
    paths=set(files)|{PARENT,'data/kant-unrestricted-others-basis-v1.json','artifacts/written-units-v1/kant-1784.json',
        'tests/test_appointed_thinkers.py','docs/appointed-thinkers-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_appointed_thinkers','check_appointed_thinkers','compose_origin_clock','compose_limits',
        'compose_situated_criticism','check_described_appraisals','check_rod_setup','check_coordinate_correspondence'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script'))
    return dict(status='partial_appointed_independent_judgment_not_full_paragraph',document=FULL,basis_audits=audits,
        generic=generic_checks(),source=source_checks(),appointment=appointment_checks(),judgment=judgment_checks(),structure=structure(),alignment=alignment(),
        roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Shared appointed thinkers and changing future witnesses checked',flush=True)


if __name__=='__main__':main()
