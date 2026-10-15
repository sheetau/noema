"""Verify ordered attribution, quotation identity and preservation of the content."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_ordered_contrast import ROOT, PARENT, LIBRARY, SOURCE, CORE, BASIS, build, basis
from scripts.compose_qualified_utterance import closure
from scripts import check_faculty_opportunities as previous

REPORT=ROOT/'reports/ordered-contrast-v1.json'
DOMAIN=('whole','author','first','second','scope','other')
SCENES=('anchor','other')
FLAGS=('left','right','forward','reverse','contrast','combined')


@lru_cache(maxsize=4)
def document(path): return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def generic_fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jonode[] a.r joauthor[] a.r jofirst[] a.r josecond[] a.r joscope[] a.r jocontext[] d.
r jorecord[a a i d[e] a d] c.r jocontrast[a a i d[e] i d[e] a d] c.r jobefore[a a d] c.
r jotruth[d] c.
d joleft[] e[b scene[k jotruth[v scene]]].
d joright[] e[b scene[k jotruth[v scene]]].
q[k rw3[k jonode[] k joauthor[] k jofirst[] k josecond[] r d[k joleft[]] r d[k joright[]]
 k joscope[] k jocontext[] p jorecord p jocontrast p jobefore]].''')


def forbidden(*args): raise AssertionError('Attribution evaluated the attributed content')


def is_code(code, name):
    return code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol=name,arguments=[])


def callbacks(*,source=False,flags=(True,True,True,False,True,True),variant='baseline'):
    state=dict(zip(FLAGS,flags,strict=True))
    left,right=('iafleft','iafright') if source else ('joleft','joright')
    def record(node,author,code,scope,scene):
        if variant=='unknown_records': raise ValueError('Unknown discourse record')
        if (author,scope,scene)!=('author','scope','anchor'): return False
        if node=='whole': return state['combined'] and is_code(code,'iaecontrast')
        if node=='first': return state['left'] and is_code(code,right if variant=='swapped_records' else left)
        if node=='second': return state['right'] and is_code(code,left if variant=='swapped_records' else right)
        return False
    def contrast(node,author,first,second,scope,scene):
        if variant=='unknown_contrast': raise ValueError('Unknown contrast presentation')
        expected_author='other' if variant=='contrast_other_author' else 'author'
        expected_scope='other' if variant=='contrast_other_scope' else 'scope'
        expected_scene='other' if variant=='contrast_other_context' else 'anchor'
        expected_node='other' if variant=='contrast_other_node' else 'whole'
        return (state['contrast'] and (node,author,scope,scene)==(expected_node,expected_author,expected_scope,expected_scene)
            and is_code(first,right if variant=='swapped_contrast' else left)
            and is_code(second,left if variant=='swapped_contrast' else right))
    def before(first,second,scene):
        if variant=='unknown_order': raise ValueError('Unknown discourse order')
        return scene==('other' if variant=='order_other_context' else 'anchor') and (
            (first,second)==('first','second') and state['forward'] or
            (first,second)==('second','first') and state['reverse'])
    values={
        'node':lambda:'whole','author':lambda:'other' if variant=='other_author' else 'author',
        'first':lambda:'first','second':lambda:'first' if variant=='same_nodes' else 'second',
        'scope':lambda:'other' if variant=='other_scope' else 'scope',
        'context':lambda:'other' if variant=='other_context' else 'anchor',
        'record':record,'contrast':contrast,'before':before,'truth':forbidden}
    if source:
        names=dict(node='iacnode',author='wa',first='iafleftnode',second='iafrightnode',scope='iacscope',
            context='wh',record='iaereport',contrast='iafpresents',before='ue')
        return {names[key]:value for key,value in values.items() if key in names}
    return {'jo'+key:value for key,value in values.items()}


def values(path=None,*,memoize=True,**options):
    doc=deepcopy(document(path) if path else generic_fixture())
    if path: doc['statements']=doc['statements'][-1:]
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    primitives.update(callbacks(source=path is not None,**options))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives,
        memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(maxsize=1)
def content_fixture():
    doc=deepcopy(previous.fixture()); doc['statements']=[]
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iafleft','iafright']):
        if d['name'] not in names: doc['declarations'].append(d); names.add(d['name'])
    return parse(format_graph(doc,'compact')+'''
q[t[k iafleft[]][k jalanchor[]]].q[t[k iafright[]][k jalanchor[]]].
q[t[k iaecontrast[]][k jalanchor[]]].''')


def content_values(**options):
    return previous.evaluate(content_fixture(),previous.model(**options),previous.DOMAIN,previous.SCENES,budget=10_000_000)


VARIANTS=('other_author','other_scope','other_context','same_nodes','swapped_records','swapped_contrast',
    'contrast_other_author','contrast_other_scope','contrast_other_context','contrast_other_node','order_other_context')
UNKNOWNS=('unknown_records','unknown_contrast','unknown_order')
CONTENT_CASES=({},dict(variant='empty_faculties'),dict(variant='other_person_lacks_room'),
    dict(table=2),dict(joint=True),dict(table=0),dict(table=15))


def alignment():
    units=json.loads((ROOT/previous.previous.previous.UNITS).read_text(encoding='utf-8'))['units']
    unit=next(u for u in units if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        segments=[dict(start=a,end=b,text=unit['text'][a:b]) for a,b in ((467,562),(564,609),(611,714))],
        definitions=['iafleft','iafright','iafparallel','iafannotation'],semantic_completion=False,
        adds_new_text_coverage=False,remaining_concession='doch expectation is not inferred from advantage')


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for flags in product((False,True),repeat=6):
        a,b,f,r,c,combined=flags
        generic=values(flags=flags); source=values(CORE,flags=flags)
        assert generic==[a and b and f and not r and c]
        assert source==[a and b and f and not r and c and combined]
        matrix.append(dict(flags=list(flags),generic=generic,source=source))
    for path in (None,CORE,SOURCE):
        assert values(path)==[True] and values(path,memoize=False)==[True]
        for variant in VARIANTS: assert values(path,variant=variant)==[False],(path,variant)
        for variant in UNKNOWNS:
            try: values(path,variant=variant)
            except ValueError as error: assert 'Unknown' in str(error)
            else: raise AssertionError((path,variant))
    contents=[]
    for options in CONTENT_CASES:
        result=content_values(**options)
        assert result[2]==(result[0] and result[1]),(options,result)
        contents.append(dict(options=options,values=result))
    assert {tuple(row['values']) for row in contents}=={
        (True,True,True),(True,False,False),(False,True,False),(False,False,False)}
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,'scripts/compose_ordered_contrast.py','scripts/check_ordered_contrast.py',
        'tests/test_ordered_contrast.py','scripts/check_faculty_opportunities.py',previous.previous.previous.UNITS,
        'noema/constructed.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='ordered_nonfactive_contrast_connected',documents=documents,attribution_matrix=matrix,
        content_integration=contents,source_alignment=alignment(),roundtrips=True,attribution_uncached_checked=True,
        content_uncached_checked=False,content_step_budget=10_000_000,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream: json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Ordered attribution and unchanged content conjunction verified; semantic completion remains open')


if __name__=='__main__': main()
