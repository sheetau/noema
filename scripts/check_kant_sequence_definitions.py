"""Integrate all five sequence constructors with saved public definitions."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json,time
from scripts.kant_page_public_context import ROOT,BRIDGE
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.kant_lexical_context import LexicalContext
from scripts.shared_modality import renamed
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_sequences import pins as prior_pins
from scripts.kant_structural_trial import prepare as trial,report

ORIGINALS=('rdr','r2pv','rcx','r2ai')
KINDS=frozenset(('sequence','length','position','concat','fold'))
OUT=ROOT/'output/kant-sequence-definitions'
RUN=ROOT/'.noema-project/runs/kant-sequence-definitions-v1'


def constructors(value):
    if isinstance(value,list):return set().union(*(constructors(v) for v in value))
    if not isinstance(value,dict):return set()
    kind=value.get('kind')
    own={kind} if kind in KINDS and (kind!='sequence' or 'items' in value) else set()
    return own|set().union(*(constructors(v) for v in value.values()))


@lru_cache(maxsize=1)
def inputs():
    prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=prior['source_sha256'][name]:
            raise ValueError('Saved sequence definition input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'));rows=[]
    for original in ORIGINALS:
        source=next(d for d in bridge['source_declarations'] if d['name']==original)
        declaration=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][original])
        if renamed(source,bridge['mapping'])!=declaration:raise ValueError('Definition differs from its source/name bridge')
        body=deepcopy(declaration['body']);equation=declaration['result']!='truth'
        if equation:
            reference=dict(kind='call',symbol=declaration['name'],arguments=[dict(kind='variable',name=p['name']) for p in declaration['parameters']])
            body=dict(kind='equal',arguments=[body,reference])
        for p in reversed(declaration['parameters']):body=dict(kind='forall',variable=p['name'],sort=p['sort'],body=body)
        rows.append((declaration,dict(kind='assert',body=body),equation))
    return published,rows


def cases():
    return [(key,'既存定義 '+key+' の列構文と束縛',row[1]) for key,row in zip(ORIGINALS,inputs()[1])]


@lru_cache(maxsize=4)
def checked(index):
    published,rows=inputs();declaration,source,equation=rows[index]
    started=time.perf_counter()
    drawing=compile_statement(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(published))
    if recovered!=source:raise ValueError('Sequence definition scope changed')
    body=recovered['body']
    for p in declaration['parameters']:
        if (body['kind'],body['variable'],body['sort'])!=('forall',p['name'],p['sort']):
            raise ValueError('Definition parameter changed')
        body=body['body']
    if equation:body=body['arguments'][0]
    if body!=declaration['body']:raise ValueError('Sequence definition body changed')
    key,label,_=cases()[index]
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],seconds=time.perf_counter()-started,
        original_symbol=key,public_symbol=declaration['name'],declaration_sha256=syntax_hash(declaration),
        body_sha256=syntax_hash(body),syntax_sha256=syntax_hash(source),sequence_constructors=sorted(constructors(body)),
        diagnostic_equation=equation,branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'reports/kant-sequences-v2.json',
                 'scripts/check_kant_sequence_definitions.py','tests/test_kant_sequence_definitions.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-sequence-definitions-1',version=VERSION,title='既存定義の列構文を読む',
        intro='保存された定義本体を元の引数範囲で閉じ、列の五つの構成子を実際の図形から読み戻します。',
        limits=['Four saved native definition bodies; wrappers are structural diagnostics, not declaration writing or new semantic assertions',
                'Remaining constructors, full-page integration and visual approval remain incomplete'])


def build_report():return report(OUT,pins)
