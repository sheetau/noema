"""Check care, comparison, and its actual reference from the revised attribution."""
import argparse
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import hashlib, json
from itertools import product
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue, evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_tender_care import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,CARE,RANKED,DESCRIPTION,build,basis,reading,review,manuscript
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_covered_unfolding as unfolding

REPORT = ROOT/'reports/tender-care-v1.json'
AUDIT = ROOT/'reports/kant-manuscript-obligations-v2.json'
DOMAIN = ('actor','object','other','careone','caretwo','outsider')
SCENES = ('now','elsewhere')
GOAL = 'r jxsuccess[j[a] d] c.d jxintact[bindings j[a]] e[b point[k jxsuccess[v bindings v point]]].d jxalias[bindings j[a]] e[k jxintact[v bindings]].'


@lru_cache(maxsize=4)
def document(path): return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text = (ROOT/LIBRARY).read_text(encoding='utf-8')+GOAL
    args = {}
    for name,sort in RANKED:
        if name == 'goals':
            text += 'd jxgoals[object a] '+DESCRIPTION+'[r[p jxintact]].'
            args[name] = 'p jxgoals'; continue
        provider = not sort.startswith('h[')
        text += primitive('jx'+name,'h[] '+sort if provider else sort)
        args[name] = 'k jx'+name+'[]' if provider else 'p jx'+name
    args['goal'] = 'r[p jxintact]'
    for name,fields in (('ryj',CARE),('ryk',RANKED),('ryl',RANKED)):
        text += 'q[k '+name+'['+' '.join(args[n] for n,t in fields)+']].'
    return parse(text)


def model(*, degrees=(2,1), affection=True, variant='baseline', actor='actor', point='now'):
    targets = ('object','other')
    def goalfor(obj,goal,scene):
        return obj in targets and scene == point and code_is(goal,'jxintact') and variant != 'wrong_goal_object'
    def aim(who,act,goal,bindings,scene):
        if variant == 'unknown_aim': raise ValueError('Unknown purpose')
        if len(bindings.items) != 1 or bindings.items[0] not in targets: return False
        obj = bindings.items[0]
        expected = 'careone' if obj == 'object' else 'caretwo'
        return (who,act,scene) == (actor,expected,point) and code_is(goal,'jxalias' if variant=='goal_alias' else 'jxintact') and not (
            variant == 'wrong_aim_actor' or variant == 'other_binding' and obj=='object' or variant == 'uncared_comparator' and obj=='other')
    def occurs(act,scene):
        return scene == point and act in ('careone','caretwo') and variant != 'no_action'
    def performs(act,who,scene):
        return scene == point and who == actor and act in ('careone','caretwo') and variant != 'other_performer'
    def classified(who,obj,scene):
        if variant == 'unknown_comparator' and obj=='other': raise ValueError('Unknown affection assessment')
        return (who,scene) == (actor,point) and obj in targets and not (variant=='unassessed_comparator' and obj=='other')
    def degree(who,obj,scene):
        if variant == 'unknown_degree': raise ValueError('Unknown affection degree')
        return Fraction(degrees[targets.index(obj)]) if obj in targets else Fraction(0)
    listed = () if variant=='empty' else ('object',) if variant=='omitted' else ('object','object','other') if variant=='duplicate' else targets
    scope = lambda obj: obj in targets and not (variant=='target_excluded' and obj=='object')
    return dict(arithmetic(),jxactor=lambda:actor,jxobject=lambda:'object',jxcontext=lambda:point,
        jxobjects=lambda:SequenceValue(listed,'"individual"'),jxscope=scope,jxgoalfor=goalfor,jxaims=aim,
        jxoccurs=occurs,jxperforms=performs,jxaffection=lambda who,obj,scene:affection and (who,obj,scene)==(actor,'object',point),
        jxclassified=classified,jxdegree=degree,jxsuccess=forbidden)


def values(*,memoize=True,**options):
    doc = fixture(); p = model(**options)
    p = {d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc = deepcopy(document(CORE)); doc['statements'] = []
    extra = parse('p:'+GOAL+'d iawgoals[actor a point d object a] '+DESCRIPTION+'[r[p jxintact]].')
    pos = next(i for i,d in enumerate(doc['declarations']) if d['name']=='iawgoals')
    doc['declarations'][pos:pos+1] = extra['declarations']
    text = format_graph(doc,'compact')+'r jxobject[] a.r jxcontext[] d.'
    text += ''.join('q[t[k '+name+'[k jxobject[]]][k jxcontext[]]].' for name in ('iagdepiction','iawcare','iawdepiction'))
    return parse(text)


def source_values(*,variant='baseline',degrees=(2,1)):
    p = dict(arithmetic(),**unfolding.model(variant='other_affected_object' if variant=='wrong_growth_object' else 'baseline'))
    c = model(actor='nature',point='end',variant=variant,degrees=degrees)
    old_occurs,old_performs = p['dg'],p['df']
    p.update(jxobject=lambda:'object',jxcontext=lambda:'end',jxsuccess=forbidden,
        iawobjects=lambda actor,point:c['jxobjects'](),iawscope=lambda actor,point,obj:c['jxscope'](obj),
        iawgoalfor=c['jxgoalfor'],iawaims=c['jxaims'],iawaffection=c['jxaffection'],
        iawclassified=c['jxclassified'],iawdegree=c['jxdegree'],
        dg=lambda act,point:old_occurs(act,point) or c['jxoccurs'](act,point),
        df=lambda act,actor,point:old_performs(act,actor,point) or c['jxperforms'](act,actor,point))
    doc=source_fixture();p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,unfolding.DOMAIN+('careone','caretwo'),unfolding.SCENES,budget=4_000_000)


def attribution(*,variant='baseline',family=False):
    doc = deepcopy(document(CORE))
    if family:
        doc['statements'] = []
        doc = parse(format_graph(doc,'compact')+'q[k iawiahfamily[r b[p iahinner]]].')
    p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'other' if variant=='author' else 'author',iagscope=lambda:'scope',wh=lambda:'now',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','now') and code_is(code,'iatschema' if variant=='old_quote' else 'iawiatschema',2),
        iahpresents=lambda node,author,target,depiction,point:(node,author,point)==('node','author','now') and code_is(target,'iahinner',1) and code_is(depiction,'iagdepiction' if variant=='old_quote' else 'iawdepiction',1))
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('now',),primitives=p)]


def review_report():
    packet = json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    units = json.loads((ROOT/packet['source_units']).read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id']==packet['unit'])
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
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==review(files)
    for a,b in product(range(3),repeat=2): assert values(degrees=(a,b))==[True,True,a>=b]
    assert source_values()==[True,True,True]
    assert attribution()==attribution(family=True)==[True]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    inspected=review_report();care=next(r for r in inspected['obligations'] if r['id']=='tender_care')
    assert not care['unconnected_candidate_roots']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,'scripts/compose_tender_care.py','scripts/check_tender_care.py',
        'tests/test_tender_care.py','docs/tender-care-v1.md','noema/manuscript_obligations.py','noema/linking.py',
        'scripts/check_covered_unfolding.py','scripts/check_caused_choice.py','noema/constructed.py',
        'noema/constructed_discourse.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py',
        'noema/diagnostic_short_circuit.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='care_depiction_connected_to_attributed_template',documents=documents,
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryj','ryk','ryl','iawcare','iawdepiction','iawiatschema'],adds_new_text_coverage=False,semantic_completion=False),
        relocation=manuscript()[1],roundtrips=True,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report()
    inspected['document']=SOURCE;inspected['input_sha256']=report['source_sha256']
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Care is now reachable from the attributed depiction; semantic completion remains open')


if __name__=='__main__':main()
