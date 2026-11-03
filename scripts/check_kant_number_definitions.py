"""Read two saved definition bodies differing in their native numeric argument.

Universal wrappers close the original parameter scopes for structural checks;
they are not new semantic assertions or a declaration writing syntax.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from scripts.kant_page_public_context import ROOT,BRIDGE
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.kant_lexical_context import LexicalContext
from scripts.shared_modality import renamed
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_numbers import pins as prior_pins
from scripts.kant_structural_trial import prepare as trial,report

ORIGINALS=('hztb','rqzf')
OUT=ROOT/'output/kant-number-definitions'
RUN=ROOT/'.noema-project/runs/kant-number-definitions-v1'


@lru_cache(maxsize=1)
def inputs():
    prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=prior['source_sha256'][name]:
            raise ValueError('Saved numeric definition input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'));rows=[]
    for original in ORIGINALS:
        source=next(d for d in bridge['source_declarations'] if d['name']==original)
        declaration=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][original])
        if renamed(source,bridge['mapping'])!=declaration:raise ValueError('Definition differs from original meaning/name bridge')
        if declaration['result']!='truth':raise ValueError('Diagnostic expects a truth-valued body')
        body=deepcopy(declaration['body'])
        for p in reversed(declaration['parameters']):body=dict(kind='forall',variable=p['name'],sort=p['sort'],body=body)
        rows.append((declaration,dict(kind='assert',body=body)))
    return published,rows


def cases():
    return [(key,'既存定義 '+key+' の数値引数と本体',row[1]) for key,row in zip(ORIGINALS,inputs()[1])]


@lru_cache(maxsize=2)
def checked(index):
    published,rows=inputs();declaration,source=rows[index]
    drawing=compile_statement(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(published))
    if recovered!=source:raise ValueError('Numeric definition scope changed')
    body=recovered['body']
    for p in declaration['parameters']:
        if (body['kind'],body['variable'],body['sort'])!=('forall',p['name'],p['sort']):
            raise ValueError('Definition parameter changed')
        body=body['body']
    if body!=declaration['body']:raise ValueError('Numeric definition body changed')
    key,label,_=cases()[index]
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        original_symbol=key,public_symbol=declaration['name'],declaration_sha256=syntax_hash(declaration),
        body_sha256=syntax_hash(body),syntax_sha256=syntax_hash(source),
        numeric_argument=body['arguments'][-1],branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'reports/kant-numbers-v1.json',
                 'scripts/check_kant_number_definitions.py','tests/test_kant_number_definitions.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-number-definitions-1',version=VERSION,title='既存定義の数値引数を読む',
        intro='保存された hztb と rqzf の本体を、元の引数範囲で閉じて読み戻します。',
        limits=['Two saved native definition bodies; no new semantic assertions or declaration syntax',
                'Remaining constructors, page integration and visual approval are incomplete'])


def build_report():return report(OUT,pins)
