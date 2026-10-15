"""Check untested dispositions, candidate responses, and the current manuscript."""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_dispositional_resistance import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,FIELDS,build,basis,review,manuscript
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_load_resistance as response
from scripts import check_cover_reference as cover
from scripts import check_tender_care as care
from scripts import check_covered_unfolding as growth
from scripts import check_property_apposition as apposition

REPORT=ROOT/'reports/dispositional-resistance-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v8.json'
DOMAIN=response.DOMAIN+('germ','detail')
ANCHORS=('now','start','middle','end')
CANDIDATES=tuple(anchor+suffix for anchor in ANCHORS for suffix in ('responseone','responsetwo'))
SCENES=response.SCENES+CANDIDATES


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args=[]
    for name,sort in FIELDS:
        provider=not sort.startswith('h[')
        text+=primitive('jl'+name,'h[] '+sort if provider else sort)
        args.append('k jl'+name+'[]' if provider else 'p jl'+name)
    return parse(text+'q[k rys['+' '.join(args[:-1])+']].q[k ryu['+' '.join(args)+']].')


def model(*,variant='baseline',actual_loaded=False,point='now',calls=None,**options):
    p=response.model(variant=variant,point=point,**options)
    anchors=('start','middle','end') if point=='growth' else (point,)
    def prospects(obj,test,protocol,loadunit,deformationunit,anchor,candidate):
        if variant=='unknown_prospects':raise ValueError('Unknown candidate response relation')
        expected=('other' if variant=='wrong_object' else 'cover',
            'other' if variant=='wrong_test' else test,
            'other' if variant=='wrong_protocol' else 'protocol',
            'other' if variant=='wrong_loadunit' else 'forceunit',
            'other' if variant=='wrong_deformationunit' else 'lengthunit')
        if (obj,test,protocol,loadunit,deformationunit)!=expected or test not in response.TESTS:return False
        if anchor not in (('outside',) if variant=='wrong_anchor' else anchors):return False
        if variant=='no_candidates' or variant=='missing_test_candidates' and test=='probetwo':return False
        return candidate in (anchor+'responseone',anchor+'responsetwo')
    original={n:p['jl'+n] for n in ('assessed','load','deformation')}
    def assess(*args):
        obj,test,protocol,loadunit,deformationunit,scene=args
        if calls is not None:calls.append(args)
        if variant=='unknown_assessment':raise ValueError('Unknown mechanical assessment')
        if scene in anchors:return actual_loaded and original['assessed'](*args)
        return (obj,protocol,loadunit,deformationunit)==('cover','protocol','forceunit','lengthunit') and test in response.TESTS and scene in CANDIDATES and not (variant=='unassessed' and test=='probetwo')
    def load(*args):
        return original['load'](*args) if args[-1] in CANDIDATES or actual_loaded else F(0)
    def deformation(*args):
        if variant=='bad_candidate' and args[-1].endswith('responsetwo') and args[1]=='probetwo':return F(1)
        if variant=='middle_failure' and args[-1]=='middleresponsetwo' and args[1]=='probetwo':return F(1)
        return original['deformation'](*args)
    p.update(jlprospects=prospects,jlassessed=assess,jlload=load,jldeformation=deformation)
    return p


def values(*,memoize=True,indices=(0,1),**options):
    p=model(**options);doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(response.source_fixture());old=doc['statements'][1:2];doc['statements']=[]
    names={d['name']:d for d in doc['declarations']}
    for d in document(CORE)['declarations']:
        if d['name'] not in names:doc['declarations'].append(deepcopy(d));names[d['name']]=d
        elif d['name']!='iawgoals':assert names[d['name']]==d,d['name']
    doc=parse(format_graph(doc,'compact')+'''
q[t[k ibcdepiction[k jxobject[]]][k jxcontext[]]].
q[k ibcfamily[r b[p iahinner]]].
''')
    doc['statements']=old+doc['statements'];return doc


def source_values(variant='baseline',indices=(0,1,2),calls=None,actual_loaded=False):
    p=dict(arithmetic(),**growth.model(hard=0 if variant=='legacy_false' else 7,
        variant='switched_cover' if variant=='switched_cover' else 'baseline'))
    for name in ('iaghistory','iagsurrounds','iagresistant'):
        old=p[name];p[name]=lambda *args,_old=old:args[-1] in growth.SCENES and _old(*args)
    order=p['iagbefore'];p['iagbefore']=lambda obj,anchor,left,right:left in growth.SCENES and right in growth.SCENES and order(obj,anchor,left,right)
    c=care.model(actor='nature',point='end');occurs,performs=p['dg'],p['df']
    p.update(cover.reference_model('split_cover' if variant=='split_cover' else 'baseline'),
        jxobject=lambda:'object',jxcontext=lambda:'end',jxsuccess=forbidden,
        iawobjects=lambda actor,point:c['jxobjects'](),iawscope=lambda actor,point,obj:c['jxscope'](obj),
        iawgoalfor=c['jxgoalfor'],iawaims=c['jxaims'],iawaffection=c['jxaffection'],iawclassified=c['jxclassified'],iawdegree=c['jxdegree'],
        dg=lambda act,point:occurs(act,point) or c['jxoccurs'](act,point),
        df=lambda act,actor,point:performs(act,actor,point) or c['jxperforms'](act,actor,point),
        iahpresents=lambda node,author,target,depiction,point:(node,author,point)==('node','author','utterance') and code_is(target,'iahinner',1) and code_is(depiction,'ibadepiction' if variant=='old_depiction' else 'ibcdepiction',1))
    m=model(variant=variant,actual_loaded=actual_loaded,point='growth',calls=calls)
    def fixed(name):
        def provider(obj,anchor):
            assert anchor=='utterance','Benchmark changed with depicted time'
            return m['jl'+name]()
        return provider
    for name in ('tests','protocol','loadunit','deformationunit','minimum','maximum'):p['iba'+name]=fixed(name)
    p.update(ibascope=lambda obj,anchor,test:anchor=='utterance' and m['jlscope'](test),
        ibaassessed=m['jlassessed'],ibaload=m['jlload'],ibadeformation=m['jldeformation'],ibcprospects=m['jlprospects'])
    nominal=apposition.source_model(variant='no_clarification' if variant=='no_apposition' else 'baseline')
    p.update({n:nominal[n] for n in ('ibbgermnode','ibbdetailnode')})
    p['ibbdenotes']=lambda node,author,code,scope,point:point=='utterance' and nominal['ibbdenotes'](node,author,code,scope,'end')
    p['ibbclarifies']=lambda first,second,author,scope,point:point=='utterance' and nominal['ibbclarifies'](first,second,author,scope,'end')
    before=p['ue'];p['ue']=lambda left,right,point:(left,right,point)==('germ','detail','utterance') or before(left,right,point)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,budget=8_000_000)


def attribution(old=False):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    path='data/kant-manuscript-obligations-v7.json' if old else REVIEW
    name=json.loads((ROOT/path).read_text(encoding='utf-8'))['templates'][0]['symbol']
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'utterance',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','utterance') and code_is(code,name,2))
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
    for path,value in ((BASIS,basis()),(REVIEW,review(files))):assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
    contrasts={name:values(variant=name,actual_loaded=True) for name in ('baseline','no_candidates','missing_test_candidates','bad_candidate')}
    assert contrasts==dict(baseline=[True,True],no_candidates=[True,False],missing_test_candidates=[True,False],bad_candidate=[True,False])
    assert values()==[False,True] and source_values()==[False,True,True]
    assert source_values('middle_failure',actual_loaded=True)==[False,False,True]
    assert attribution()==[True] and attribution(True)==[False]
    inspected=review_report();assert all(not r['unconnected_candidate_roots'] for r in inspected['obligations'] if r['id'] in ('hard_cover','germ','thinking_disposition'))
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,response.CORE,cover.CORE,care.CORE,growth.CORE,apposition.CORE,
        'data/kant-manuscript-obligations-v7.json','data/load-resistance-basis-v1.json',
        'scripts/compose_dispositional_resistance.py','scripts/check_dispositional_resistance.py','tests/test_dispositional_resistance.py','docs/dispositional-resistance-v1.md',
        'scripts/compose_load_resistance.py','scripts/check_load_resistance.py','scripts/check_property_apposition.py',
        'scripts/check_cover_reference.py','scripts/check_tender_care.py','scripts/check_covered_unfolding.py','scripts/check_caused_choice.py',
        'noema/linking.py','noema/manuscript_obligations.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='disposition_separated_from_actual_loading',documents=documents,relocation=manuscript()[1],
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryu','ibcresistant','ibcdepiction','ibcfamily'],adds_new_text_coverage=False,semantic_completion=False),
        contrast_results=contrasts,untested_response_and_disposition=[False,True],
        verification_scope='Actual growth/care depiction and amended family/apposition evaluated. Earlier full causal/appraisal schema not rerun. Candidate selection is interpreted input.',
        roundtrips=True,limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Untested disposition connected; physical interpretation and source semantics remain incomplete')


if __name__=='__main__':main()
