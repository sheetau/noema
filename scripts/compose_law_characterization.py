"""State scope-relative characterization by applicable relations in both directions."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-magnetic-curvature.noema'
SOURCE='examples/v014/einstein-law-characterization.noema'
LIBRARY='examples/v014/law-characterization.noema'
CORE='examples/v014/law-characterization-core.noema'
READING='data/law-characterization-reading-v1.json'
SCALAR='h['+CUT+'] '+CUT
RELATIONS=[('selected','h[a] c'),('scope','h[a d] c'),('bound','h[a a a d] c'),
    ('applicable','h[a a d] c'),('conditions','h[a a d] c'),('allowed','h[a a a a d] c')]
FIELDS=[('theory','a'),('subject','a'),('frame','a'),('context','d')]+RELATIONS
CASE=[('case','a'),('context','d')]+[RELATIONS[i] for i in (0,3,4)]
ROLES='light speed beta mass charge electricresponse magneticresponse drop magnetic radius lower upper'.split()
CATALOGUE=[('zrlrationode','setw','sets'),('zrnclaimnode','seuz','seur'),('zroradiusnode','sevn','sevh')]


def definitions():
    case,relation,context=v('case'),v('relation'),v('context')
    selected=app(v('selected'),relation);scope=app(v('scope'),case,context)
    applies=app(v('applicable'),relation,case,context);holds=app(v('conditions'),relation,case,context)
    accepted=k('sevp',*args(CASE));allowed=app(v('allowed'),v('theory'),v('subject'),v('frame'),case,context)
    text=definition('sevp',params(CASE),quant('f','relation','a',op('y',selected,op('y',applies,holds))))
    text+=definition('sevq',params(FIELDS),both(quant('g','relation','a',selected),quant('g','case','a',scope),
        quant('f','case','a',op('y',scope,app(v('bound'),case,v('subject'),v('frame'),context)))))
    text+=definition('sevr',params(FIELDS),quant('f','case','a',op('y',both(scope,allowed),accepted)))
    text+=definition('sevs',params(FIELDS),quant('f','case','a',op('y',both(scope,accepted),allowed)))
    text+=definition('sevt',params(FIELDS),both(k('sevq',*args(FIELDS)),k('sevr',*args(FIELDS)),k('sevs',*args(FIELDS))))
    text+=definition('sevu',params(FIELDS),quant('g','case','a',both(scope,accepted,op('u',allowed))))
    text+=definition('sevv',params(FIELDS),quant('g','case','a',both(scope,allowed,op('u',accepted))))
    text+=definition('sevw',params(FIELDS),quant('f','case','a',op('y',scope,quant('g','relation','a',both(selected,applies)))))
    return text


MEANINGS={
    'sevp':'一つの事例について、選択した全関係のうち適用されるものが全て成立する。適用されない関係はその事例を制約しない。全関係が不適用ならこの連言は真となる。',
    'sevq':'選択した関係と対象事例の範囲がともに非空で、範囲内の全事例が同じ対象・基準系・文脈へ結ばれている。対応の欠落を範囲の縮小で隠さない。',
    'sevr':'範囲内で理論が許す全事例が、適用される全関係を満たすという必要条件側の一致。式が余分な事例を許す可能性は残る。',
    'sevs':'範囲内で適用される全関係を満たす事例を、理論が全て許すという十分条件側の一致。理論が許す事例を式が排除する可能性は残る。',
    'sevt':'同じ非空の範囲・対象・系・理論についてsevrとsevsがともに成立し、事例の許容が過不足なく一致する。実際の運動や測定結果との一致を条件にしない。',
    'sevu':'式は許すが同じ理論は許さない、範囲内の反例が少なくとも一つある。',
    'sevv':'同じ理論は許すが式は排除する、範囲内の反例が少なくとも一つある。',
    'sevw':'範囲内の全事例に、選択した関係の少なくとも一つが適用されるという診断。過不足のない一致sevtとは別に検査する。',
    'sevx':'直前の三関係の提示箇所だけを選ぶ述語。偏向の比、電位降下の等号列、曲率半径の式を指す。',
    'sevy':'同じ事例と文脈の値から、選んだ三つの関係の数値条件を作る。電位降下については同じ場の向き付き積分も保持する。適用条件と理論の許容をこの式から補わない。',
    'sevz':'先行本文のsetw・seuz・sevnをこの順で引用した三項の一覧。引用だけでは式の内容を実行せず、必要な前提や全称化を追加しない。',
    'sewa':'同じ電子・系K・理論・評価範囲で三関係が許容事例を過不足なく表す、というu0275の部分解釈。三つの参照を互いに異なるものとして保持する。',
}
LIMITS=[
    'vollständiger Ausdruckを、明示した適用条件と評価範囲における許容事例の双方向一致として具体化する候補である。対象を全軌道・全物理条件へ設定することは妨げないが、その範囲の具体化と原文の読みの意味確認は残る。',
    '適用条件には各式の設定、初期静止、無放射、同じ場の積分、校正、磁場の向き等を適切に割り当てる必要がある。関係の値が真になる事例だけを適用範囲として選んではならない。範囲と理論の許容は独立した入力である。',
    'sevyは先行する三式のパラメーターを事例ごとに取り出す構成である。履歴・場・単位・出来事の帰属を含む先行本文の全前提を、この射影だけで復元したとはしない。引用一覧sevzと数値条件の参照関係を構造検査する。',
    '適用される関係がない事例は式側では制約されない。その事例を理論も許すなら過不足のない一致は成立しうる。適用範囲の網羅性sevwや各式の独立性を、完全な一致へ追加の必要条件として混入しない。',
    '有限モデルの全事例の検査は、無限の運動・軌道の集合を検証した証拠ではない。未知の適用条件・理論の許容・数値を推定せず、与えた有限範囲に対する結果として報告する。',
    '現行の有限評価器は論理枝の値を先に計算するため、数値射影の評価には不適用の枝も含む明示的な関数解釈が必要となる。未定義の物理量を零で補完する実装は追加しない。原文全体の意味一致と一般的な理論概念の基礎説明は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={'zrp'+n:('a','事例の'+n+'という量への役割参照。') for n in ROLES}
    values.update({'zrptheory':('a','u0275でいう本理論への参照。現実の真偽とは別に許容条件を指定する。'),
        'zrpnode':('a','u0275の三関係による完全な表現の主張箇所。'),'zrpdiscussion':('a','u0275の完全な表現についての議論の範囲。'),
        'zrpvalues':('h[a a d] '+CUT,'同じ事例・量の役割・文脈における明示された数値。単位・帰属の整合性は別に確認する。'),
        'zrpprofile':('h[a d] '+SCALAR,'同じ事例・文脈の電位降下を求める一次元の場。')})
    meanings={'scope':'結果を見て絞らない評価事例の範囲。全軌道を対象にする場合もこの入力で明示する。',
        'bound':'事例・対象・基準系・文脈の対応。','applicable':'関係・事例・文脈における適用条件。数値が合うかどうかとは別に定める。',
        'allowed':'理論・対象・基準系・事例・文脈における理論上の許容。実際の発生や観測を要求しない。'}
    for n,sort in RELATIONS:
        if n in meanings:values['zrp'+n]=(sort,meanings[n])
    extra=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    chosen=[op('e',v('relation'),k(n)) for n,_,_ in CATALOGUE]
    extra+=definition('sevx','relation a',op('x',chosen[0],op('x',chosen[1],chosen[2])))
    value=lambda n:app(k('zrpvalues'),v('case'),k('zrp'+n),v('context'))
    numbers=lambda names:[value(n) for n in names.split()]
    ratio=k('sets',*numbers('light speed electricresponse magneticresponse'))
    potential=both(k('seur',*numbers('light speed beta mass charge drop')),k('seus',*numbers('lower upper'),app(k('zrpprofile'),v('case'),v('context')),value('drop')))
    radius=k('sevh',*numbers('light speed beta mass charge magnetic radius'))
    branches=[both(test,condition) for test,condition in zip(chosen,(ratio,potential,radius))]
    extra+=definition('sevy','relation a case a context d',op('x',branches[0],op('x',branches[1],branches[2])))
    extra+=definition('sevz','','l[i[e]]['+' '.join('r['+k(n)+']' for _,n,_ in CATALOGUE)+']','j[i[e]]')
    fields=[k('zrptheory'),k('zramatter'),k('ra'),v('context'),'p sevx',k('zrpscope'),k('zrpbound'),k('zrpapplicable'),'p sevy',k('zrpallowed')]
    distinct=[op('u',op('e',k(CATALOGUE[i][0]),k(CATALOGUE[j][0]))) for i,j in ((0,1),(0,2),(1,2))]
    extra+=definition('sewa','','b context['+both(*distinct,k('sevt',*fields))+']','e')
    doc=parse(format_graph(doc,'compact')+extra)
    new='s[k uh[k zrpnode[] k rd[] r[k sewa[]] k zrpdiscussion[] k ri[]]].'
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+new)['statements']
    basis=json.loads((ROOT/'data/einstein-magnetic-curvature-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-law-characterization-basis-v1',document=SOURCE);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for n,(_,meaning) in values.items():
        d=lookup[n];basis['primitives'].append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-law-characterization-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:8],[]),(CORE,['sevz','sevu','sevv','sevw'],[len(old['statements'])])):
        selection=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selection.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selection,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
