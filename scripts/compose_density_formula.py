"""Isolate the five M0390 equalities from stronger field-system premises."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_boost import FLOW,CUT
from scripts.compose_field_equations import FIELD,REGION,POINT,JET,ROLES

PARENT='examples/v014/einstein-charge-normalization.noema'
RATIONAL=FLOW+' newexx neweyy newezz'
FORMULA=[(n,CUT) for n in FLOW.split()]+[('newelectricjet',JET)]
PARTIALS=FORMULA+[('newfield',FIELD),('region',REGION),('point',POINT)]
ROOTS=['senr','sens','sent']
MEANINGS={
    'senr':'M0390の三速度の関係と密度の変換をsempで表し、同じ新密度を新しい電場の三空間対角微分値の和へ結ぶ。型付き有理数の比較形。場の六式、磁気側、旧場の微分値は前提に含めない。',
    'sens':'M0390の三速度と密度の変換semt、および新密度が新電場の発散semdに等しいことを、有効な実切断で結ぶ。新しい二つの密度値を導入せず、五つの等式で同じ値を共有する。',
    'sent':'sensの三空間対角微分値を、指定した同じ新電場・領域・地点・対応する各軸の偏微分s5tへ結ぶ。三つの必要な偏微分だけを要求し、磁場や時間・対角外の微分の存在を追加しない。',
}
LIMITS=[
    'V>0、基準系の速度|v|<V、正のbetaの正規化、およびD=V²−v*ux≠0を引き継ぐ。分数が未定義となる入力を分母を払った式だけで通さない。原文の式にない流速の大きさ制限やD>0は追加しない。',
    'ここで新たに記述するのはM0390の五つの等式の条件である。原文のwobeiによる導入、どの量・基準系・出来事を指すか、著者の定義・主張への帰属は、型付き関数の作成だけで完成とはしない。',
    'sentは新側の三つの偏微分を同じ場と点へ結ぶ。旧側の速度・密度の参照先と新旧の基準系・出来事の全ての接続は、この定義の引数だけでは完了しない。',
    '式を過不足なく記述できるかと、その物理的な命題が真であるかを区別する。原著者の主張を記述するために、新たな物理法則の証明を翻訳の必要条件にはしない。一方、演算子の意味や参照先の未説明は意味確認の課題として残す。',
    '単位・電荷・基準系の物理的な意味、全実数上の偏微分の一般理論、原文文脈への参照、全文の意味一致は未完。既存の強い場の条件semx/semy等を削除せず、式だけの条件を別に設ける。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-charge-normalization-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definition('senr',params([(n,'b') for n in RATIONAL.split()]),both(k('semp',*map(v,FLOW.split())),
        op('e',v('newdensity'),k('ab',k('ab',v('newexx'),v('neweyy')),v('newezz')))))
    text+=definition('sens',params(FORMULA),both(k('semt',*map(v,FLOW.split())),k('semd',v('newelectricjet'),v('newdensity'))))
    partials=[k('s5t',app(v('newfield'),k(axis)),v('region'),v('point'),k(axis),app(v('newelectricjet'),k(axis),k(axis))) for axis in ROLES[:3]]
    text+=definition('sent',params(PARTIALS),both(k('sens',*args(FORMULA)),*partials))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='einstein-density-formula-basis-v1',document='examples/v014/einstein-density-formula.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS+[
        'u0236/M0390の意味確認に向け、式だけの条件と必要な三微分への接続を分ける。新しい著者主張・原始概念・原文範囲は追加しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(['senr'],'density-formula')
def core_composed():return projected(ROOTS,'density-formula-core')
BUILDERS=((generic_composed,'density-formula'),(source_composed,'einstein-density-formula'),(core_composed,'density-formula-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored density formula differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
