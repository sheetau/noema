"""Verify governing-role qualification and the actual current conditional."""
from copy import deepcopy
from functools import lru_cache
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_governing_role import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,FIELDS,build,basis,reading,review,parent_schema
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_current_manuscript as current

REPORT=ROOT/'reports/governing-role-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v9.json'
DOMAIN=('monarch','council','other','office','deputy','peer','state','otherstate','community','othercommunity')
SCENES=('end','political','outside')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args=[]
    for name,sort in FIELDS:
        provider=not sort.startswith('h[')
        text+=primitive('jg'+name,'h[] '+sort if provider else sort)
        args.append('k jg'+name+'[]' if provider else 'p jg'+name)
    return parse(text+'q[k ryv['+' '.join(args)+']].')


def relations(variant='baseline',actor='monarch',calls=None):
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    def roles(role,organization,point):
        log('roles',role,organization,point)
        selected=() if variant=='empty_roles' else ('office',) if variant=='single_role' else (
            ('office','deputy','peer') if variant=='incomparable' else ('office','deputy'))
        return role in selected and organization=='state'
    def above(first,second,organization,point):
        if organization!='state':return False
        return (first,second)==('office','deputy') or variant=='cycle' and (first,second)==('deputy','office') or variant=='reflexive' and first==second=='office'
    def occupants(who,office,organization,point):
        if variant=='unknown_occupant':raise ValueError('Unknown governing-office occupant')
        log('occupants',who,office,organization,point)
        expected=('other' if variant=='wrong_actor' else actor,
            'deputy' if variant=='lower_office' else 'office',
            'otherstate' if variant=='other_organization' else 'state')
        return (who,office,organization)==expected and variant!='no_occupant' and not (
            variant=='late_vacancy' and point=='political') and (variant!='wrong_context' or point=='outside')
    def jurisdiction(organization,community,point):
        if variant=='unknown_jurisdiction':raise ValueError('Unknown community jurisdiction')
        log('jurisdiction',organization,community,point)
        return (organization,community)==('state','othercommunity' if variant=='wrong_community' else 'community') and variant!='no_jurisdiction' and not (variant=='late_jurisdiction_loss' and point=='political')
    return dict(roles=roles,above=above,occupants=occupants,jurisdiction=jurisdiction)


def values(variant='baseline',actor='monarch',memoize=True):
    p={'jg'+name:fn for name,fn in relations(variant,actor).items()}
    p.update(jgactor=lambda:actor,jgcommunity=lambda:'community',jgoffice=lambda:'office',
        jgorganization=lambda:'state',jganchor=lambda:'end')
    return evaluate(fixture(),p,DOMAIN,SCENES,memoize=memoize)


def qualification_model(variant='baseline',actor='government',calls=None):
    rel=relations(variant,actor,calls)
    def organization(community,anchor):
        if calls is not None:calls.append(('organization',community,anchor))
        assert (community,anchor)==('community','end'),'Organization scope moved with evaluation time'
        return 'state'
    return dict(ibdorganization=organization,iabroles=rel['roles'],iababove=rel['above'],
        ibdoccupants=rel['occupants'],ibdjurisdiction=rel['jurisdiction'])


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    return parse(format_graph(doc,'compact')+'''
r jgactor[] a.r jgoffice[] a.r jgcommunity[] a.r jganchor[] d.r jglate[] d.
q[k ibdqualified[k jgactor[] k jgoffice[] k jgcommunity[] k jganchor[] k jganchor[]]].
q[k ibdqualified[k jgactor[] k jgoffice[] k jgcommunity[] k jganchor[] k jglate[]]].
''')


def source_values(variant='baseline',calls=None):
    p=qualification_model(variant,actor='monarch',calls=calls)
    p.update(jgactor=lambda:'monarch',jgoffice=lambda:'office',jgcommunity=lambda:'community',
        jganchor=lambda:'end',jglate=lambda:'political')
    doc=source_fixture();p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES)


@lru_cache(maxsize=1)
def integrated_fixture():
    doc=deepcopy(current.fixture());names={d['name']:d for d in doc['declarations']}
    for declaration in document(CORE)['declarations']:
        name=declaration['name']
        if name not in names:doc['declarations'].append(deepcopy(declaration));names[name]=declaration
        else:assert names[name]==declaration,name
    doc['statements'][0]['body']['symbol']='ibdschema'
    return parse(format_graph(doc,'compact'))


def integrated_values(variant='baseline',indices=(0,),calls=None):
    p,domain,scenes=current.model(variant,calls)
    p.update(qualification_model(variant,calls=calls))
    domain+=tuple(x for x in ('state','otherstate','deputy','peer','othercommunity') if x not in domain)
    doc=deepcopy(integrated_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,domain,scenes,budget=110_000_000)


@lru_cache(maxsize=1)
def integration_checks():
    calls=[];baseline=integrated_values(indices=tuple(range(len(current.LABELS))),calls=calls)
    assert baseline==[True,True,True,False,True,True,True,True,True],baseline
    print('Qualified actor in complete conditional: passed',flush=True)
    results={}
    for variant in ('wrong_community','lower_office','other_organization','late_vacancy','wrong_regime','no_clarification'):
        results[variant]=integrated_values(variant)
        assert results[variant]==[False],(variant,results[variant])
        print(variant+': rejected',flush=True)
    occupants=[row[1:] for row in calls if row[0]=='occupants']
    assert occupants and all(row[:3]==('government','office','state') for row in occupants)
    assert {'end','political'}<={row[3] for row in occupants}
    assert all(row[1:]==('community','end') for row in calls if row[0]=='organization')
    return dict(baseline=dict(zip(current.LABELS,baseline)),contrasts=results,
        qualification_points=sorted({row[3] for row in occupants}),
        fixed_organization_anchor='end',reached_primitive_families=sorted({row[0] for row in calls}))


def attribution(old=False):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'end',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','end') and code_is(code,parent_schema() if old else 'ibdschema',2))
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
    for path,value in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
    assert attribution()==[True] and attribution(True)==[False]
    inspected=review_report();assert all(not row['unconnected_candidate_roots'] for row in inspected['obligations'])
    results=integration_checks()
    paths=current.input_paths()|{PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,
        'scripts/compose_governing_role.py','scripts/check_governing_role.py','tests/test_governing_role.py',
        'docs/governing-role-v1.md','data/collective-office-basis-v1.json','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='same_policy_actor_qualified_by_office_and_community',documents=documents,
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryv','ibdqualified','ibdschema'],adds_new_text_coverage=False,semantic_completion=False),
        integration=results,source_definitions_replaced=[],roundtrips=True,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def write_reports():
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return report


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--report',action='store_true');args=cli.parse_args()
    if args.report:write_reports()
    else:print(integration_checks(),flush=True)
