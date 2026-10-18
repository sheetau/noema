"""Apply one closed dissemination frame to focused subgroup descriptions."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT, closure
from scripts.compose_thinking_disseminators import call as k, apply, conjunction as both
from scripts.compose_described_dissemination import FIELDS, BINDINGS, declaration
from scripts import compose_scalar_backgrounds as scalar

PARENT = 'examples/v016/kant-subgroup-dissemination.noema'
PARENT_BASIS = 'data/subgroup-dissemination-basis-v1.json'
FULL = 'examples/v016/kant-focused-dissemination.noema'
CORE = 'examples/v016/focused-dissemination-core.noema'
LIBRARY = 'examples/v016/focused-subgroups.noema'
BASIS = 'data/focused-dissemination-basis-v1.json'
PREDICATE = 'i[h[a d] c]'
FRAME = 'i b[h[' + PREDICATE + '] e]'
BASE = [(n,t) for n,t in FIELDS if n not in ('governed','appoints','guardianrole')]
DESCRIBED = [(n,t if n=='state' else 'i['+t+']') for n,t in BASE]
MEANINGS = {
 'rqtj':'順序付き履歴の基準点より後の全機会で同じ条件を要求する。基準点は履歴に属し、将来機会は非空でなければならない。基準点自身での条件成立は要求しない。',
 'hzoy':'hzovの母集団、各人の独立判断・自己離脱・相対範囲への伝播、全将来機会を保持し、部分集団の条件だけを引数にする内容。各点の母集団が人の範囲であること、全体に複数の該当者がおり、その中に部分集団の該当者がいることを要求する。',
 'hzoz':'同じ30引数から部分集団の閉じた述語記述を受け取る枠を作る。受け取った述語を評価してhzoyへ渡す。内容の構成時に記述を評価するのではなく、構成された枠が適用される段階で評価する。',
 'hzp2':'共通の30引数の閉じた記述から、hzozの階数1の枠記述を構成する。性向記述は記述値として持ち上げ、その内容をこの段階では実行しない。',
 'rqtk':'同じ閉じた階数1の枠へ一つの部分集団述語記述を値として適用し、閉じた内容記述を構成する。部分集団の述語や内容を構成時には実行しない。',
 'rqtl':'部分集団述語記述の列の全要素へ同じ枠を適用する。順序と重複を保ち、比較対象ごとに母集団・行為者・経路・将来範囲を変えない。',
 'rqtm':'焦点と比較対象の部分集団述語を同じ枠へ適用し、主張内容と尺度条件だけの背景をrtgで組にする。背景に比較対象の実際の成立は要求しない。視点・尺度の基準文脈・比較関係は明示した閉じた記述で渡す。',
}
LIMITS = [
 '比較対象ごとに変えるのは部分集団述語の閉じた記述だけである。共通の内容の定義はhzooを再利用し、自己思考や伝播を別の不透明な基本述語へ置き換えない。',
 '後見役の焦点は既存hzhbの閉じた述語として渡せる。比較対象を非後見役に限定せず、どの比較範囲を選ぶかは明示する必要がある。',
 'rqtmは尺度だけの背景を採る候補である。部分集団外にも該当者が実在するという追加条件を自動では加えない。sogarの全用法や唯一の読みを実装したとはしない。',
 '尺度の向きは指定された関係の意味規約による。確率・予想外の程度・注目すべき程度などを自動補完しない。尺度・視点・比較対象が原文に適切かは未確定。',
 '全将来内容同士を比較する明示した作用範囲である。各将来点の内部で背景を評価する読みや、自由の仮定、Denn、比喩、著者への実際の帰属は未完。',
 '既存32文と七単位の確認を保持する。新たな著者主張・対応範囲・意味確認済み単位は加算しない。',
]


def definitions():
    future = both(apply('history','v point'),apply('before','v base','v point'))
    text = declaration('rqtj',[('history','h[d] c'),('before','h[d d] c'),('base','d'),('condition','h[d] c')],'c',
        both(k('rqtb','v history','v before','v base'),
             'f point d[y['+future+']['+apply('condition','v point')+']]'))
    human = 'f person a[y['+apply('members','v person','v opportunity')+']['+k('aa','v person')+']]'
    qualified = 'i[person a candidatepoint d]['+k('hzoo','v person','v candidatepoint',*('v '+n for n,t in BINDINGS))+']'
    atpoint = both(human,k('rqti','v opportunity','v members','v subgroup',qualified))
    text += declaration('hzoy',BASE+[('subgroup','h[a d] c')],'e',
        'b base['+k('rqtj','v history','v before','v base','i[opportunity d]['+atpoint+']')+']')
    text += declaration('hzoz',BASE,'h['+PREDICATE+'] e',
        'i[subgroup '+PREDICATE+']['+k('hzoy',*('v '+n for n,t in BASE),'s[v subgroup]')+']')
    args=['o r[v state]' if n=='state' else 'v '+n for n,t in BASE]
    text += declaration('hzp2',DESCRIBED,FRAME,'o a[r b[p hzoz]]['+' '.join(args)+']')
    text += declaration('rqtk',[('frame',FRAME),('subgroup',PREDICATE)],scalar.PC,'o a[v frame][o r[v subgroup]]')
    mapped='q[v subgroups][l['+scalar.PC+'][]][i[items j['+scalar.PC+'] subgroup '+PREDICATE+'][m[v items][l['+scalar.PC+']['+k('rqtk','v frame','v subgroup')+']]]]'
    text += declaration('rqtl',[('frame',FRAME),('subgroups','j['+PREDICATE+']')],'j['+scalar.PC+']',mapped)
    fields=[('frame',FRAME),('focus',PREDICATE),('alternatives','j['+PREDICATE+']')]+scalar.INPUTS[2:]
    text += declaration('rqtm',fields,scalar.PAIR,k('rtg',
        'o r['+k('rqtk','v frame','v focus')+']',k('rtk',k('rqtl','v frame','v alternatives')),
        'v observer','v anchor','v ranking'))
    return text


def imported():
    source=parse((ROOT/scalar.LIBRARY).read_text(encoding='utf-8'))
    return closure(source,['rtg','rtk','rsx','rsy','rsw','rsz'])


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    imports=imported();added={d['name'] for d in imports}|set(MEANINGS)
    assert not added & set(old.entries)
    meanings=json.loads((ROOT/scalar.BASIS).read_text(encoding='utf-8'))['definitions']
    meanings={d['name']:meanings[d['name']] for d in imports}|MEANINGS
    size=len(doc['declarations']);statements=doc['statements'];doc['statements']=[]
    doc['declarations']+=imports
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['rqtm','hzp2','rsx','rsy','rsw','rsz','hzny','rqsx','hzow'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqtm','rsx','rsy','rsw','rsz'])
    basis=dict(status='shared_dissemination_frame_with_separate_scalar_background',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=meanings,
        imported_definitions_from=scalar.BASIS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Shared future dissemination frame and separate scalar background constructed',flush=True)


if __name__=='__main__':main()
