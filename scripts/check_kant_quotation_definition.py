"""Connect existing definition rqtk to the three quotation operators.

Its described content is disquoted and evaluated under a diagnostic situation
binder. The wrapper is not a new semantic assertion or a definition declaration.
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
from scripts.check_kant_quotation_operations import pins as prior_pins
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

ORIGINAL='rqtk'
OUT=ROOT/'output/kant-quotation-definition'
RUN=ROOT/'.noema-project/runs/kant-quotation-definition-v1'


@lru_cache(maxsize=1)
def inputs():
    prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=prior['source_sha256'][name]:
            raise ValueError('Published quotation definition input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))
    original=next(d for d in bridge['source_declarations'] if d['name']==ORIGINAL)
    declaration=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][ORIGINAL])
    if renamed(original,bridge['mapping'])!=declaration:
        raise ValueError('Published quotation definition differs from its original')
    if declaration['result']!=dict(kind='description',result='content',rank=1):
        raise ValueError('Existing quotation result type changed')
    body=dict(kind='evaluate',content=dict(kind='disquote',description=deepcopy(declaration['body']),rank=1),
        situation=dict(kind='variable',name='vc'))
    body=dict(kind='forall',variable='vc',sort='situation',body=body)
    for p in reversed(declaration['parameters']):body=dict(kind='forall',variable=p['name'],sort=p['sort'],body=body)
    return published,declaration,dict(kind='assert',body=body)


def cases():return [('definition-body','既存定義 rqtk の引用構成・持ち上げ・復号',inputs()[2])]


@lru_cache(maxsize=1)
def checked(index):
    if index!=0:raise IndexError(index)
    published,declaration,source=inputs()
    drawing=compile_statement(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(published))
    if recovered!=source:raise ValueError('Quotation definition diagnostic changed native syntax')
    body=recovered['body']
    for p in declaration['parameters']:
        if (body['kind'],body['variable'],body['sort'])!=('forall',p['name'],p['sort']):
            raise ValueError('Quotation definition parameter changed')
        body=body['body']
    original_body=body['body']['content']['description']
    if original_body!=declaration['body']:raise ValueError('Quotation definition body changed')
    key,label,_=cases()[0]
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        original_symbol=ORIGINAL,public_symbol=declaration['name'],declaration_sha256=syntax_hash(declaration),
        body_sha256=syntax_hash(original_body),syntax_sha256=syntax_hash(source),
        branch_limits=drawing['branch_limits'],unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'scripts/check_kant_function_definition_body.py',
                 'scripts/check_kant_quotation_definition.py','tests/test_kant_quotation_definition.py',
                 'reports/kant-quotation-operations-v1.json'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,
        preserved_count=0,schema='kant-quotation-definition-1',version=VERSION,
        title='既存の引用構成の定義本体を読む',
        intro='保存済み定義 rqtk の本体を元の引数束縛の下で描きます。結果の記述を解き、検査用の状況において評価する構文です。新しい主張や定義宣言の完成形ではありません。',
        limits=['One unchanged existing definition body and a diagnostic wrapper, not a new semantic assertion',
                'Definition declarations, page layout, remaining native constructors and visual approval remain incomplete'])


def build_report():return diagnostic_report(OUT,pins)
