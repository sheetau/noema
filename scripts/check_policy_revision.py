"""Verify the three forms of revision and their actual political causal link."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_policy_revision import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,build,basis,review,manuscript,definitions
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_governing_principles as principles
from scripts import check_institutional_appraisal as institutional

REPORT=ROOT/'reports/policy-revision-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v11.json'
LABELS=institutional.governing.current.LABELS+('normative_change','strict_replacement')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(principles.fixture());doc['statements']=[]
    common='k jgsource[] k jgactor[] k jgoffice[] r[p jgfirst] r[p jgsecond] p jgprobes k jgstart[] k jgend[] p jgrequired'
    return parse(format_graph(doc,'compact')+definitions()+''.join('q[k '+name+'['+common+']].' for name in ('rx3','ryx','ryy','ryz'))+
        'q[t[k jgsecond[l[a][]]][k jgend[]]].')


def values(old=1,new=2,*,variant='baseline',memoize=True,calls=None):
    def required(source,actor,office,code,bindings,polarity,point):
        if variant=='unknown_norm':raise ValueError('Unknown normative state')
        if calls is not None:calls.append((source,actor,office,code,bindings.items,polarity,point))
        expected=('outsider' if variant=='other_source' else 'source',
            'outsider' if variant=='other_actor' else 'government','outsider' if variant=='other_office' else 'office')
        if (source,actor,office)!=expected or bindings.items!=(('person',) if variant=='wrong_bindings' else ()) or polarity!=(variant!='negative_polarity'):return False
        if point not in ('start','end'):return False
        mask=old if code_is(code,'jgfirst') else new if code_is(code,'jgsecond') else 0
        return bool(mask&(1<<('start','end').index(point)))
    def treatment(actor,person,point):
        if variant=='unknown_content':raise ValueError('Unknown principle content')
        return variant!='equivalent' and (actor,point)==('government','probe') and person in principles.PEOPLE
    def probes(point):
        if variant=='unknown_probes':raise ValueError('Unknown comparison scope')
        return variant!='empty_probes' and point=='probe'
    p=dict(arithmetic(),jgactor=lambda:'government',jgsource=lambda:'source',jgoffice=lambda:'office',
        jgpeople=lambda:SequenceValue(principles.PEOPLE,'"individual"'),jgscope=lambda who:who in principles.PEOPLE,
        jgcondition=lambda who,point:who in principles.PEOPLE,jgfirsttreatment=lambda *args:False,jgsecondtreatment=treatment,
        jgstart=lambda:'start',jgend=lambda:'start' if variant=='same_context' else 'end',jgprobes=probes,jgrequired=required)
    doc=fixture();p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,principles.DOMAIN,principles.SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(institutional.source_fixture());names={d['name']:d for d in doc['declarations']}
    for declaration in document(CORE)['declarations']:
        name=declaration['name']
        if name not in names:doc['declarations'].append(deepcopy(declaration));names[name]=declaration
        else:assert names[name]==declaration,name
    doc['statements'][0]['body']['symbol']='ibfschema';doc['statements'][6]['body']['symbol']='ibfcausal'
    statements=doc['statements'];doc['statements']=[]
    common='k jpsource[] k jpactor[] k jpoffice[] r[p jpold] r[p jpnew] p jpprobes k jrbefore[] k jrafter[]'
    doc=parse(format_graph(doc,'compact')+'r jrbefore[] d.r jrafter[] d.'+
        ''.join('q[k '+name+'['+common+']].' for name in ('ibfchange','iarreplacement')))
    doc['statements']=statements+doc['statements'];return doc


def source_model(mode='replacement',calls=None):
    p,domain,scenes=institutional.source_model(calls=calls)
    previous=p['h7k']
    def required(source,actor,office,code,bindings,polarity,point):
        if code_is(code,'jpold') or code_is(code,'jpnew'):
            if calls is not None:calls.append(('revision_norm',source,actor,office,code,bindings.items,polarity,point))
            if (source,actor,office)!=('norm','government','office') or bindings.items or not polarity:return False
            if point not in ('normbase','normchanged','normkept'):return False
            if code_is(code,'jpold'):
                return mode in ('addition','unchanged','independent_change') or point!='normchanged'
            return mode in ('retirement','unchanged') or point=='normchanged' or mode=='independent_change' and point=='normkept'
        return previous(source,actor,office,code,bindings,polarity,point)
    p.update(h7k=required,jrbefore=lambda:'normbase',jrafter=lambda:'normchanged')
    return p,domain,scenes


def source_values(mode='replacement',indices=(9,10),calls=None):
    p,domain,scenes=source_model(mode,calls);doc=deepcopy(source_fixture())
    doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,domain,scenes,budget=130_000_000)


@lru_cache(maxsize=1)
def integration_checks():
    calls=[];baseline=source_values(indices=tuple(range(len(LABELS))),calls=calls)
    assert baseline==[True,True,True,False,True,True,True,True,True,True,True],baseline
    print('Replacement retained in complete conditional: passed',flush=True)
    cases={}
    for mode in ('addition','retirement'):
        cases[mode]=source_values(mode,indices=(0,6,9,10))
        assert cases[mode]==[True,True,True,False],(mode,cases[mode])
        print(mode+': accepted without strict replacement',flush=True)
    for mode in ('unchanged','independent_change'):
        cases[mode]=source_values(mode,indices=(0,9))
        assert cases[mode]==[False,mode=='independent_change'],(mode,cases[mode])
        print(mode+': rejected as a causal consequence',flush=True)
    norms=[row[1:] for row in calls if row[0]=='revision_norm']
    assert norms and all(row[:3]==('norm','government','office') and row[4:6]==((),True) for row in norms)
    return dict(baseline=dict(zip(LABELS,baseline)),cases=cases,
        case_columns=dict(addition=['schema','political_cause','normative_change','strict_replacement'],
            retirement=['schema','political_cause','normative_change','strict_replacement'],
            unchanged=['schema','normative_change'],independent_change=['schema','normative_change']),
        reached_primitive_families=sorted({row[0] for row in calls}))


def attribution(old=False):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'political',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','political') and code_is(code,'ibeschema' if old else 'ibfschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=institutional.DOMAIN+('node','author','scope'),situations=institutional.SCENES,primitives=p)]


def review_report():
    packet=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    unit=next(u for u in json.loads((ROOT/packet['source_units']).read_text(encoding='utf-8'))['units'] if u['id']==packet['unit'])
    assert hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()==packet['document_sha256']
    return audit(document(SOURCE),unit,packet)


def build_report():
    files=build();documents={}
    for path,text in files.items():
        assert (ROOT/path).read_text(encoding='utf-8')==text;doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    for path,value in ((BASIS,basis()),(REVIEW,review(files))):assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
    assert attribution()==[True] and attribution(True)==[False]
    inspected=review_report();assert all(not row['unconnected_candidate_roots'] for row in inspected['obligations'])
    results=integration_checks()
    paths=institutional.governing.current.input_paths()|{PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,
        'scripts/compose_policy_revision.py','scripts/check_policy_revision.py','tests/test_policy_revision.py','docs/policy-revision-v1.md',
        'data/kant-manuscript-obligations-v10.json','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='addition_and_retirement_allowed_in_normative_political_effect',documents=documents,
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryx','ryy','ryz','ibfchange','ibfcausal','ibfschema'],adds_new_text_coverage=False,semantic_completion=False),
        integration=results,relocation=manuscript()[1],source_definitions_replaced=[],roundtrips=True,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def write_reports():
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return report


if __name__=='__main__':write_reports()
