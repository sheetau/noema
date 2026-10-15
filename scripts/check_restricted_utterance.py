"""Check an open qualification template and its precise source annotation."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from unittest.mock import patch
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts import check_anchored_ability as previous
from scripts.compose_origin_clock import definition
from scripts.compose_restricted_utterance import ROOT,PARENT,ABILITY,SOURCE,CORE,BASIS,PROVIDERS,primitive,build,basis

REPORT=ROOT/'reports/restricted-utterance-v1.json'
UNITS='artifacts/written-units-v1/kant-1784.json'


@lru_cache(maxsize=2)
def source_document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=32)
def setup(speaker=True,context=True,variant='baseline'):
    doc,expected=previous.setup(speaker,context,variant)
    doc=deepcopy(doc);doc['statements']=[];text=format_graph(doc,'compact')
    for name,sort in PROVIDERS:
        if name in ('speakerfor','hearersfor','contextfor'):continue
        text+=primitive('hzt'+name,sort)
    for name,symbol,sort in [('speakerfor','jbspeaker','i b[a]'),('hearersfor','jbhearers','i b[h[a d] c]'),('contextfor','jbcontext','i b[d]')]:
        text+=definition('hzt'+name,'actor a anchor d','k '+symbol+'[v actor]',sort)
    doc=parse(text)
    doc['declarations'].append(deepcopy(next(d for d in source_document(CORE)['declarations'] if d['name']=='hztonly')))
    text=format_graph(doc,'compact')+'r jzcriterion[a d] c.'
    expression='k hztonly[p jzcriterion k juanchor[]]'
    code='r c['+expression+']'
    return parse(text+'q['+expression+'].q[e['+code+']['+code+']].'),expected


def values(*,speaker=True,hearers=True,context=True,success=True,eligible=False,available=True,selected=True,
           variant='baseline',indices=(0,1),memoize=True):
    fixture=setup(speaker,context,variant)
    def evaluate(doc,**kwargs):
        model=kwargs['primitives']
        def criterion(actor,anchor):
            if variant=='unknown_criterion':raise ValueError('Unknown qualification')
            return eligible and actor==('other' if variant=='criterion_wrong_person' else 'speaker') and anchor==('left' if variant=='criterion_wrong_anchor' else 'anchor')
        model['jzcriterion']=criterion
        model['hztpopulation']=lambda actor:variant!='empty_population' and actor=='speaker'
        model['hztaudiencefor']=lambda actor,recipient,anchor:anchor==('left' if variant=='wrong_audience_anchor' else 'anchor') and model['juaudience'](recipient)
        for name,sort in PROVIDERS:
            if name in ('population','audiencefor','speakerfor','hearersfor','contextfor'):continue
            model['hzt'+name]=model['juevents' if name=='eventsfor' else 'ju'+name]
        return evaluate_document(doc,**kwargs)
    with patch.object(previous,'setup',return_value=fixture),patch.object(previous,'evaluate_document',side_effect=evaluate):
        return previous.values(speaker=speaker,hearers=hearers,context=context,success=success,eligible=eligible,
            available=available,selected=selected,variant=variant,indices=indices,memoize=memoize)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(source_document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Open qualification or quoted speech was evaluated during annotation')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hztonly')
    model.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hztannotation=report)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]


def lower_rank_refused():
    doc=deepcopy(setup()[0]);doc['statements']=doc['statements'][-1:]
    for node in doc['statements'][0]['body']['arguments']:node['rank']=1
    try:parse(format_graph(doc,'compact'))
    except ValueError as error:assert 'strictly lower ranks' in str(error)
    else:raise AssertionError('Reference evaluation hidden in a same-rank quote')
    return True


def alignment():
    corpus=json.loads((ROOT/UNITS).read_text(encoding='utf-8'))
    unit=next(u for u in corpus['units'] if u['id']=='kant-1784:u0017')
    segments=[]
    for phrase in ('nur derjenige','kann das sagen'):
        start=unit['text'].index(phrase);segments.append(dict(start=start,end=start+len(phrase),text=phrase))
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],segments=segments,
        definitions=['hztonly','hztattribution'],status='explicit_interpretive_annotation',semantic_completion=False,
        open_qualification=True,qualification_lexemes_counted=False)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    parent=source_document(PARENT);child=source_document(SOURCE)
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert child['statements'][:-1]==parent['statements']
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for speaker,hearers,context,success,eligible in product((False,True),repeat=5):
        result=values(speaker=speaker,hearers=hearers,context=context,success=success,eligible=eligible)
        assert result==[speaker and hearers and context and (not success or eligible),True]
        matrix.append(dict(bits=[speaker,hearers,context,success,eligible],result=result))
    contrasts={}
    for name in ('criterion_wrong_person','criterion_wrong_anchor','wrong_audience_anchor','extra_hearer','missing_hearer'):
        result=values(variant=name,eligible=True);assert result==[False,True],(name,result);contrasts[name]=result
    for name in ('alias_references','later_audience','empty_population'):
        result=values(variant=name,eligible=True);assert result==[True,True],(name,result);contrasts[name]=result
    assert values(eligible=False,selected=False)==[True,True]
    assert values(eligible=False,available=False)==[True,True]
    assert values(success=False,eligible=True)==[True,True]
    for name in ('unknown_criterion','unknown_speaker','unknown_context','unknown_hearers','unknown_availability'):
        assert values(variant=name,indices=(1,))==[True]
    assert values(eligible=True,memoize=False)==[True,True]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for name in ('node','author','scope','context'):assert attribution(path,name)==[False]
    paths=[PARENT,ABILITY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_restricted_utterance.py','scripts/check_restricted_utterance.py',
        'tests/test_restricted_utterance.py','scripts/check_anchored_ability.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='partial_annotated_restriction_not_filled_qualification',documents=documents,parent_preserved=True,
        matrix=matrix,contrasts=contrasts,roundtrips=True,lower_rank_refused=lower_rank_refused(),source_alignment=alignment(),
        annotation_does_not_evaluate_qualification=True,verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Open qualification, aligned utterance restriction and source annotation verified')


if __name__=='__main__':main()
