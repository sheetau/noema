"""Check procedural institutional acceptance without inferring private belief."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_institutional_appraisal import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,FIELDS,build,basis,review,manuscript
from scripts.compose_self_benefit import BASE,TRUE,FALSE,DESCRIPTION,RECIPE
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_governing_role as governing

REPORT=ROOT/'reports/institutional-appraisal-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v10.json'
DOMAIN=('government','actor','beneficiary','person','other','outsider','anyrule','allrule','lastrule')
SCENES=('political','outside')
PEOPLE=('person','other')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jtruth[] c.r jany[] a.r jall[] a.r jlast[] a.
d jpolicy[bindings j[a]] e[b point[k jtruth[]]].
d jrecipe[actor a beneficiary a policy '''+DESCRIPTION+''' anchor d context d] c[k jtruth[]].
d jdecision[rule a inputs j[c]] c[x[w[e[v rule][k jany[]]][q[v inputs]['''+FALSE+'''][i[value c item c][x[v value][v item]]]]][x[w[e[v rule][k jall[]]][q[v inputs]['''+TRUE+'''][i[value c item c][w[v value][v item]]]]][w[e[v rule][k jlast[]]][q[v inputs]['''+FALSE+'''][i[value c item c][v item]]]]]].
'''
    args=[]
    for name,sort in FIELDS:
        if name in ('policy','recipe','decides'):
            args.append(dict(policy='r[p jpolicy]',recipe='r b[p jrecipe]',decides='p jdecision')[name]);continue
        provider=not sort.startswith('h[')
        text+=primitive('jc'+name,'h[] '+sort if provider else sort)
        args.append('k jc'+name+'[]' if provider else 'p jc'+name)
    return parse(text+'q[k ryw['+' '.join(args)+']].')


def institutional_model(variant='baseline',bits=1,rule='anyrule',calls=None,policy_name='jpnew',recipe_name='iatbenefit'):
    selected=PEOPLE[:1] if variant=='single_person' else PEOPLE
    listed=() if variant=='empty' else PEOPLE[:1] if variant=='omitted' else PEOPLE+('person',) if variant=='duplicate' else tuple(reversed(PEOPLE)) if variant in ('reversed','reordered') else selected
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    def signature(assessor,actor,beneficiary,policy,recipe,context):
        expected=('outsider' if variant=='wrong_assessor' else 'government',
            'outsider' if variant=='wrong_actor' else 'government',
            'outsider' if variant=='wrong_beneficiary' else 'government',
            'outside' if variant=='wrong_context' else 'political')
        return (assessor,actor,beneficiary,context)==expected and code_is(policy,'jpold' if variant=='wrong_policy' else policy_name) and code_is(recipe,'jrecipealias' if variant=='wrong_recipe' else recipe_name,1)
    def classified(*args):
        if variant=='unknown_input':raise ValueError('Unknown procedural input')
        log('classified',*args)
        return signature(*args[:-1]) and args[-1] in PEOPLE and not (variant=='unassessed' and args[-1]=='other')
    def position(*args):
        log('position',*args)
        assert signature(*args[:-1]),'Unmatched procedural input was read'
        return bool(bits&(1<<PEOPLE.index(args[-1])))
    def constitutes(*args):
        if variant=='unknown_constitution':raise ValueError('Unknown institutional constitution')
        log('constitutes',*args)
        return variant!='no_constitution' and signature(*args[:-2]) and args[-2].items==(listed if variant=='reordered' else selected) and args[-1]==('allrule' if variant=='wrong_rule' else rule)
    def decides(selected,inputs):
        if variant=='unknown_rule':raise ValueError('Unknown decision procedure')
        log('decides',selected,inputs.items)
        if selected=='anyrule':return any(inputs.items)
        if selected=='allrule':return all(inputs.items)
        if selected=='lastrule':return bool(inputs.items and inputs.items[-1])
        raise ValueError('Unknown decision procedure identifier')
    return dict(ibeparticipants=lambda *args:SequenceValue(listed,'"individual"'),
        ibescope=lambda *args:signature(*args[:-1]) and args[-1] in selected,
        ibeclassified=classified,ibeposition=position,iberule=lambda *args:rule,
        ibeconstitutes=constitutes,ibedecides=decides,
        ibecollective=lambda who,point:variant not in ('no_collective','individual','individual_unrecognized') and (who,point)==('government','political'))


def values(variant='baseline',bits=1,rule='anyrule',memoize=True):
    m=institutional_model(variant,bits,rule,policy_name='jpolicy',recipe_name='jrecipe')
    # The fixture's policy and recipe descriptions are supplied to every input
    # relation by the actual general definition, not synthesized in Python.
    def scope(person):return person in (PEOPLE[:1] if variant=='single_person' else PEOPLE)
    p=dict(arithmetic(),jtruth=forbidden,jany=lambda:'anyrule',jall=lambda:'allrule',jlast=lambda:'lastrule',
        jcassessor=lambda:'government',jcactor=lambda:'government',jcbeneficiary=lambda:'government',jccontext=lambda:'political',
        jcparticipants=lambda:m['ibeparticipants'](),jcscope=scope,
        jcpersons=lambda who:who in PEOPLE and not (variant=='nonperson' and who=='other'),
        jcclassified=lambda who:variant!='unassessed' or who!='other',
        jcpositions=lambda who:bool(bits&(1<<PEOPLE.index(who))),jcrule=lambda:rule,jcconstitutes=m['ibeconstitutes'])
    doc=fixture();p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(governing.integrated_fixture());names={d['name']:d for d in doc['declarations']}
    for declaration in document(CORE)['declarations']:
        name=declaration['name']
        if name not in names:doc['declarations'].append(deepcopy(declaration));names[name]=declaration
        else:assert names[name]==declaration,name
    doc['statements'][0]['body']['symbol']='ibeschema'
    doc['statements'][2]['body']['symbol']='ibeappraisal'
    return parse(format_graph(doc,'compact'))


def source_model(variant='baseline',bits=1,rule='anyrule',calls=None):
    p,domain,scenes=governing.current.model('no_benefit' if variant=='no_benefit' else 'baseline',calls)
    p.update(governing.qualification_model('late_vacancy' if variant=='late_vacancy' else 'baseline',calls=calls))
    old_human=p['aa'];old_awareness=p['iatawareness']
    individual=variant in ('individual','individual_unrecognized','ambiguous_kind')
    p['aa']=lambda who:old_human(who) or individual and who=='government'
    m=institutional_model(variant,bits,rule,calls)
    p.update(m)
    p['iatawareness']=(lambda *args:variant!='individual_unrecognized' and old_awareness(*args)) if individual else forbidden
    if variant in ('individual','individual_unrecognized'):
        for name in ('ibeparticipants','ibescope','ibeclassified','ibeposition','iberule','ibeconstitutes','ibedecides'):p[name]=forbidden
    if variant=='nonperson':p['aa']=lambda who:old_human(who) and who!='other'
    domain+=tuple(x for x in ('state','otherstate','deputy','peer','othercommunity','anyrule','allrule','lastrule','outsider') if x not in domain)
    return p,domain,scenes


def source_values(variant='baseline',bits=1,rule='anyrule',indices=(2,3),calls=None):
    p,domain,scenes=source_model(variant,bits,rule,calls)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,domain,scenes,budget=120_000_000)


@lru_cache(maxsize=1)
def integration_checks():
    calls=[];baseline=source_values(indices=tuple(range(len(governing.current.LABELS))),calls=calls)
    assert baseline==[True,True,True,False,True,True,True,True,True],baseline
    print('Institutional appraisal in complete conditional: passed',flush=True)
    results={}
    for variant in ('no_constitution','late_vacancy'):
        results[variant]=source_values(variant,indices=(0,))
        assert results[variant]==[False],(variant,results[variant])
        print(variant+': rejected',flush=True)
    reached={row[0] for row in calls};assert {'classified','position','constitutes','decides'}<=reached
    return dict(baseline=dict(zip(governing.current.LABELS,baseline)),contrasts=results,
        reached_primitive_families=sorted(reached),private_awareness_executed=False)


def attribution(old=False):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'political',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','political') and code_is(code,'ibdschema' if old else 'ibeschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN+('node','author','scope'),situations=SCENES,primitives=p)]


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
    paths=governing.current.input_paths()|{PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,
        'scripts/compose_institutional_appraisal.py','scripts/check_institutional_appraisal.py','tests/test_institutional_appraisal.py',
        'docs/institutional-appraisal-v1.md','data/kant-manuscript-obligations-v9.json','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='institutional_acceptance_connected_to_same_self_benefit_appraisal',documents=documents,
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryw','ibeawareness','ibeappraisal','ibeschema'],adds_new_text_coverage=False,semantic_completion=False),
        integration=results,relocation=manuscript()[1],source_definitions_replaced=[],roundtrips=True,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def write_reports():
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return report


if __name__=='__main__':write_reports()
