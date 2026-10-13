"""Bind hypothetical calibration outcomes to the same pair, frame and event."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT

PARENT='examples/v014/einstein-inverse-methods.noema'
PROFILE='h[a a b d] c'
READING='h[a a a a a a '+CUT+' d] c'
PAIR='h[a a a a a d] c'
EQUAL='h[a a a a d] c'
REST='h[a a d] c'


def definitions():
    text=definition('sbv2','leftkind a rightkind a leftscale b rightscale b left '+CUT+' right '+CUT,
        both(op('e',v('leftkind'),v('rightkind')),k('aa','n p a b',v('leftscale')),k('aa','n p a b',v('rightscale')),
            k('ba',v('left')),k('ba',v('right')),k('sca',k('bj',v('leftscale'),v('left')),k('bj',v('rightscale'),v('right')))))
    args='record a target a kind a frame a event a unit a scale b value '+CUT+' context d profile '+PROFILE+' reading '+READING
    text+=definition('sbw2',args,both(k('aa','n p a b',v('scale')),k('ba',v('value')),
        app(v('profile'),v('unit'),v('kind'),v('scale'),v('context')),
        app(v('reading'),*(v(n) for n in ('record','target','kind','frame','event','unit','value','context')))))
    args='trial a first a second a frame a event a context d paired '+PAIR+' equalamount '+EQUAL+' atrest '+REST
    text+=definition('sbx2',args,both(op('u',op('e',v('first'),v('second'))),
        app(v('paired'),*(v(n) for n in ('trial','first','second','frame','event','context'))),
        app(v('equalamount'),*(v(n) for n in ('first','second','frame','event','context'))),
        app(v('atrest'),v('first'),v('frame'),v('context'))))
    return text


MEANINGS={
    'sbv2':'同じ種類の二つの実数値を、正の有理単位尺度で共通の基準へ換算して比較する。数値だけの一致を量の一致とはしない。既存の量・単位ライブラリの乗法的な換算を、この文書の実数等値scaへ接続する。',
    'sbw2':'一つの記録・対象・量の種類・系・出来事・単位・値・文脈を同じ測定結果関係へ結ぶ。単位の種類と正の尺度を検査する。実測か仮定上の指定かは文脈の解釈に従い、観測済みとは自動認定しない。',
    'sbx2':'異なる二対象を同じ試行・系・出来事・文脈へ結び、同じ量であることと第一対象が静止することを要求する。第二対象の静止を原文にない条件として追加しない。',
    'sby2':'同じ仮定上の二つの電気量の比較で、距離の結果が1 cm、第一対象から第二対象への力の結果が1 Dynとなる校正条件。距離と力は同じ試行を対象にし、量の種類・単位・記録を区別する。',
    'sbz2':'同じ第一対象について、静止系・同じ出来事・文脈で電気量の値を指定単位で1とする結果条件。',
    'sca2':'sby2の作用による校正とsbz2の電気量1を、本文の同じ仮定として採用する内容。任意の現実の測定で完全な値が観測済みだとは主張しない。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()
    text+='r zof[a a b d] c.r zog[a a a a a a '+CUT+' d] c.r zoh[a a a a a d] c.r zoi[a a a a d] c.r zok[a d] c.'
    text+=''.join('r '+n+'[] a.' for n in ('zol','zom','zon','zoo','zop','zoq','zor','zos','zot','zou','zov','zow','zox','zoy'))
    frame=k('ra');ctx=v('context');one=k('bb','n p b b')
    reading=lambda record,target,kind,unit:k('sbw2',k(record),k(target),k(kind),frame,k('zoo'),k(unit),'n p b b',one,ctx,'p zof','p zog')
    calibration=both(k('va',frame),k('zok',k('zol'),ctx),
        k('sbx2',k('zon'),k('zol'),k('zom'),frame,k('zoo'),ctx,'p zoh','p zoi','p xm'),
        op('u',op('e',k('zop'),k('zoq'))),reading('zov','zon','zop','zos'),reading('zow','zon','zoq','zot'))
    text+=definition('sby2','','b context['+calibration+']','e')
    text+=definition('sbz2','','b context['+both(op('u',op('e',k('zor'),k('zop'))),op('u',op('e',k('zor'),k('zoq'))),reading('zox','zol','zor','zou'))+']','e')
    text+=definition('sca2','','b context['+both(op('t',k('sby2'),ctx),op('t',k('sbz2'),ctx))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k ug[k zoy[] k rd[] r[k sca2[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-inverse-methods-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-charge-calibration-basis-v1',document='examples/v014/einstein-charge-calibration.noema')
    meanings={
        'zof':(['unit','kind','scale','context'],'単位の量の種類と基準への正の有理尺度を、同じ文脈で指定する関係。物理的な単位の実現や次元の導出とは別の意味規約。'),
        'zog':(['record','target','kind','frame','event','unit','value','context'],'同じ対象・量の種類・系・出来事・単位・文脈に値を結ぶ結果記録。今回は仮定された結果に使用し、実測済みの標識ではない。'),
        'zoh':(['trial','first','second','frame','event','context'],'第一対象から第二対象への作用と両者の距離を比較する同じ試行の割当。逆方向や別の出来事を同一試行に混ぜない。'),
        'zoi':(['first','second','frame','event','context'],'二対象の電気量が同じであるという比較条件。二対象が同じ物体であるという意味ではない。電気量の一般的な同定の説明は未完。'),
        'zok':(['body','context'],'本文で点状の電気量として理想化して扱う対象であること。点状理想化と電気量の基礎説明は未完。'),
        'zol':([], '本文で仮定する第一の電気量の対象。'),'zom':([], '校正で比較する同じ大きさの第二の電気量の対象。'),
        'zon':([], '二対象の距離と作用を同じ条件で指定する仮定上の校正試行。'),'zoo':([], '同じ校正結果を指定する出来事。日時の数値は補わない。'),
        'zop':([], '対象間の距離という量の種類。'),'zoq':([], '第一対象から第二対象への力の大きさという量の種類。力の一般的な基礎説明は未完。'),
        'zor':([], '電気量の量の種類。'),'zos':([], '本文の長さ単位cm。校正の長さの基準尺度を1とする。'),
        'zot':([], '本文の力の単位Dyn。校正の力の基準尺度を1とする。質量・長さ・時間による実現との接続は未完。'),
        'zou':([], 'この作用条件によって値1を指定する電気量の単位。固有名を知るだけで意味を完成したとは扱わない。'),
        'zov':([], '同じ試行についての距離の結果記録。'),'zow':([], '同じ試行についての力の結果記録。'),'zox':([], '第一対象の電気量の値1の結果記録。'),
        'zoy':([], 'u0173冒頭で電気量とその作用を仮定して説明する箇所。'),
    }
    for name,(args,meaning) in meanings.items():
        d=next(d for d in doc['declarations'] if d['name']==name);basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0173の静止系での値1と、同じ電気量へ距離1 cmで力1 Dynを及ぼす条件を仮定として部分記述した。現実の試行の実行や測定済みを主張しない。',
        '点状理想化、電気量、力、同じ電気量という比較の一般的な説明、Dynの質量・長さ・時間による実現は未完。固有名や単位記号だけで説明済みには数えない。',
        '結果記録の単位の種類と正の尺度は結ぶが、既存の次元ライブラリ全体と物理的な測定手順の構成を結び終えたものではない。原点をずらす換算や対数量は扱わない。',
        '校正条件と電気量1を同じ仮定で結んだ。ある一つの指定試行の実行が、単位の一般定義の必要十分条件になるという強い主張は追加しない。',
        '移動系でも同じ電気量1になるという次の主張、静止条件付きの力ベクトルとの同定、二つの言い表しと全文の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed={'sbv2','sbw2','sbx2'}
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='charge-calibration-basis-v1',document='examples/v014/charge-calibration.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],definitions={n:m for n,m in basis['definitions'].items() if n in needed},
        unresolved=['単位の種類・尺度と、同じ試行に結ぶ結果の条件。実際の測定、物理的な力や電気量の一般定義は別に与える。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'charge-calibration'),(composed,'einstein-charge-calibration')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored calibration differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Unit values and paired calibration outcomes composed')


if __name__=='__main__':main()
