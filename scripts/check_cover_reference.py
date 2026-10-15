"""Check nonfactive backreference and identity of the cover inside the depiction."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_cover_reference import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,build,basis,reading,review,manuscript
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_tender_care as care
from scripts import check_covered_unfolding as growth

REPORT=ROOT/'reports/cover-reference-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v5.json'
DOMAIN=growth.DOMAIN+('careone','caretwo','node','prior','author','scope','prior_scope')
SCENES=growth.SCENES+('utterance','low','high')


def call_is(code,name):
    return code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol=name,arguments=[])


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def generic_fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jknode[] a.r jkprior[] a.r jkauthor[] a.r jkscope[] a.r jkpriorscope[] a.r jkcontext[] d.r jkcover[] a.r jkregime[] d.
r jkrecords[a a i d[e] a d] c.r jkbefore[a a d] c.r jkmapping[a a a a a d d] c.r jkcontenttruth[d] c.
d jkcontent[] e[b point[k jkcontenttruth[v point]]].
q[k ryr[k jknode[] k jkprior[] k jkauthor[] k jkscope[] k jkpriorscope[] k jkcontext[] k jkcover[] k jkregime[] r d[k jkcontent[]] p jkrecords p jkbefore p jkmapping]].
''')


def generic_values(record=True,forward=True,reverse=False,mapping=True,*,same_node=False,memoize=True):
    p=dict(jknode=lambda:'node',jkprior=lambda:'node' if same_node else 'prior',jkauthor=lambda:'author',
        jkscope=lambda:'scope',jkpriorscope=lambda:'prior_scope',jkcontext=lambda:'utterance',jkcover=lambda:'cover',jkregime=lambda:'low',
        jkrecords=lambda node,author,code,scope,point:record and (node,author,scope,point)==('prior','author','prior_scope','utterance') and call_is(code,'jkcontent'),
        jkbefore=lambda left,right,point:point=='utterance' and (forward if (left,right)==('prior','node') else reverse if (left,right)==('node','prior') else False),
        jkmapping=lambda node,author,scope,prior,cover,regime,point:mapping and (node,author,scope,prior,cover,regime,point)==('node','author','scope','prior_scope','cover','low','utterance'),
        jkcontenttruth=forbidden)
    return evaluate(generic_fixture(),p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    extra=care.source_fixture()
    selected=[deepcopy(d) for d in extra['declarations'] if d['name'] in ('jxsuccess','jxintact','jxalias','iawgoals')]
    pos=next(i for i,d in enumerate(doc['declarations']) if d['name']=='iawgoals')
    doc['declarations'][pos:pos+1]=selected
    text=format_graph(doc,'compact')+'r jxobject[] a.r jxcontext[] d.'
    text+=''.join('q[t[k '+name+'[k jxobject[]]][k jxcontext[]]].' for name in ('iagdepiction','iawdepiction','iazdepiction'))
    text+='q[k iazreference[]].q[k iazfamily[r b[p iahinner]]].'
    return parse(text)


def reference_model(variant='baseline',calls=None,context='utterance'):
    def cover(node,author,scope,point):
        if variant=='unknown_cover':raise ValueError('Unknown cover reference')
        if calls is not None:calls.append(('selected',node,author,scope,point))
        assert (node,author,scope,point)==('node','author','scope',context)
        return 'othercover' if variant=='split_cover' else 'cover'
    def lower(anchor):
        assert anchor==context,'Depiction time leaked into discourse reference'
        return 'low'
    def records(node,author,code,scope,point):
        return (node,author,scope,point)==('prior','other' if variant=='wrong_author' else 'author',
            'scope' if variant=='wrong_prior_scope' else 'prior_scope','end' if variant=='wrong_context' else context) and call_is(code,'iafleft' if variant=='wrong_content' else 'iafright')
    def before(left,right,point):
        if point!=context:return False
        return variant!='missing_order' if (left,right)==('prior','node') else variant=='reverse_order' if (left,right)==('node','prior') else False
    def mapping(node,author,scope,prior,cover,regime,point):
        if variant=='unknown_mapping':raise ValueError('Unknown metaphorical mapping')
        expected_cover='othercover' if variant in ('split_cover','wrong_mapped_cover') else 'cover'
        return variant!='no_mapping' and (node,author,scope,prior,cover,regime,point)==('node','author',
            'prior_scope' if variant=='wrong_current_scope' else 'scope','prior_scope',expected_cover,
            'high' if variant=='wrong_regime' else 'low',context)
    return dict(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:context,
        iafrightnode=lambda:'prior',iacscope=lambda:'prior_scope',iaclower=lower,iazcover=cover,iaereport=records,ue=before,iazmapping=mapping,
        iahpresents=lambda node,author,target,depiction,point:(node,author,point)==('node','author',context) and code_is(target,'iahinner',1) and code_is(depiction,'iawdepiction' if variant=='old_depiction' else 'iazdepiction',1))


def source_values(variant='baseline',indices=(0,1,2,3,4),calls=None):
    p=dict(arithmetic(),**growth.model(variant='switched_cover' if variant=='switched_cover' else 'baseline'))
    # Additional discourse/comparison situations are outside the depicted
    # history; extend the inherited finite interpretation to them explicitly.
    for name in ('iaghistory','iagsurrounds','iagresistant'):
        previous=p[name]
        p[name]=lambda *args,_old=previous:args[-1] in growth.SCENES and _old(*args)
    previous_order=p['iagbefore']
    p['iagbefore']=lambda obj,anchor,left,right:left in growth.SCENES and right in growth.SCENES and previous_order(obj,anchor,left,right)
    c=care.model(actor='nature',point='end',variant='no_action' if variant=='no_care' else 'baseline')
    old_occurs,old_performs=p['dg'],p['df']
    p.update(reference_model(variant,calls),jxobject=lambda:'object',jxcontext=lambda:'end',jxsuccess=forbidden,
        iawobjects=lambda actor,point:c['jxobjects'](),iawscope=lambda actor,point,obj:c['jxscope'](obj),
        iawgoalfor=c['jxgoalfor'],iawaims=c['jxaims'],iawaffection=c['jxaffection'],iawclassified=c['jxclassified'],iawdegree=c['jxdegree'],
        dg=lambda act,point:old_occurs(act,point) or c['jxoccurs'](act,point),
        df=lambda act,actor,point:old_performs(act,actor,point) or c['jxperforms'](act,actor,point))
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,budget=4_000_000)


def attribution(variant='baseline'):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'utterance',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','utterance') and code_is(code,'iayschema' if variant=='old' else 'iaziayschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=p)]


@lru_cache(maxsize=2)
def integrated_values(variant='baseline'):
    from scripts import check_policy_integration as integration
    doc=deepcopy(integration.fixture());names={d['name']:d for d in doc['declarations']}
    for d in document(CORE)['declarations']:
        if d['name'] not in names:doc['declarations'].append(deepcopy(d));names[d['name']]=d
        else:assert names[d['name']]==d,d['name']
    doc['statements']=doc['statements'][:1]
    doc['statements'][0]['body']['symbol']='iaziayschema'
    doc=parse(format_graph(doc,'compact'))
    p,domain,scenes=integration.model()
    p.update(reference_model(variant,context='end'))
    domain+=tuple(x for x in ('cover','prior','prior_scope') if x not in domain)
    scenes+=tuple(x for x in ('low','high') if x not in scenes)
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,domain,scenes,budget=90_000_000)


def review_report():
    packet=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    units=json.loads((ROOT/packet['source_units']).read_text(encoding='utf-8'))['units'];unit=next(u for u in units if u['id']==packet['unit'])
    assert hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()==packet['document_sha256']
    return audit(document(SOURCE),unit,packet)


def build_report():
    files=build();documents={}
    for path,text in files.items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    for path,expected in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==expected
    for r,f,b,m in product((False,True),repeat=4):assert generic_values(r,f,b,m)==[r and f and not b and m]
    assert source_values()==[True]*5 and source_values('split_cover')==[True,True,False,True,True]
    assert attribution()==[True] and attribution('old')==[False]
    assert integrated_values()==[True] and integrated_values('wrong_regime')==[False]
    inspected=review_report();row=next(r for r in inspected['obligations'] if r['id']=='hard_cover')
    assert not row['unconnected_candidate_roots']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,care.CORE,growth.CORE,'scripts/compose_cover_reference.py','scripts/check_cover_reference.py',
        'tests/test_cover_reference.py','docs/cover-reference-v1.md','noema/linking.py','noema/manuscript_obligations.py',
        'scripts/check_policy_integration.py','reports/policy-integration-v1.json',
        'scripts/check_tender_care.py','scripts/check_covered_unfolding.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='same_depicted_cover_bound_to_prior_lower_regime',documents=documents,relocation=manuscript()[1],
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryr','iazreference','iazselected','iazdepiction','iazfamily'],adds_new_text_coverage=False,semantic_completion=False),
        roundtrips=True,limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same cover and prior regime connected; interpretive scope remains open')


if __name__=='__main__':main()
