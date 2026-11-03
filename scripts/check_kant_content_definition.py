"""Recover the saved content definition bf in its defining equation.

This is a closed structural diagnostic, not a renderer of a declaration and
not a newly registered assertion from the source work.
"""
from functools import lru_cache
from copy import deepcopy
import hashlib,json

from scripts.kant_page_public_context import ROOT,BRIDGE
from scripts.kant_lexical_context import LexicalContext
from scripts.shared_modality import renamed
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_content_binding import pins as prior_pins
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

ORIGINAL='bf'
OUT=ROOT/'output/kant-content-definition'
RUN=ROOT/'.noema-project/runs/kant-content-definition-v1'


@lru_cache(maxsize=1)
def inputs():
    prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=prior['source_sha256'][name]:
            raise ValueError('Published content definition input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))
    original=next(d for d in bridge['source_declarations'] if d['name']==ORIGINAL)
    declaration=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][ORIGINAL])
    if renamed(original,bridge['mapping'])!=declaration:
        raise ValueError('Published content definition differs from its original')
    reference=dict(kind='call',symbol=declaration['name'],arguments=[dict(kind='variable',name=p['name']) for p in declaration['parameters']])
    body=dict(kind='equal',arguments=[deepcopy(declaration['body']),reference])
    for p in reversed(declaration['parameters']):body=dict(kind='forall',variable=p['name'],sort=p['sort'],body=body)
    return published,declaration,dict(kind='assert',body=body)


def cases():return [('definition-body','既存の内容定義 bf の本体と定義呼び出し',inputs()[2])]


@lru_cache(maxsize=1)
def checked(index):
    if index!=0:raise IndexError(index)
    published,declaration,source=inputs()
    drawing=compile_statement(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(published))
    if recovered!=source:raise ValueError('Content definition equation changed native syntax')
    body=recovered['body']
    for p in declaration['parameters']:
        if (body['kind'],body['variable'],body['sort'])!=('forall',p['name'],p['sort']):
            raise ValueError('Content definition parameter changed')
        body=body['body']
    if body['arguments'][0]!=declaration['body']:raise ValueError('Content definition body changed')
    key,label,_=cases()[0]
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        original_symbol=ORIGINAL,public_symbol=declaration['name'],declaration_sha256=syntax_hash(declaration),
        body_sha256=syntax_hash(body['arguments'][0]),syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'scripts/check_kant_function_definition_body.py',
                 'scripts/check_kant_content_definition.py','tests/test_kant_content_definition.py',
                 'reports/kant-content-binding-v1.json'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,
        preserved_count=0,schema='kant-content-definition-1',version=VERSION,
        title='既存の内容定義の本体を読む',
        intro='保存済み定義 bf の引数を束縛し、元の本体とその定義呼び出しを等式で並べた構文確認です。定義宣言や原典の新しい主張として登録するものではありません。',
        limits=['One saved definition body in its defining equation; no new semantic assertion or declaration syntax',
                'Remaining expressions, declaration writing, page layout and visual approval are incomplete'])


def build_report():return diagnostic_report(OUT,pins)
