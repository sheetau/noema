"""Verify directive-only and reasoned-response profiles without conflating them."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_reasoned_variation import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,FIELDS,build,basis,reading,review
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_thinking_disposition import code_is,forbidden
from scripts.check_scoped_counts import arithmetic

REPORT=ROOT/'reports/reasoned-variation-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v3.json'
DOMAIN=('person','other','topic','other_topic','faculty','leftjudge','rightjudge','reasonone','reasontwo','one','two','command','government','community','norm','office')
SCENES=('left','right','late','early','anchor','start','end')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args=[]
    for name,sort in FIELDS:
        provider=not sort.startswith('h[')
        text+=primitive('jy'+name,'h[] '+sort if provider else sort)
        args.append('k jy'+name+'[]' if provider else 'p jy'+name)
    return parse(text+''.join('q[k '+name+'['+' '.join(args)+']].' for name in ('rym','ryn','ryo')))


def values(*,same_command=True,same_choice=False,same_reasons=False,independent=(True,True),variant='baseline',memoize=True):
    def assessed(actor,topic,point):
        if variant=='unknown':raise ValueError('Unknown comparison assessment')
        return (actor,topic)==('person','topic') and not (variant=='unassessed' and point=='right')
    p=dict(jyactor=lambda:'person',jytopic=lambda:'topic',
        jycases=lambda point:point in ('left','right') and variant!='empty',jyassessed=assessed,
        jydirective=lambda actor,topic,point:'command' if same_command or point=='left' else 'two',
        jychoice=lambda actor,topic,point:'one' if same_choice or point=='left' else 'two',
        jyindependent=lambda actor,topic,point:(actor,topic)==('person','topic') and independent[point=='right'],
        jyreasons=lambda actor,topic,point,reason:(actor,topic)==('person','topic') and reason==('reasonone' if same_reasons or point=='left' else 'reasontwo'))
    return evaluate(fixture(),p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    text=format_graph(doc,'compact')+'''
r jyperson[] a.r jytopic[] a.r jynow[] d.r jyactor[] a.r jycommunity[] a.r jyanchor[] d.
d jypolicy[bindings j[a]] e[b point[e[n p a b][n p a b]]].
d jyalias[bindings j[a]] e[k jypolicy[v bindings]].
q[k iaxdirected[k jyperson[] k jytopic[] k jynow[]]].
q[k iaxresponsive[k jyperson[] k jytopic[] k jynow[]]].
q[k iaxbeyond[k jyperson[] k jynow[]]].
q[k iaxbeneficiaries[k jyactor[] r[p jypolicy] k jycommunity[] k jyanchor[] k jynow[]]].
q[k iaxindependent[k jyperson[] k jytopic[] k jynow[]]].
'''
    return parse(text)


def source_model(variant='baseline'):
    def scene(point):return point in ('left','right')
    def judge(point):return 'leftjudge' if point=='left' else 'rightjudge'
    def cases(actor,topic,anchor,point):return (actor,topic,anchor)==('person','topic','late') and scene(point)
    def chosen(actor,topic,judgment,choice,point):
        return (actor,topic,judgment,choice)==('person','topic',judge(point),'one' if point=='left' else 'two') and scene(point) and variant!='unlinked_choice'
    def fc(judgment,reason,point):
        expected='reasonone' if variant=='same_reasons' or point=='left' else 'reasontwo'
        return scene(point) and judgment==judge(point) and reason==expected
    def signature(actor,policy,community,anchor):
        return (actor,community,anchor)==('government','community','anchor') and code_is(policy,'jyalias' if variant=='other_policy' else 'jypolicy')
    p=dict(jyperson=lambda:'person',jytopic=lambda:'topic',jynow=lambda:'early' if variant=='early' else 'late',
        jyactor=lambda:'other' if variant=='other_government' else 'government',jycommunity=lambda:'community',jyanchor=lambda:'anchor',
        aa=lambda actor:actor=='person' and variant!='nonhuman',
        ab=lambda faculty,actor,point:(faculty,actor)==('faculty','other' if variant=='other_faculty_owner' else 'person') and scene(point),
        ac=lambda actor,faculty,judgment,point:(actor,faculty,judgment)==('person','faculty',judge(point)) and scene(point),
        fa=lambda actor,judgment,point:(actor,judgment)==('other' if variant=='other_judge' else 'person',judge(point)) and scene(point),
        fb=lambda judgment,topic,point:scene(point) and (judgment,topic)==(judge(point),'other_topic' if variant=='other_topic' else 'topic'),
        fc=fc,fd=lambda reason,judgment,point:fc(judgment,reason,point) and variant!='unsupported',
        ad=lambda guide,actor,judgment,point:variant=='guided' and (guide,actor,judgment)==('other','person',judge(point)) and scene(point),
        iaxcases=cases,iaxassessed=lambda actor,topic,anchor,point:cases(actor,topic,anchor,point) and not (variant=='unassessed' and point=='right'),
        iaxdirective=lambda actor,topic,point:'two' if variant=='different_command' and point=='right' else 'command',
        iaxchoice=lambda actor,topic,point:'one' if point=='left' or variant=='same_choice' else 'two',
        iaxjudgment=lambda actor,topic,point:judge(point),iaxchooses=chosen,
        iaxpeople=lambda *args:SequenceValue(('person','person') if variant=='duplicate' else ('person',),'"individual"'),
        iaxscope=lambda actor,policy,community,anchor,person:signature(actor,policy,community,anchor) and person=='person')
    return dict(arithmetic(),**p)


def source_values(*,variant='baseline'):
    doc=source_fixture();p=source_model(variant)
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES)


def wrapper_values(*,variant='baseline',remaining=True):
    """Exercise the new wrapper through the previous schema's typed interface.

    The prior causal/appraisal model is a recording stand-in in this diagnostic;
    it is not evidence of re-evaluating that entire model.
    """
    doc=deepcopy(source_fixture());doc['statements']=[]
    parent=next(d for d in doc['declarations'] if d['name']=='iawiatschema')
    parent['kind']='primitive';parent.pop('body')
    parent['parameters']=[p['sort'] for p in parent['parameters']]
    text=format_graph(doc,'compact')+'''r jynorm[] a.r jyoffice[] a.r jyprobes[d] c.
r jyremaining[i b[h[a] e] a j[a] d d d d] c.
q[k iaxschema[r b[p iahinner] k jynorm[] k jyactor[] k jyoffice[] r[p jyalias] r[p jypolicy] p jyprobes p jyremaining]].'''
    doc=parse(text);p=source_model(variant);seen=[]
    def previous(reading,source,actor,office,first,second,probes,rest):
        seen.append((source,actor,office,first,second))
        return rest(reading,'community',SequenceValue(('other',),'"individual"'),'anchor','start','end','late')
    p.update(iawiatschema=previous,jynorm=lambda:'norm',jyoffice=lambda:'office',jyprobes=lambda point:True,
        jyremaining=lambda reading,community,contributors,anchor,start,end,late:remaining and code_is(reading,'iahinner',1) and
            (community,contributors.items,anchor,start,end,late)==('community',('other',),'anchor','start','end','late'))
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    result=evaluate(doc,p,DOMAIN,SCENES)
    assert seen and seen[0][:3]==('norm','other' if variant=='other_government' else 'government','office')
    assert code_is(seen[0][3],'jyalias') and code_is(seen[0][4],'jypolicy')
    return result


def attribution(variant='baseline'):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'other' if variant=='author' else 'author',iagscope=lambda:'scope',wh=lambda:'now',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','now') and code_is(code,'iawiatschema' if variant=='old' else 'iaxschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('now',),primitives=p)]


def review_report():
    packet=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    units=json.loads((ROOT/packet['source_units']).read_text(encoding='utf-8'))['units']
    unit=next(u for u in units if u['id']==packet['unit'])
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
    for command,choice,reasons in product((False,True),repeat=3):
        assert values(same_command=command,same_choice=choice,same_reasons=reasons)==[True,not command or choice,command and not choice and not reasons]
    assert source_values()==[False,True,True,True,False]
    assert wrapper_values()==attribution()==[True]
    inspected=review_report();row=next(r for r in inspected['obligations'] if r['id']=='more_than_machine')
    assert not row['unconnected_candidate_roots']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,READING,REVIEW,'scripts/compose_reasoned_variation.py','scripts/check_reasoned_variation.py',
        'tests/test_reasoned_variation.py','docs/reasoned-variation-v1.md','noema/manuscript_obligations.py',
        'scripts/check_caused_choice.py','noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='reasoned_variation_connected_to_same_policy_beneficiaries',documents=documents,
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryn','ryo','iaxbeyond','iaxbeneficiaries','iaxschema'],adds_new_text_coverage=False,semantic_completion=False),
        verification_scope='New response profile and typed parent interface; prior full causal/appraisal model is not rerun here.',
        roundtrips=True,limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Reasoned response contrast connected; source equivalence and dignity remain open')


if __name__=='__main__':main()
