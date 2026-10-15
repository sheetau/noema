"""Verify shared property reference without identifying a bearer with a germ."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_property_apposition import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,FIELDS,build,basis,reading,review,manuscript
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_thinking_disposition as thinking
from scripts import check_cover_reference as cover

REPORT=ROOT/'reports/property-apposition-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v7.json'
DOMAIN=thinking.DOMAIN+('germ','detail','prior','prior_scope','cover')
SCENES=thinking.SCENES+('low','high')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jmtruth[a d] c.d jmproperty[person a] e[b point[k jmtruth[v person v point]]].
d jmalias[person a] e[k jmproperty[v person]].
''';args=[]
    for name,sort in FIELDS:
        if name=='referent':args.append('r b[p jmproperty]');continue
        provider=not sort.startswith('h[')
        text+=primitive('jm'+name,'h[] '+sort if provider else sort)
        args.append('k jm'+name+'[]' if provider else 'p jm'+name)
    return parse(text+'q[k ryt['+' '.join(args)+']].')


def values(mentions=3,*,forward=True,reverse=False,clarifies=True,variant='baseline',memoize=True):
    def denotes(node,author,code,scope,point):
        if variant=='unknown':raise ValueError('Unknown nominal reference')
        return node in ('germ','detail') and bool(mentions&(1 if node=='germ' else 2)) and (author,scope,point)==('author','scope','end') and code_is(code,'jmalias' if variant=='alias' and node=='detail' else 'jmproperty',1)
    p=dict(jmfirst=lambda:'germ',jmsecond=lambda:'germ' if variant=='same_node' else 'detail',jmauthor=lambda:'author',
        jmscope=lambda:'scope',jmcontext=lambda:'end',jmtruth=forbidden,jmdenotes=denotes,
        jmbefore=lambda left,right,point:point=='end' and (forward if (left,right)==('germ','detail') else reverse if (left,right)==('detail','germ') else False),
        jmclarifies=lambda first,second,author,scope,point:clarifies and (first,second,author,scope,point)==('germ','detail','author','scope','end'))
    return evaluate(fixture(),p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    text=format_graph(doc,'compact')+'r jtperson[] a.r jtanchor[] d.d jmbundlealias[person a] e[k ibbinner[v person]].'
    for name in ('ibbinner','ibbvocation','iahinner','iahvocation'):
        text+='q[t[k '+name+'[k jtperson[]]][k jtanchor[]]].'
    for name in ('ibbapposition','ibbfamily'):
        for reading in ('iahinner','iahvocation'):
            text+='q[k '+name+'[r b[p '+reading+']]].'
    text+='q[k ibbapposition[r b[p iahthinking]]].'
    return parse(text)


def source_model(*,variant='baseline',hits=3,urge=True,assigned=True,calls=None):
    p=thinking.model(hits=hits,urge=urge,assigned=assigned,variant=variant)
    p.update(cover.reference_model(context='end'))
    old_order=p['ue']
    def before(left,right,point):
        if (left,right)==('germ','detail'):return variant!='missing_order' and point=='end'
        if (left,right)==('detail','germ'):return variant=='reverse_order' and point=='end'
        return old_order(left,right,point)
    def denotes(node,author,code,scope,point):
        if variant=='unknown_reference':raise ValueError('Unknown nominal reference')
        if calls is not None:calls.append((node,author,code,scope,point))
        if (author,scope,point)!=('other' if variant=='wrong_author' else 'author',
            'prior_scope' if variant=='wrong_scope' else 'scope','outside' if variant=='wrong_context' else 'end'):return False
        if node not in ('germ','detail') or variant=='missing_mention' and node=='detail':return False
        if variant=='crossed':return code_is(code,'ibbinner' if node=='germ' else 'ibbvocation',1)
        if variant=='alias' and node=='detail':return code_is(code,'jmbundlealias',1)
        return any(code_is(code,name,1) for name in ('ibbinner','ibbvocation'))
    if variant=='other_assignment_person':
        p['iahassigned']=lambda source,person,code,point:(source,person,point)==('norm','other','end') and code_is(code,'iahthinking')
    if variant=='other_assignment_time':
        p['iahassigned']=lambda source,person,code,point:(source,person,point)==('norm','person','outside') and code_is(code,'iahthinking')
    p.update(ibbgermnode=lambda:'germ',ibbdetailnode=lambda:'detail',ibbdenotes=denotes,ue=before,
        ibbclarifies=lambda first,second,author,scope,point:variant!='no_clarification' and (first,second,author,scope,point)==('germ','detail','author','scope','end'),
        iahpresents=lambda node,author,target,depiction,point:(node,author,point)==('node','author','end') and any(code_is(target,n,1) for n in ('iahinner','iahvocation')) and code_is(depiction,'ibadepiction',1))
    return p


def source_values(*,indices=tuple(range(9)),**options):
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p=source_model(**options);p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,budget=6_000_000)


def attribution(old=False):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    packet=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    prior=json.loads((ROOT/'data/kant-manuscript-obligations-v6.json').read_text(encoding='utf-8'))
    name=(prior if old else packet)['templates'][0]['symbol']
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'end',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','end') and code_is(code,name,2))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=p)]


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
    for path,value in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
    for mentions,forward,reverse,clarifies in product(range(4),(False,True),(False,True),(False,True)):
        assert values(mentions,forward=forward,reverse=reverse,clarifies=clarifies)==[mentions==3 and forward and not reverse and clarifies]
    assert source_values()==[True]*8+[False]
    assert source_values(variant='missing_latent',indices=(0,1,2,3))==[True,True,False,False]
    assert attribution()==[True] and attribution(True)==[False]
    inspected=review_report();row=next(r for r in inspected['obligations'] if r['id']=='thinking_disposition')
    assert not row['unconnected_candidate_roots']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,thinking.CORE,'data/kant-manuscript-obligations-v6.json',
        'scripts/compose_property_apposition.py','scripts/check_property_apposition.py','tests/test_property_apposition.py','docs/property-apposition-v1.md',
        'scripts/check_thinking_disposition.py','scripts/check_cover_reference.py','scripts/check_caused_choice.py',
        'noema/linking.py','noema/manuscript_obligations.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='same_property_bundle_referenced_by_explanatory_apposition',documents=documents,relocation=manuscript()[1],
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryt','ibbbundle','ibbinner','ibbvocation','ibbapposition','ibbfamily'],adds_new_text_coverage=False,semantic_completion=False),
        verification_scope='Actual component/development definitions and amended family; earlier full causal/appraisal schema not rerun.',
        roundtrips=True,limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Appositive property reference connected; source semantics remain incomplete')


if __name__=='__main__':main()
