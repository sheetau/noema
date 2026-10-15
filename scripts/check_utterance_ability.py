"""Check ordered utterances without evaluating quoted claims or commands."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_utterance_ability import ROOT,LIBRARY,EXAMPLE,BASIS,ABILITY,PARENT,build,basis
from scripts.compose_shared_quotation import FIELDS,PERMISSION,OBEY

REPORT=ROOT/'reports/utterance-ability-v1.json'
DOMAIN=('speaker','other','listener','a','b','c','d','plan')
SCENES=('anchor','left','right')

@lru_cache(maxsize=1)
def setup():
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'));expected={};codes={}
    for actor,constant in [('speaker','juperson'),('other','juother')]:
        refs={n:'p hzs'+n for n,_ in FIELDS};refs.update(source='k '+constant+'[]',anchor='k juanchor[]',people='p jupeople',required='p h7a',allowed='p h7b')
        literals=['r b[c[i[content e][j '+force+'[v content]]][c[p '+symbol+']['+' '.join(refs[n] for n,_ in fields)+']]]'
                  for force,symbol,fields in [('s','rub',PERMISSION),('m','rua',OBEY)]]
        probe=deepcopy(doc);probe['statements']=[]
        probe=parse(format_graph(probe,'compact')+''.join('q[e['+literal+']['+literal+']].' for literal in literals))
        nodes=[d['body']['arguments'][0] for d in probe['statements']]
        expected[actor]=[node['body'] for node in nodes];codes[actor]=nodes
    return doc,expected,codes

def values(bits=(True,True,True,True,True,True,True),*,eligible=False,variant='baseline',indices=None,memoize=True,program=None):
    available,outleft,outright,selleft,selright,successleft,successright=bits
    original,expected,codes=setup();doc=deepcopy(original)
    if program is not None:
        assert len(program)<=4 and all(index in (0,1) for index in program)
        next(d for d in doc['declarations'] if d['name']=='jumessages')['body']=dict(kind='sequence',element=dict(kind='description',result='message',rank=1),items=[deepcopy(codes['speaker'][i]) for i in program])
        doc=parse(format_graph(doc,'compact'))
    if variant=='repeated_message':
        next(d for d in doc['declarations'] if d['name']=='jumessages')['body']=dict(kind='sequence',element=dict(kind='description',result='message',rank=1),items=[deepcopy(codes['speaker'][0]),deepcopy(codes['speaker'][0])])
        doc=parse(format_graph(doc,'compact'))
    if variant=='current_point':doc['statements'][0]['body']['situation']={'kind':'call','symbol':'juanchor','arguments':[]}
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('Quoted normative contents were executed')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def events(actor,point):
        parts=('a','b') if actor=='speaker' else ('c','d') if actor=='other' else ()
        if program is not None:parts=('a','b','c','d')[:len(program)] if actor=='speaker' else ()
        if variant=='empty_events':parts=()
        if variant=='short_events':parts=parts[:1]
        if variant=='extra_events' and parts:parts=parts+('plan',)
        if variant=='reversed_events':parts=tuple(reversed(parts))
        if variant=='duplicate_event' and parts:parts=(parts[0],parts[0])
        return SequenceValue(parts,json.dumps('individual'))
    def actor_of(event):
        if program is not None:return 'speaker' if event in ('a','b','c','d')[:len(program)] else None
        return 'speaker' if event in ('a','b') else 'other' if event in ('c','d') else None
    def occurs(event,point):
        if variant=='unknown_occurrence':raise ValueError('Unknown occurrence')
        return actor_of(event) is not None and ((point=='left' and successleft) or (point=='right' and successright))
    def agent(actor,event,point):return actor==actor_of(event) and not (variant=='other_actor' and actor=='speaker')
    def presents(event,recipient,point):return recipient=='listener' and variant!='other_listener'
    def conveys(event,code,point):
        actor=actor_of(event)
        if not actor:return False
        index=0 if event in ('a','c') or variant in ('repeated_message','duplicate_event') else 1
        if program is not None:index=program[('a','b','c','d').index(event)]
        if variant=='swapped_messages':index=1-index
        if variant=='other_speaker_content':actor='other' if actor=='speaker' else 'speaker'
        return code.rank==1 and json.loads(code.syntax)==expected[actor][index]
    def before(earlier,later,point):
        if program is not None:
            order=('a','b','c','d')[:len(program)]
            return earlier in order and later in order and order.index(earlier)<order.index(later)
        if variant=='no_order':return False
        if variant=='self_order' and earlier==later:return True
        if variant=='two_way_order':return (earlier,later) in (('a','b'),('b','a'),('c','d'),('d','c'))
        return (earlier,later) in (('a','b'),('c','d'))
    def available_fn(actor,plan,start):
        if variant=='unknown_availability':raise ValueError('Unknown availability')
        return available and actor=='speaker' and plan=='plan' and start=='anchor'
    def outcome(actor,plan,start,end):
        return actor=='speaker' and plan=='plan' and start=='anchor' and ((end=='left' and outleft) or (end=='right' and outright))
    def selected(actor,plan,start,end):
        return actor=='speaker' and plan=='plan' and start=='anchor' and ((end=='left' and selleft) or (end=='right' and selright))
    model.update(juperson=lambda:'speaker',juother=lambda:'other',juanchor=lambda:'anchor',jufirst=lambda:'left',jusecond=lambda:'right',
        jupeople=lambda person,point:person=='listener' and point=='anchor',juaudience=lambda person:person=='listener' and variant!='empty_audience',
        jupopulation=lambda person:person=='speaker',jueligible=lambda person:eligible,
        jureference=lambda actor,first,second:first if actor=='speaker' else second,juevents=events,
        juoccurs=occurs,juagent=agent,jupresents=presents,juconveys=conveys,jubefore=before,
        juavailable=available_fn,juoutcomes=outcome,juselected=selected)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=10_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]

def expected(bits,eligible=False):
    available,ol,orr,sl,sr,gl,gr=bits
    valid=(sl or sr) and (not sl or ol) and (not sr or orr)
    capable=available and valid and (not sl or gl) and (not sr or gr)
    incapable=(not available or valid) and not capable
    return [gl,gr,capable,incapable,not capable or eligible,eligible or incapable,True]

def build_report():
    documents={}
    for name,text in build().items():
        assert (ROOT/name).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[name]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for bits in product((False,True),repeat=7):
        result=values(bits);assert result==expected(bits),(bits,result,expected(bits));matrix.append(dict(bits=bits,result=result))
    contrasts={}
    for variant in ('empty_events','short_events','extra_events','reversed_events','duplicate_event','other_actor','other_listener','swapped_messages',
                    'other_speaker_content','no_order','self_order','two_way_order','empty_audience'):
        result=values(variant=variant);assert result==[False,False,False,True,True,True,True],(variant,result);contrasts[variant]=result
    assert values(variant='repeated_message',indices=(0,1))==[True,True]
    for variant in ('unknown_occurrence','unknown_availability'):assert values(variant=variant,indices=(6,))==[True]
    assert values(memoize=False,indices=(0,1,2,3,6))==values(indices=(0,1,2,3,6))
    assert values(variant='current_point',indices=(0,2))==[False,True]
    programs=[]
    for length in range(4):
        for pattern in product((0,1),repeat=length):
            result=values(program=pattern,indices=(0,1));assert result==[bool(pattern)]*2
            programs.append(dict(pattern=pattern,result=result))
    assert values(program=(0,1,0,1),indices=(0,1))==[True,True]
    paths=[LIBRARY,EXAMPLE,BASIS,ABILITY,PARENT,'scripts/compose_utterance_ability.py','scripts/check_utterance_ability.py','tests/test_utterance_ability.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    result=dict(status='utterance_realization_and_relative_ability_not_full_source_can_semantics',documents=documents,new_definitions=6,new_library_primitives=0,
        roundtrips=True,matrix=matrix,contrasts=contrasts,repeated_message_with_distinct_events=True,programs=programs,limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Ordered realization, assessed ability and necessary-only eligibility verified')

if __name__=='__main__':main()
