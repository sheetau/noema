"""Verify protocol-relative resistance and the same cover throughout growth."""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_load_resistance import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,FIELDS,build,basis,reading,review,manuscript
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_cover_reference as cover
from scripts import check_tender_care as care
from scripts import check_covered_unfolding as growth

REPORT=ROOT/'reports/load-resistance-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v6.json'
TESTS=('probeone','probetwo')
DOMAIN=cover.DOMAIN+TESTS+('protocol','forceunit','lengthunit')
SCENES=cover.SCENES+('now',)


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args=[]
    for name,sort in FIELDS:
        provider=not sort.startswith('h[')
        text+=primitive('jl'+name,'h[] '+sort if provider else sort)
        args.append('k jl'+name+'[]' if provider else 'p jl'+name)
    return parse(text+'q[k rys['+' '.join(args)+']].')


def model(*,variant='baseline',loads=(10,20),deformations=(F(1,20),F(1,10)),minimum=10,maximum=F(1,10),
          force_scale=1,deformation_scale=1,point='now',calls=None):
    def signature(obj,test,protocol,loadunit,deformationunit,scene):
        expected=('other' if variant=='wrong_object' else 'cover',test,
            'other' if variant=='wrong_protocol' else 'protocol',
            'other' if variant=='wrong_loadunit' else 'forceunit',
            'other' if variant=='wrong_deformationunit' else 'lengthunit')
        return (obj,test,protocol,loadunit,deformationunit)==expected and test in TESTS and scene in (
            ('outside',) if variant=='wrong_context' else ('start','middle','end') if point=='growth' else (point,))
    def assessed(*args):
        if variant=='unknown_assessment':raise ValueError('Unknown mechanical assessment')
        if calls is not None:calls.append(args)
        return signature(*args) and force_scale>0 and deformation_scale>0 and not (variant=='unassessed' and args[1]=='probetwo')
    def load(*args):
        if variant=='unknown_load':raise ValueError('Unknown load')
        return F(loads[TESTS.index(args[1])])*force_scale
    def deformation(*args):
        if variant=='unknown_deformation':raise ValueError('Unknown deformation')
        value=F(1) if variant=='middle_failure' and args[-1]=='middle' and args[1]=='probetwo' else F(deformations[TESTS.index(args[1])])
        return value*deformation_scale
    listed=() if variant=='empty' else TESTS[:1] if variant=='omitted' else TESTS+('probeone',) if variant=='duplicate' else TESTS
    return dict(arithmetic(),jlobject=lambda:'cover',jlcontext=lambda:point,
        jltests=lambda:SequenceValue(listed,'"individual"'),jlscope=lambda test:test in TESTS,
        jlprotocol=lambda:'protocol',jlloadunit=lambda:'forceunit',jldeformationunit=lambda:'lengthunit',
        jlminimum=lambda:F(minimum)*force_scale,jlmaximum=lambda:F(maximum)*deformation_scale,
        jlassessed=assessed,jlload=load,jldeformation=deformation)


def values(*,memoize=True,**options):
    p=model(**options);doc=fixture()
    p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    # The prior diagnostic supplies the care-goal description. All actual
    # resistance definitions and their quoted ancestors remain unchanged.
    doc=deepcopy(cover.source_fixture());doc['statements']=doc['statements'][2:3]
    old=doc['statements'];doc['statements']=[];names={d['name']:d for d in doc['declarations']}
    for d in document(CORE)['declarations']:
        if d['name'] not in names:doc['declarations'].append(deepcopy(d));names[d['name']]=d
        elif d['name']!='iawgoals':assert names[d['name']]==d,d['name']
    doc=parse(format_graph(doc,'compact')+'''
q[t[k ibadepiction[k jxobject[]]][k jxcontext[]]].
q[k ibafamily[r b[p iahinner]]].
''')
    doc['statements']=old+doc['statements'];return doc


def source_values(variant='baseline',indices=(0,1,2),calls=None):
    p=dict(arithmetic(),**growth.model(hard=0 if variant=='legacy_false' else 7))
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
        iahpresents=lambda node,author,target,depiction,point:(node,author,point)==('node','author','utterance') and code_is(target,'iahinner',1) and code_is(depiction,'iazdepiction' if variant=='old_depiction' else 'ibadepiction',1))
    m=model(variant=variant,point='growth',calls=calls)
    def fixed(name):
        def provider(obj,anchor):
            assert anchor=='utterance','Benchmark changed with depicted time'
            return m['jl'+name]()
        return provider
    for name in ('tests','protocol','loadunit','deformationunit','minimum','maximum'):p['iba'+name]=fixed(name)
    p.update(ibascope=lambda obj,anchor,test:anchor=='utterance' and m['jlscope'](test),
        ibaassessed=m['jlassessed'],ibaload=m['jlload'],ibadeformation=m['jldeformation'])
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,budget=5_000_000)


def attribution(old=False):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    _,mapping=manuscript()
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'utterance',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','utterance') and code_is(code,'iaziayschema' if old else mapping['iaziayschema'],2))
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
    assert values()==values(force_scale=1000,deformation_scale=F(1,100))==[True]
    assert source_values()==[True]*3 and source_values('middle_failure')==[True,False,True]
    assert source_values('legacy_false')==[False,True,True]
    assert attribution()==[True] and attribution(True)==[False]
    inspected=review_report();row=next(r for r in inspected['obligations'] if r['id']=='hard_cover')
    assert not row['unconnected_candidate_roots']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,cover.CORE,care.CORE,growth.CORE,
        'scripts/compose_load_resistance.py','scripts/check_load_resistance.py','tests/test_load_resistance.py','docs/load-resistance-v1.md',
        'scripts/check_cover_reference.py','scripts/check_tender_care.py','scripts/check_covered_unfolding.py','scripts/check_caused_choice.py',
        'noema/linking.py','noema/manuscript_obligations.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='load_resistance_explained_inside_same_cover_depiction',documents=documents,relocation=manuscript()[1],
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['rys','ibaresistant','ibadepiction','ibafamily'],adds_new_text_coverage=False,semantic_completion=False),
        verification_scope='Resistance and complete growth/care depiction evaluated; family and attribution checked without asserting depiction. Earlier causal/appraisal model not rerun.',
        roundtrips=True,limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Protocol-relative resistance connected; material and source semantics remain incomplete')


if __name__=='__main__':main()
