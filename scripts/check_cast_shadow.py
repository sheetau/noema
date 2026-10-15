"""Check direct-light loss and a described shadow without assuming its existence."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_cast_shadow import ROOT,LIBRARY,EXAMPLE,BASIS,AFFECT,build,basis

REPORT=ROOT/'reports/cast-shadow-v1.json'
DOMAIN=('source','blocker','patch1','patch2','path1','path2','place','region','person','state','outside')
SCENES=('anchor','elsewhere','imagined')
ALL=(True,)*8


@lru_cache(maxsize=1)
def document():return parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))


def values(flags=ALL,*,fear=True,variant='baseline',indices=(0,1,2),memoize=True):
    emit=flags[:2];clear=flags[2:4];hit=flags[4:6];opaque=flags[6:8]
    doc=deepcopy(document());doc['statements']=[doc['statements'][i] for i in indices]
    def emits(source,patch,point):
        if variant=='unknown_geometry':raise ValueError('Unknown emission geometry')
        return source==('blocker' if variant=='wrong_source' else 'source') and point==('elsewhere' if variant=='other_context' else 'anchor') and patch in ('patch1','patch2') and emit[('patch1','patch2').index(patch)]
    def route(patch,place,path,point):
        return place==('outside' if variant=='wrong_destination' else 'place') and point=='anchor' and (patch,path) in (('patch1','path1'),('patch2','path2'))
    def otherwise(path,blocker,point):
        return blocker==('source' if variant=='wrong_clear_blocker' else 'blocker') and point=='anchor' and path in ('path1','path2') and clear[('path1','path2').index(path)]
    def intercepts(blocker,path,point):
        return blocker==('source' if variant=='other_interceptor' else 'blocker') and point=='anchor' and path in ('path1','path2') and hit[('path1','path2').index(path)]
    def opacity(blocker,path,point):
        return blocker==('source' if variant=='other_opacity_object' else 'blocker') and point=='anchor' and path in ('path1','path2') and opaque[('path1','path2').index(path)]
    def contains(region,place,point):
        return variant!='empty_region' and region==('outside' if variant=='other_region' else 'region') and point=='anchor' and (place=='place' or variant=='mixed_region' and place=='outside')
    def experienced(person,state,point):
        if variant=='unknown_emotion':raise ValueError('Unknown emotional experience')
        return fear and (person,state,point)==('person','state','anchor')
    def directed(state,code,point):
        return (state,point)==('state','anchor') and json.loads(code.syntax)==dict(kind='function_ref',symbol='jytopic')
    model=dict(jysource=lambda:'source',jyblocker=lambda:'blocker',jyplace=lambda:'place',jyregion=lambda:'region',
        jyanchor=lambda:'anchor',jyperson=lambda:'person',jyemits=emits,jyroute=route,jyotherwiseclear=otherwise,
        jyintercepts=intercepts,jyopaque=opacity,jycontains=contains,jyexperienced=experienced,jydirected=directed,
        jyaversive=lambda state,point:(state,point)==('state','anchor'),
        jyanticipated=lambda state,anchor,end:(state,anchor,end)==('state','anchor','imagined'),
        jyadverse=lambda person,point:(person,point)==('person','imagined'))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=4_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def oracle(flags):
    candidate=[i for i in range(2) if flags[i] and flags[i+2]]
    lost=[i for i in candidate if flags[i+4] and flags[i+6]]
    return [bool(lost),bool(lost) and len(lost)==len(candidate),bool(lost) and len(lost)<len(candidate)]


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for bits in product((False,True),repeat=8):
        result=values(bits);assert result==oracle(bits),(bits,result)
        matrix.append(dict(bits=list(bits),result=result))
    contrasts={}
    for name in ('wrong_source','wrong_destination','wrong_clear_blocker','other_interceptor','other_opacity_object','other_context'):
        result=values(variant=name);assert result==[False,False,False],(name,result);contrasts[name]=result
    for name in ('empty_region','mixed_region'):
        result=values(variant=name,indices=(0,3,4));assert result==[True,False,False];contrasts[name]=result
    assert values(variant='other_region',indices=(0,3,4))==[True,False,True]
    integration=[]
    settings={'dark':(False,False,*ALL[2:]),'unblocked':(*ALL[:4],False,False,*ALL[6:]),
        'umbra':ALL,'penumbra':(*ALL[:4],True,False,*ALL[6:])}
    for name,bits in settings.items():
        for fear in (False,True):
            result=values(bits,fear=fear,indices=(3,4,5,6,7));shadow=name in ('umbra','penumbra')
            assert result==[shadow,shadow,fear,not fear,True]
            integration.append(dict(setting=name,fear=fear,result=result))
    assert values(variant='unknown_geometry',indices=(5,6,7))==[True,False,True]
    assert values(variant='unknown_emotion',indices=(3,4,7))==[True,True,True]
    for name,index in [('unknown_geometry',4),('unknown_emotion',5),('unknown_emotion',6)]:
        try:values(variant=name,indices=(index,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown relation was treated as a known truth value')
    assert values(memoize=False,indices=(0,1,2,5))==[True,True,False,True]
    paths=[LIBRARY,EXAMPLE,BASIS,AFFECT,'scripts/compose_cast_shadow.py','scripts/check_cast_shadow.py','tests/test_cast_shadow.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='geometric_direct_shadow_property_and_unasserted_attitude_target',documents=documents,
        new_definitions=5,new_library_primitives=0,matrix=matrix,contrasts=contrasts,integration=integration,roundtrips=True,
        source_ranges_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Source-relative direct shadows, regions and unevaluated attitude targets verified')


if __name__=='__main__':main()
