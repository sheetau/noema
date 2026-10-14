"""Distinguish continuing roles, endpoint-free histories and numeric horizons."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app
from scripts.compose_situated_criticism import params,args
from scripts.compose_purposive_undertakings import TIER

PARENT='examples/v014/kant-purposive-undertakings.noema'
POINT=[('controller','a'),('members','h[a d] c'),('subjects','h[a d] c'),('scene','d'),('controls','h[a a d] c')]
TAIL=[(n,t) for n,t in POINT if n!='scene']+[('history','h[d] c'),('before','h[d d] c'),('anchor','d')]
NUMERIC=TAIL+[('beyond','h[b d] c')]
SOURCE=[('controller','a'),('members','h[a d] c'),('subjects','h[a d] c'),('histories','h[d] h[d] c')]
SCALED=SOURCE+[('horizons','h[d] h[b d] c')]
ROOTS=['ric','rid','rie','rif']


def definitions():
    at=lambda name:'i[person a]['+app(v(name),v('person'),v('scene'))+']'
    text=definition('ric',params(POINT),k('ria',*args(TIER,members=at('members'),subjects=at('subjects'))))
    state='i[scene d]['+k('ric',*args(POINT))+']'
    for name,parent,fields in (('rid','rca',TAIL),('rie','rcb',TAIL),('rif','rcc',NUMERIC)):
        inputs=[v('history'),v('before'),v('anchor'),state]
        if name=='rif':inputs.append(v('beyond'))
        text+=definition(name,params(fields),k(parent,*inputs))
    return text


MEANINGS={
    'ric':'各評価時点の構成員と対象者の範囲を使ってriaの二段階の監督を記述する。集団の識別は保つが、同じ個人が全期間に存在することや、基準時の構成員を将来まで保持することは要求しない。',
    'rid':'同じ履歴と厳密な全順序の基準時以降の全状況でricが成立する。構成員・対象者・担当者の交代を許す。選んだ一部分の期間の成功とは異なるが、履歴に終点があっても成立できる。',
    'rie':'ridの持続に加えて、同じ履歴の基準時以降の各状況より後にさらに状況がある。順序上の終点がないことを要求し、未知の終期や有限の観測列を終点の不在として扱わない。',
    'rif':'rieの持続に加え、同じ基準時の時間尺度についてどんな有理数の限界も超える状況が同じ将来履歴にある。beyondは正当な時間座標との比較という意味規約を要し、任意の真偽関数を物理的な尺度と扱わない。',
}
LIMITS=[
    '各状況の構成員・対象者はそれぞれ非空で、その状況の同じ二段階の監督を満たす。誰もいない期間を、組織が持続した期間へ空虚に数えない。',
    '旧ribの基準時に固定した人々への持続と、新ridの各時点の人々への持続を併存させる。将来の構成員の範囲、組織の同一性と承継、当事者が将来世代を拘束できるかは別の意味条件である。',
    '終点のない順序でも数値的には有限長の場合がある。rieだけで数値的な無限時間を表したとせず、その強い条件にはrifを使う。',
    'rifの時間座標、原点・単位、比較と時間順序の整合、実数の切断としての妥当性は呼出側の意味規約に残る。全有理数への量化を有限の限界値で代用しない。',
    '有限解釈器が全状況を有限集合と解釈した場合、rieは偽になる。これはそのモデルの性質であり、目的の記述不能、現実の不可能性、一般の無限モデルでの偽を示さない。',
    '内容を引用して目的にすることは、その内容の成立・実現能力・因果的な永続化を主張しない。後見の制度、宣誓、組織の共同意図、将来世代への拘束の正当性の説明は残る。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    extra=definitions();before='i[first d second d]['+k('ic',v('first'),v('second'),v('context'))+']'
    for name,target,fields in (('hzcn','rid',SOURCE),('hzco','rie',SOURCE),('hzcp','rif',SCALED)):
        bindings=dict(controls='p dc',history=app(v('histories'),v('context')),before=before,anchor=v('context'))
        if name=='hzcp':bindings['beyond']=app(v('horizons'),v('context'))
        extra+=definition(name,params(fields),'b context['+k(target,*args(NUMERIC if name=='hzcp' else TAIL,**bindings))+']','e')
    doc=parse(format_graph(doc,'compact')+extra);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-purposive-undertakings-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-continuing-institutions-basis-v1',document='examples/v014/kant-continuing-institutions.noema')
    basis['definitions'].update(MEANINGS|{
        'hzcn':'各時点の構成員・対象者へのridの持続を、同じ組織の既存監督dcと同じ評価文脈の時間順序icへ接続する内容。評価区間ではなく履歴の将来全体を使う。',
        'hzco':'hzcnと同じ人物範囲の時点依存と監督関係を保ち、終点のないrieの内容を作る。閉じた適用式をhzckの目的として引用でき、個々人の不死を加えない。',
        'hzcp':'同じ組織・各時点の人々・履歴・時間尺度に対するrifの内容。horizonsは同じ評価文脈で固定し、時点ごとに別の時間尺度へ切り替えない。'})
    basis['unresolved']+=LIMITS+['u0013のunaufhörlicheへの三つの時間的強さを分けた解釈注記。永続化する行為の因果・成功、verewigenの記述、著者への帰属と全文の意味一致は未完。語の一意の意味を無限時間だと確定しない。']
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'continuing-institutions')
def core_composed():return projected(ROOTS+['hzcn','hzco','hzcp','hzck','hzcl','hzcm'],'continuing-institutions-core')
BUILDERS=((generic_composed,'continuing-institutions'),(source_composed,'kant-continuing-institutions'),(core_composed,'continuing-institutions-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored continuing institution differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
