"""Preserved cut arithmetic with explicit domains for partial operations."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document, function_sort
from noema.meaning_catalog import _references
from scripts import shared_real_cuts as previous
from scripts.shared_real_cuts import ROOT, catalog, injective_mapping, require, digest, encoded, write_new
from scripts.shared_modality import renamed, call, v, op
from scripts.shared_reference import definition
from scripts.shared_time import allof
from scripts.visible_cuts_vocabulary import CutsVocabulary

LIBRARY='examples/v016/shared-cut-products-v1.noema'
BASIS='data/shared-cut-products-basis-v1.json'
BRIDGE='data/einstein-cut-products-correspondence-v1.json'
CUT=function_sort(['number'],'truth')
DEFINITIONS=dict(sag='cutmutualrelation',sah='cutnonnegativeproduct',sca='cutvalueequal',
    shu='cutabsolute',shv='cutproduct',sjd='cutpositivereciprocal',sje='cutpositivequotient',
    sju='cutnonnegative',sjt='cutreciprocal',sky='cutsqrtcandidate')
MAPPING=previous.MAPPING|DEFINITIONS
MEANINGS={
 'cutmutualrelation':'二つの有理数上の性質について、指定された二項関係が両方向で成立する。指定関係を包含とした場合に値の一致を表す。任意の関係そのものが包含や等号だとは仮定しない。',
 'cutnonnegativeproduct':'q<0、または左と右にそれぞれ正の有理数xとyが含まれq<x*yとなる、という性質を返す。非負の有効な切断を入力するときにその積として使う。',
 'cutvalueequal':'左右の性質が互いに含まれる。これは全有理数での外延的一致であり、関数の記述や引用された名前の同一性ではない。実数値の一致として使うときは両入力のcutvalidを要求する。',
 'cutabsolute':'零の切断が入力に含まれる場合は入力を、それ以外ではcutnegateを選ぶ。有効な切断を入力するときに絶対値として使う。',
 'cutproduct':'両入力の絶対値の非負積を作り、同符号ならそのまま、異符号なら符号反転する。有効な切断を入力するときに符号付きの積として使う。',
 'cutpositivereciprocal':'q<0、または正の有理数uが入力に含まれずq*u<1となる、という性質を返す。正の有効な切断だけを逆数の入力にする。零や負の入力に対する出力を逆数としない。',
 'cutpositivequotient':'分子と、分母のcutpositivereciprocalとのcutproduct。分子のcutvalidと、分母が正の有効な切断であることを利用側で要求する。',
 'cutnonnegative':'零の切断が入力の性質に含まれる。有効な実切断について零以上の値を表すが、入力の有効性自体は検査しない。',
 'cutreciprocal':'非負判定に従って正の逆数候補を使うか、入力を符号反転して正の逆数候補を作り再び符号反転する。非零の有効な切断を入力するときだけ逆数として使う。',
 'cutsqrtcandidate':'q<0または入力がq*qを含む、という性質を返す。非負の有効な切断を入力するときだけ非負の平方根として使う。負の入力を許す平方根の関係ではない。',
 'cutproductrelation':'左右と結果が全て有効な切断であり、結果が左右のcutproductと外延的に一致する。',
 'cutreciprocalrelation':'入力と結果が有効な切断で、入力が零と外延的に異なり、結果がcutreciprocalと外延的に一致する。',
 'cutquotient':'分子と分母のcutreciprocalとのcutproductを返す。符号を問わず非零の有効な分母と有効な分子を利用条件とする。',
 'cutquotientrelation':'分子・分母・結果が有効な切断で、分母が零と外延的に異なり、結果がcutquotientと外延的に一致する。',
 'cutsqrtrelation':'入力と結果が有効な切断で、入力が非負であり、結果がcutsqrtcandidateと外延的に一致する。平方根の負の枝を含めない。'}
ROLES=dict(cutmutualrelation=['left','right','relation'],cutnonnegativeproduct=['left','right'],
    cutvalueequal=['left','right'],cutabsolute=['candidate'],cutproduct=['left','right'],
    cutpositivereciprocal=['candidate'],cutpositivequotient=['numerator','denominator'],
    cutnonnegative=['candidate'],cutreciprocal=['candidate'],cutsqrtcandidate=['candidate'],
    cutproductrelation=['left','right','result'],cutreciprocalrelation=['candidate','result'],
    cutquotient=['numerator','denominator'],cutquotientrelation=['numerator','denominator','result'],
    cutsqrtrelation=['candidate','result'])
LIMITS=[
 'fn[N]Tは実数専用の型ではない。候補関数の外側でcutvalidと演算ごとの定義域を確認する。関係の不成立は実数演算の値を返さない。',
 'cutpositivequotientは正の分母用、cutquotientは非零の分母用である。負の分母を正の逆数候補へ渡して代用しない。',
 '多項式の証明は有理数上の条件付き補題であり、全実切断の体の法則・存在・一意性・完備性の一般証明ではない。',
 '有限診断では下位演算を明示したモデルへ差し替えて引数の結合と定義域条件を検査する。この診断を実数切断のモデルや証明とはしない。',
 '原文の別名を統合しない。既存10定義の対応と、新たな5構成定義を区別する。正本の本文と以前の意味判断を変更しない。']


def zero():return call('rationalcut',dict(kind='number',numerator=0,denominator=1))


def additional_definitions():
    def add(name,body,result='truth'):
        return definition(name,[(p,CUT) for p in ROLES[name]],result,body)
    def valid(*names):return [call('cutvalid',v(n)) for n in names]
    def equal_result(body):return call('cutvalueequal',v('result'),body)
    def nonzero(name):return op('not',call('cutvalueequal',v(name),zero()))
    return [
      add('cutproductrelation',allof(*valid('left','right','result'),equal_result(call('cutproduct',v('left'),v('right'))))),
      add('cutreciprocalrelation',allof(*valid('candidate','result'),nonzero('candidate'),equal_result(call('cutreciprocal',v('candidate'))))),
      add('cutquotient',call('cutproduct',v('numerator'),call('cutreciprocal',v('denominator'))),CUT),
      add('cutquotientrelation',allof(*valid('numerator','denominator','result'),nonzero('denominator'),equal_result(call('cutquotient',v('numerator'),v('denominator'))))),
      add('cutsqrtrelation',allof(*valid('candidate','result'),call('cutnonnegative',v('candidate')),equal_result(call('cutsqrtcandidate',v('candidate')))))]


@lru_cache(maxsize=1)
def composed():
    c=catalog();injective_mapping(c.document,MAPPING)
    declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in MAPPING]
    require(_references(declarations)<=set(MAPPING),'Cut product projection has external dependencies')
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[])
    doc=injective_mapping(doc,MAPPING);doc['declarations']+=additional_definitions()
    doc=normalize_document(doc);parent=CutsVocabulary()
    for d in doc['declarations']:
        if d['name'] in parent._words:require(d==parent._plain_declaration(d['name']),'Existing cut definition changed')
    return doc


@lru_cache(maxsize=1)
def basis():
    old=deepcopy(previous.basis());parent=CutsVocabulary()
    for d in composed()['declarations']:
        name=d['name']
        if name in parent._words:
            entry=parent.entry(name)
            old['public_contracts'][name]['interpretation_inputs']=entry['context']
            continue
        old['definitions'][name]=MEANINGS[name]
        old['public_contracts'][name]=dict(arguments=[dict(role=n,sort=p['sort']) for n,p in zip(ROLES[name],d['parameters'],strict=True)],
            result=d['result'],interpretation_inputs=['有理数は標準の正確な算術で解釈する。','候補関数の利用時に切断の有効性と非零・非負など各演算の定義域を確認する。'])
    old.update(status='shared_preserved_cut_arithmetic_and_explicit_domains',document=LIBRARY,
        preserved_sources=[dict(document=previous.SELECTED,basis=previous.SELECTED_BASIS,renaming=MAPPING)],
        new_compositions=[d['name'] for d in additional_definitions()],limitations=LIMITS)
    return old


@lru_cache(maxsize=1)
def correspondence():
    c=catalog();targets={d['name']:d for d in composed()['declarations']};direct,_=c._dependencies()
    def closure(names):
        seen=set();pending=set(names)
        while pending:
            n=pending.pop()
            if n not in seen:seen.add(n);pending.update(direct[n]-seen)
        return seen
    uses=[closure(_references(s)) for s in c.document['statements']];rows=[]
    for old,new in DEFINITIONS.items():
        entry=c.entries[old];d=targets[new]
        require(renamed(entry['declaration'],MAPPING)==d,'Selected definition body changed')
        rows.append(dict(source_symbol=old,shared_word=new,source_basis=entry['meaning_basis'],
            source_meaning=entry['meaning_ja'],shared_meaning=MEANINGS[new],
            source_declaration_sha256=digest(encoded(entry['declaration'])),shared_declaration_sha256=digest(encoded(d)),
            direct_dependencies=sorted(direct[old]),statement_indices=[i for i,names in enumerate(uses) if old in names],
            judgment='injective_renaming_of_typed_definition_with_explicit_domain_contract'))
    return dict(schema='noema-public-word-correspondence-1',work='einstein-1905',document=previous.SELECTED,
        document_sha256=digest((ROOT/previous.SELECTED).read_bytes()),library=LIBRARY,rows=rows,
        previous_correspondence=previous.BRIDGE,combined_mapping=MAPPING,
        new_compositions=[d['name'] for d in additional_definitions()],reviewer='assistant',
        original_manuscript_modified=False,old_reviews_rebound=False,quotation_names_merged=False,
        full_manuscript_mapping_complete=False)


def prepare():
    write_new(LIBRARY,format_graph(composed())+'\n');write_new(BASIS,basis());write_new(BRIDGE,correspondence())
