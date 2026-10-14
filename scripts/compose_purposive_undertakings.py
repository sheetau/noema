"""Bind undertaking purposes to the same acts and describe tiered oversight."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_mutual_undertakings import ACT,FORM,SOURCE as FORM_SOURCE

PARENT='examples/v014/kant-fixed-standards.noema'
AIMS='h[a a i[e] d] c'
PURPOSE=[('goal','i[e]'),('aims',AIMS)]
PURPOSIVE=FORM+[('proponents','h[a d] c')]+PURPOSE
SOURCE=FORM_SOURCE+[('proponents','h[a d] c'),('goal','i[e]')]
CONTENT=[(n,t) for n,t in SOURCE if n!='context']+[('candidates','h[d d] c'),('authorities','h[a] c'),('confirms','h[a a d] c')]
TIER=[('controller','a'),('members','h[a] c'),('subjects','h[a] c'),('scene','d'),('controls','h[a a d] c')]
ENDURING=[('controller','a'),('members','h[a d] c'),('subjects','h[a d] c'),('histories','h[d] h[d] c'),
    ('scopes','h[d] h[d] c'),('orders','h[d] h[d d] c'),('controls','h[a a d] c')]
TIER_SOURCE=[(n,t) for n,t in ENDURING if n not in ('orders','controls')]
ROOTS=['rh6','rh7','ria','rib']


def definitions():
    text=definition('rh6',params(ACT+PURPOSE),both(k('rhx',*args(ACT)),app(v('aims'),v('person'),v('act'),v('goal'),v('scene'))))
    proponents=lambda person:app(v('proponents'),v(person),v('context'))
    subset=quant('f','person','a',op('y',proponents('person'),app(v('parties'),v('person'),v('context'))))
    adapted='i[person a act a agreement a terms '+dict(FORM)['terms']+' bindings j[a] scene d]['+both(
        app(v('declares'),*(v(n) for n in ('person','act','agreement','terms','bindings','scene'))),
        op('y',proponents('person'),app(v('aims'),v('person'),v('act'),v('goal'),v('scene'))))+']'
    text+=definition('rh7',params(PURPOSIVE),both(quant('g','person','a',proponents('person')),subset,k('rhz',*args(FORM,declares=adapted))))
    member=lambda n:app(v('members'),v(n))
    subject=lambda n:app(v('subjects'),v(n))
    directs=lambda a,b:app(v('controls'),v(a),v(b),v('scene'))
    upper=quant('f','member','a',op('y',member('member'),both(op('u',op('e',v('controller'),v('member'))),directs('controller','member'))))
    lower=quant('f','subject','a',op('y',subject('subject'),quant('g','member','a',both(member('member'),
        op('u',op('e',v('member'),v('subject'))),directs('member','subject')))))
    text+=definition('ria',params(TIER),both(quant('g','member','a',member('member')),quant('g','subject','a',subject('subject')),upper,lower))
    history=app(v('histories'),v('context'));scope=app(v('scopes'),v('context'));before=app(v('orders'),v('context'))
    fixed=lambda name:'i[person a]['+app(v(name),v('person'),v('context'))+']'
    tier=k('ria',*args(TIER,members=fixed('members'),subjects=fixed('subjects')))
    future=op('x',op('e',v('scene'),v('context')),app(before,v('context'),v('scene')))
    body=both(k('tb',history,scope,before),app(scope,v('context')),
        quant('f','scene','d',op('y',app(scope,v('scene')),both(future,tier))))
    text+=definition('rib',params(ENDURING),'b context['+body+']','e')
    return text


MEANINGS={
    'rh6':'rhxと同じ本人・表明行為・時点に、指定した閉じた目的内容への志向を結び付ける。目的内容の真理、実現可能性、成功は要求しない。',
    'rh7':'相互引受けrhzの当事者に含まれる非空の目的主体範囲を基準文脈で固定し、その各人について引受けと目的志向が同じ行為・時点で成立するよう表明関係を制限する。他の当事者に同じ目的を補わない。',
    'ria':'非空の構成員範囲の全員を同じ統括主体が監督し、非空の対象者範囲の各人に対してその構成員の誰かが監督する。各段の主体と対象は異なる。担当を分担でき、全構成員が全対象を監督することや監督関係の推移性は要求しない。',
    'rib':'評価文脈で固定した統括主体・構成員範囲・対象者範囲について、基準時を含む非空で間の抜けない将来区間の全状況でriaが成立する内容。担当構成員の交代を許す。履歴・区間・順序は同じ基準文脈で選ぶ。',
}
LIMITS=[
    '目的志向の関係は既存hzuと同じ意味規約による。動機の認知過程・組織の共同意図を構成し終えたものではない。rh7は目的を持つ当事者を明示し、集団の全員が同じ目的を持つと自動推定しない。',
    '表明と目的の結合には同じ行為と時点を要求する。先に別の目的を述べただけの行為、別の当事者による目的、現在の目的を過去の表明へ無条件に移すことを認めない。',
    'riaの二段階は明示した監督関係の構造である。上位者の意図が下位者を因果的に動かす仕組み、委任や命令の伝達、監督の正当性、全権限を説明したものではない。直接関係の推移律を追加しない。',
    '統括主体には組織を指定できるが、組織が主体として行為・監督を担う制度の基礎説明は残る。各段の自分自身への監督は除くが、階層全体が非循環であることはこの二段だけでは保証しない。',
    'ribは同じ基準文脈で選んだ人々についての持続。将来の新構成員や対象者まで含める読みとは区別する。未来に人員範囲が変わる場合の選択規約は別に指定する必要がある。',
    '選んだ有限期間・履歴での持続を無限時間や変更不能性へ昇格させない。後見の歴史的な意味、unaufhörlichやverewigenの強さをこの範囲に確定しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    before='i[first d second d]['+k('ic',v('first'),v('second'),v('context'))+']'
    extra=definitions()+definition('hzck',params(SOURCE),k('rh7',*args(PURPOSIVE,eligible='p aa',before=before,occurs='p dg',performs='p f3',aims='p hzu')))
    consequent=op('t',k('hzcf',v('agreement'),v('candidates'),v('authorities'),v('confirms')),v('context'))
    extra+=definition('hzcl',params(CONTENT),'b context['+op('y',k('hzck',*args(SOURCE)),consequent)+']','e')
    orders='i[anchor d][i[first d second d]['+k('ic',v('first'),v('second'),v('anchor'))+']]'
    extra+=definition('hzcm',params(TIER_SOURCE),k('rib',*args(ENDURING,orders=orders,controls='p dc')),'e')
    doc=parse(format_graph(doc,'compact')+extra);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-fixed-standards-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-purposive-undertakings-basis-v1',document='examples/v014/kant-purposive-undertakings.noema')
    basis['definitions'].update(MEANINGS|{
        'hzck':'既存の人aa・行為の生起dg・行為者f3・時間順序ic・目的志向hzuをrh7へ接続する。目的主体と目的記述を明示し、形成も成功も無条件には主張しない。',
        'hzcl':'指定目的を持つ引受けhzckが成立するなら、同じ合意への無効性と仮定上の承認への判断hzcfが成立するという内容。原文の目的を持つ契約を全て選び終えた量化や著者帰属は未接続。',
        'hzcm':'ribの監督を既存dc、時間順序を同じ評価文脈のicへ結ぶ。閉じた適用式をhzckの目的記述として渡せる。目的の真理は引受けの成立条件と分離する。'})
    basis['unresolved']+=LIMITS+['u0013の目的への接続と、構成員を介する二段の監督への部分的な解釈注記。宣誓、制度・宗教・人々の範囲、因果的な媒介、永久性、後見を永続化する目的、問いと著者の否定判断の帰属は未完。']
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'purposive-undertakings')
def core_composed():return projected(ROOTS+['hzck','hzcl','hzcm'],'purposive-undertakings-core')
BUILDERS=((generic_composed,'purposive-undertakings'),(source_composed,'kant-purposive-undertakings'),(core_composed,'purposive-undertakings-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored purposive undertaking differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
