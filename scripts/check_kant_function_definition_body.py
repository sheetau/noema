"""Recover an existing higher-order definition body under its exact parameter scope.

The universal wrapper is only a closed syntax diagnostic. It is not a new claim,
nor a renderer of a definition declaration.
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
from scripts.check_kant_function_application import pins as prior_pins
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

DICTIONARY='output/kant-presentation-spellings/dictionary.json'
BASELINE='reports/kant-presentation-spellings-v1.json'
ORIGINAL='va'
OUT=ROOT/'output/kant-function-definition-body-v2'
RUN=ROOT/'.noema-project/runs/kant-function-definition-body-v2'


@lru_cache(maxsize=1)
def inputs():
    prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=prior['source_sha256'][name]:
            raise ValueError('Published definition input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))
    source=next(d for d in bridge['source_declarations'] if d['name']==ORIGINAL)
    declaration=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][ORIGINAL])
    if renamed(source,bridge['mapping'])!=declaration:
        raise ValueError('Published definition differs from its saved name bridge')
    body=deepcopy(declaration['body'])
    for p in reversed(declaration['parameters']):
        body=dict(kind='forall',variable=p['name'],sort=p['sort'],body=body)
    return published,declaration,dict(kind='assert',body=body)


def cases():
    return [('definition-body','既存定義 va の本体：同じ関数の存在例と対象への否定',inputs()[2])]


@lru_cache(maxsize=1)
def checked(index):
    if index!=0:raise IndexError(index)
    published,declaration,source=inputs()
    drawing=compile_statement(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(published))
    if recovered!=source:raise ValueError('Definition scope diagnostic changed native syntax')
    body=recovered['body']
    for p in declaration['parameters']:
        if (body['kind'],body['variable'],body['sort'])!=('forall',p['name'],p['sort']):
            raise ValueError('Definition parameter scope changed')
        body=body['body']
    if body!=declaration['body']:raise ValueError('Existing definition body changed')
    key,label,_=cases()[0]
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        original_symbol=ORIGINAL,public_symbol=declaration['name'],declaration_sha256=syntax_hash(declaration),
        body_sha256=syntax_hash(body),syntax_sha256=syntax_hash(source),
        branch_limits=drawing['branch_limits'],unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'scripts/check_kant_function_definition_body.py',
                 'tests/test_kant_function_definition_body.py','reports/kant-function-application-v1.json'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,
        preserved_count=0,schema='kant-function-definition-body-1',version=VERSION,
        title='既存の高階定義本体を読む',
        intro='保存済み定義 va の本体を、元の引数名と型を保つ束縛の下で描いた構文検査です。外側の全称は検査用で、新しい主張や定義宣言の完成形ではありません。',
        limits=['One existing definition body with a diagnostic scope wrapper, not a new assertion',
                'The nested application at [0,0,1,0] uses inline arguments after placement fallback; not all requested branches fit',
                'Definition declarations, page layout and visual approval remain incomplete'])


def build_report():return diagnostic_report(OUT,pins)
