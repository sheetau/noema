"""Preserved real-cut limits, derivatives, tagged integrals and one-sided approach."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts import shared_cut_products as previous
from scripts.shared_real_cuts import ROOT, catalog, injective_mapping, require, digest, encoded, write_new
from scripts.shared_modality import renamed
from scripts.visible_products_vocabulary import ProductsVocabulary

LIBRARY='examples/v016/shared-cut-analysis-v1.noema'
BASIS='data/shared-cut-analysis-basis-v1.json'
BRIDGE='data/einstein-cut-analysis-correspondence-v1.json'
DEFINITIONS=dict(sjo='cutfunctionvalid',sjp='cutnear',sjq='cutaccumulation',sjr='cutlimit',
    sjs='cutderivative',sxt='cutcontinuousat',sxu='cutcontinuous',sxs='cutclosedinterval',
    seda='cuttaggedcell',sedb='cutpartition',sedc='cutmeshbelow',sedd='cutriemannsum',sede='cutintegral',
    sesr='cutleftnear',sess='cutleftaccumulation',sest='cutleftdivergespositive',senz='cutinterior')
MAPPING=previous.MAPPING|DEFINITIONS
MEANINGS={
 'cutfunctionvalid':'指定定義域に属する全ての有効な実切断について、関数の値も有効な実切断である。定義域の非空性や、無効な入力への出力の条件は含めない。',
 'cutnear':'左右と半径が有効な実切断で、半径が正であり、左<右+半径かつ右<左+半径が成立する。距離が半径と等しい境界は含めない。',
 'cutaccumulation':'点が有効な実切断で、任意の正の有効な半径ごとに、その点と異なる定義域内の有効な切断が半径未満の近傍に存在する。点自身の定義域への所属は要求しない。',
 'cutlimit':'関数が指定定義域で有効で、目標値が有効な実切断、点がその定義域の集積点である。全ての正の精度に対して正の半径を選び、その穿孔近傍内の全有効入力の関数値が目標値から精度未満にある。',
 'cutderivative':'関数が定義域で有効で、点が有効かつ定義域内にある。点自身を除いた定義域で、関数値の差と入力差の逆数の積が、指定値へのcutlimitを満たす。端点では定義域に相対的な片側微分となり得る。',
 'cutcontinuousat':'関数が定義域で有効で、点が有効かつ定義域内にある。全ての正の精度に対し正の半径を選び、近傍内の全有効入力について関数値が点での値から精度未満にある。集積点であることは要求しない。',
 'cutcontinuous':'関数が定義域で有効で、その定義域の全ての有効な点でcutcontinuousatが成立する。定義域の非空性は要求しない。',
 'cutclosedinterval':'下端・上端・入力が有効な実切断で、下端が入力以下、入力が上端以下である。両端を含み、両端が一致する区間も許す。',
 'cuttaggedcell':'番号0の左端・1の右端・2の代表点が有効な実切断で、左端<右端、左端≤代表点≤右端である。ほかの番号の値は使わない。',
 'cutpartition':'下端と上端が有効で下端<上端、タグ付き区間の有限列が非空で全区間が有効である。列の順に、指定下端から指定上端まで左右端が一致してつながる。隙間・重複・順序の反転を許さない。',
 'cutmeshbelow':'正の有効な幅を与え、列の各タグ付き区間が有効で、その区間幅が指定幅より厳密に小さい。空列では成立するが、cutpartitionの非空条件を代用しない。',
 'cutriemannsum':'有限列の各区間の幅と代表点での関数値とのcutproductを、零から列の順にcutaddで集計する。空列は零の切断。分割や関数の妥当性は別に要求する。',
 'cutintegral':'有効な下端・上端・値で下端<上端、閉区間上の関数が有効である。各正の精度に対して正の分割幅を選び、その幅未満の分割が存在し、全てのその分割・代表点のリーマン和が指定値から精度未満にある。零幅・逆向き・広義の積分は含めない。',
 'cutleftnear':'境界・半径・入力が有効な実切断で半径が正、境界−半径<入力<境界である。境界自身と左端を含めない。',
 'cutleftaccumulation':'境界が有効で、全ての正の有効な半径に対してcutleftnearを満たす定義域内の入力が存在する。空の定義域や境界から離れた範囲を許さない。',
 'cutleftdivergespositive':'境界が定義域の左側からの集積点で、関数が定義域で有効である。任意の有限の有効な上限に対し正の半径を選び、左側近傍内の全定義域入力の関数値がその上限を超える。無限大を実数の値として追加しない。',
 'cutinterior':'有効な点が定義域に属し、その点を中心とするある正の有効な半径の開近傍の全有効入力が定義域に属する。孤立点や片側だけの端点を両側の内点にしない。'}
ROLES=dict(cutfunctionvalid=['domain','function'],cutnear=['left','right','radius'],
    cutaccumulation=['domain','point'],cutlimit=['domain','function','point','value'],
    cutderivative=['domain','function','point','value'],cutcontinuousat=['domain','function','point'],
    cutcontinuous=['domain','function'],cutclosedinterval=['lower','upper','point'],
    cuttaggedcell=['cell'],cutpartition=['partition','lower','upper'],cutmeshbelow=['partition','width'],
    cutriemannsum=['partition','function'],cutintegral=['lower','upper','function','value'],
    cutleftnear=['boundary','radius','point'],cutleftaccumulation=['domain','boundary'],
    cutleftdivergespositive=['domain','function','boundary'],cutinterior=['domain','point'])
LIMITS=[
 '数・関数・全有限列への量化を有限標本へ置換して真と認定しない。有限評価器や補助証明器が扱えない式は拒否する。',
 '原文の17定義は依存名の単射変更だけで保存する。関数の等号は外延的な数学的同一性であり、有限領域の実装ポインタ比較へ変えない。',
 '有理数への検証用投影はCUTをnumberへ、切断演算を正確な有理算術へ明示的に変更した別の構造診断である。実切断上の一般定理や無理数の性質の証明ではない。',
 '有限列の具体的な和・分割の診断を、全ての分割に量化した積分の存在・一意性・微積分学の基本定理の証明としない。',
 '物理的な時刻・軌跡・観測・近似の採用条件は利用側で接続する。共有解析語だけから原文の物理的前提を補わない。']


@lru_cache(maxsize=1)
def composed():
    c=catalog();injective_mapping(c.document,MAPPING)
    selected=[deepcopy(d) for d in c.document['declarations'] if d['name'] in MAPPING]
    require(_references(selected)<=set(MAPPING),'Analysis projection has external dependencies')
    doc=injective_mapping(dict(schema_version='0.16',lexicon_version='0.16',declarations=selected,statements=[]),MAPPING)
    doc['declarations']+=previous.additional_definitions()
    doc=normalize_document(doc);parent=ProductsVocabulary()
    for d in doc['declarations']:
        if d['name'] in parent._words:require(d==parent._plain_declaration(d['name']),'Previous mathematics changed')
    return doc


@lru_cache(maxsize=1)
def basis():
    result=deepcopy(previous.basis());parent=ProductsVocabulary()
    for d in composed()['declarations']:
        name=d['name']
        if name in parent._words:continue
        result['definitions'][name]=MEANINGS[name]
        result['public_contracts'][name]=dict(arguments=[dict(role=n,sort=p['sort']) for n,p in zip(ROLES[name],d['parameters'],strict=True)],
            result=d['result'],interpretation_inputs=['有理数は標準の正確な算術で解釈し、cutvalidを満たす性質を実数値とする。','関数と定義域を明示し、全ての精度・近傍・入力・有限分割への量化を保持する。'])
    result.update(status='shared_preserved_cut_analysis',document=LIBRARY,
        preserved_sources=[dict(document=previous.previous.SELECTED,basis=previous.previous.SELECTED_BASIS,renaming=MAPPING)],limitations=LIMITS)
    return result


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
        require(renamed(entry['declaration'],MAPPING)==d,'Analysis source payload changed')
        rows.append(dict(source_symbol=old,shared_word=new,source_basis=entry['meaning_basis'],source_meaning=entry['meaning_ja'],
            shared_meaning=MEANINGS[new],source_declaration_sha256=digest(encoded(entry['declaration'])),
            shared_declaration_sha256=digest(encoded(d)),direct_dependencies=sorted(direct[old]),
            statement_indices=[i for i,names in enumerate(uses) if old in names],judgment='injective_renaming_of_typed_definition_with_explicit_domain_and_quantifier_contract'))
    return dict(schema='noema-public-word-correspondence-1',work='einstein-1905',document=previous.previous.SELECTED,
        document_sha256=digest((ROOT/previous.previous.SELECTED).read_bytes()),library=LIBRARY,rows=rows,
        previous_correspondence=previous.BRIDGE,combined_mapping=MAPPING,reviewer='assistant',
        original_manuscript_modified=False,old_reviews_rebound=False,quotation_names_merged=False,full_manuscript_mapping_complete=False)


def prepare():
    write_new(LIBRARY,format_graph(composed())+'\n');write_new(BASIS,basis());write_new(BRIDGE,correspondence())
