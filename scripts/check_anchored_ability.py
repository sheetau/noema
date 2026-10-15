"""Check reference validity independently of successful or impossible utterance."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_anchored_ability import ROOT,LIBRARY,EXAMPLE,BASIS,PREVIOUS,PARENT,build,basis
from scripts.compose_shared_quotation import FIELDS,PERMISSION,OBEY

REPORT=ROOT/'reports/anchored-ability-v1.json'
DOMAIN=('speaker','other','listener','a','b','plan')
SCENES=('anchor','left','right')

@lru_cache(maxsize=32)
def setup(speaker=True,context=True,variant='baseline'):
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))
    extra=parse('p:r jbalias[] a.r jbdate[] d.r jbpeople[a d] c.')['declarations']
    doc['declarations']=extra+doc['declarations']
    speaker_symbol='juperson' if speaker else 'juother'
    context_symbol='juanchor' if context else 'jusecond'
    hearers_symbol='jupeople'
    if variant in ('alias_references','unknown_speaker'):speaker_symbol='jbalias'
    if variant in ('alias_references','unknown_context'):context_symbol='jbdate'
    if variant in ('alias_references','unknown_hearers'):hearers_symbol='jbpeople'
    def replacement(name,body):next(d for d in doc['declarations'] if d['name']==name)['body']=body
    replacement('jbspeaker',dict(kind='quote',rank=1,body=dict(kind='call',symbol=speaker_symbol,arguments=[])))
    replacement('jbcontext',dict(kind='quote',rank=1,body=dict(kind='call',symbol=context_symbol,arguments=[])))
    replacement('jbhearers',dict(kind='quote',rank=1,body=dict(kind='function_ref',symbol=hearers_symbol)))
    doc=parse(format_graph(doc,'compact'))
    refs={n:'p hzs'+n for n,_ in FIELDS};refs.update(source='k '+speaker_symbol+'[]',anchor='k '+context_symbol+'[]',people='p '+hearers_symbol,required='p h7a',allowed='p h7b')
    literals=['r b[c[i[content e][j '+force+'[v content]]][c[p '+symbol+']['+' '.join(refs[n] for n,_ in fields)+']]]'
        for force,symbol,fields in [('s','rub',PERMISSION),('m','rua',OBEY)]]
    probe=deepcopy(doc);probe['statements']=[]
    probe=parse(format_graph(probe,'compact')+''.join('q[e['+x+']['+x+']].' for x in literals))
    expected=[d['body']['arguments'][0]['body'] for d in probe['statements']]
    return doc,expected

def values(*,speaker=True,hearers=True,context=True,success=True,eligible=False,available=True,selected=True,
           variant='baseline',indices=None,memoize=True):
    original,expected=setup(speaker,context,variant);doc=deepcopy(original)
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('Quoted normative contents were evaluated')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def people(person,point):
        if variant=='empty_audience':return False
        if variant=='later_audience' and point!='anchor':return person=='other'
        if not hearers:return person=='other'
        if variant=='extra_hearer':return person in ('listener','other') and point=='anchor'
        if variant=='missing_hearer':return False
        return person=='listener' and point=='anchor'
    def audience(person):return variant!='empty_audience' and person=='listener'
    def events(actor,point):return SequenceValue(('a','b') if actor=='speaker' else (),json.dumps('individual'))
    def occurs(event,point):return success and event in ('a','b') and point in ('left','right')
    def conveys(event,code,point):
        return event in ('a','b') and code.rank==1 and json.loads(code.syntax)==expected[('a','b').index(event)]
    def availability(actor,plan,start):
        if variant=='unknown_availability':raise ValueError('Unknown availability')
        return available and (actor,plan,start)==('speaker','plan','anchor')
    def outcome(actor,plan,start,end):return (actor,plan,start)==('speaker','plan','anchor') and end in ('left','right')
    model.update(juperson=lambda:'speaker',juother=lambda:'other',juanchor=lambda:'anchor',jufirst=lambda:'left',jusecond=lambda:'right',
        jbalias=lambda:'speaker',jbdate=lambda:'anchor',jbpeople=people,jupeople=people,juaudience=audience,
        jupopulation=lambda actor:actor=='speaker',jueligible=lambda actor:eligible,
        jureference=lambda actor,first,second:first if actor=='speaker' else second,juevents=events,
        juoccurs=occurs,juagent=lambda actor,event,point:actor=='speaker' and event in ('a','b'),
        jupresents=lambda event,person,point:person=='listener',juconveys=conveys,
        jubefore=lambda first,second,point:(first,second)==('a','b'),juavailable=availability,juoutcomes=outcome,
        juselected=lambda actor,plan,start,end:selected and outcome(actor,plan,start,end))
    for name,symbol in [('unknown_speaker','jbalias'),('unknown_context','jbdate'),('unknown_hearers','jbpeople')]:
        if variant==name:
            def unknown(*args):raise ValueError('Unknown reference')
            model[symbol]=unknown
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=10_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]

def result_for(valid,can,cannot,eligible):
    return [valid,valid and can,valid and cannot,valid and (not can or eligible),valid and (eligible or cannot),can,cannot,True]

def lower_rank_refused():
    doc=deepcopy(setup()[0]);doc['statements']=doc['statements'][-1:]
    for node in doc['statements'][0]['body']['arguments']:node['rank']=1
    try:parse(format_graph(doc,'compact'))
    except ValueError as error:
        assert 'strictly lower ranks' in str(error)
    else:raise AssertionError('Rank-one reference evaluation was hidden in a rank-one quotation')
    return True

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
    for speaker,hearers,context,success,eligible in product((False,True),repeat=5):
        result=values(speaker=speaker,hearers=hearers,context=context,success=success,eligible=eligible)
        valid=speaker and hearers and context;assert result==result_for(valid,success,not success,eligible)
        matrix.append(dict(speaker=speaker,hearers=hearers,context=context,success=success,eligible=eligible,result=result))
    contrasts={}
    for name,valid,can,cannot in [('alias_references',True,True,False),('later_audience',True,True,False),
        ('extra_hearer',False,True,False),('missing_hearer',False,True,False),('empty_audience',True,False,True)]:
        result=values(variant=name);assert result==result_for(valid,can,cannot,False);contrasts[name]=result
    for name in ('unknown_speaker','unknown_context','unknown_hearers','unknown_availability'):
        assert values(variant=name,indices=(7,))==[True]
    assert values(speaker=False,available=False)==result_for(False,False,True,False)
    assert values(selected=False)==result_for(True,False,False,False)
    assert values(memoize=False,indices=(0,1,2,7))==values(indices=(0,1,2,7))
    paths=[LIBRARY,EXAMPLE,BASIS,PREVIOUS,PARENT,'scripts/compose_anchored_ability.py','scripts/check_anchored_ability.py','tests/test_anchored_ability.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    result=dict(status='reference_mismatch_cannot_prove_inability_or_only_restriction',documents=documents,new_definitions=6,new_library_primitives=0,
        roundtrips=True,lower_rank_refused=lower_rank_refused(),matrix=matrix,contrasts=contrasts,limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Quoted referents, capability polarities and guarded necessary conditions verified')

if __name__=='__main__':main()
