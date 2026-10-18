"""Give the source comparison an explicit qualitative expectation reading."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_thinking_disseminators import call as k,conjunction as both
from scripts.compose_described_dissemination import declaration
from scripts.compose_focused_dissemination import PREDICATE,FRAME
from scripts import compose_scalar_backgrounds as scalar

PARENT='examples/v016/kant-existential-focus.noema'
PARENT_BASIS='data/existential-focus-basis-v1.json'
FULL='examples/v016/kant-expected-focus.noema'
CORE='examples/v016/expected-focus-core.noema'
LIBRARY='examples/v016/qualitative-expectation.noema'
BASIS='data/expected-focus-basis-v1.json'
READING='data/expected-focus-reading-v1.json'
PC=scalar.PC
WEAK=scalar.ORDER
PRIMITIVE_MEANING='指定した視点からこの文脈で採る見込み評価において、第一の内容記述が第二の内容記述と少なくとも同程度に見込まれる。数値確率や実際の真理ではなく、提示された期待の比較である。二方向とも成立すれば同順位、二方向とも不成立と確認されていれば比較不能であり、情報が未知であることとは区別する。伝記的な著者の内心を自動推定しない。'
MEANINGS={
 'rqtq':'指定する内容記述の有限列上で、同じ視点・文脈の弱い比較が反射的かつ推移的であることを検査する。全比較可能性を要求せず、同順位と比較不能を区別する。列の重複を保存するが重みとして数えない。',
 'rqtr':'同じ視点・文脈について、第二の内容が第一以上に見込まれ、逆方向は成立しない場合に、第一を厳密に見込まれにくいものとする。同順位や比較不能を厳密な差へ変換しない。',
 'rqts':'焦点と比較候補を合わせた範囲の弱い比較をrqtqで検査し、その同じ比較からrqtrで作る厳密な向きをrtbへ渡す背景内容。焦点が全候補より見込まれにくいことを要求し、比較候補自体の現実の成立は要求しない。',
 'rqtt':'部分集団述語の閉じた記述から、同じ人物・同じ時点についての否定述語の閉じた記述を合成する。元の述語や世界の事実を構成時には実行しない。母集団は比較に共用する枠の側に保持する。',
 'hzpu':'hzptの文脈的な弱い見込み比較を、rqtrの厳密な見込まれにくさへ接続する。向きを逆にせず、明示した比較範囲での整合性は別にrqtsで確認する。',
 'hzpv':'同じ閉じた枠に、焦点の部分集団述語とその否定を適用する。hzptの期待比較とrqtsの整合性を背景とし、焦点の内容を主張側へ保持する。視点と比較文脈は閉じた記述で明示する。',
 'hzpw':'公衆の自己啓蒙の段落の採用読解として、hzpvの視点を著者waが提示する期待、比較文脈をhzp3に固定する。与えた焦点を後見役とする接続例では、その外側との比較になる。本文の真理や数値確率の断言ではない。',
}
LIMITS=[
 'カントの当該箇所には、著者が提示する期待尺度で後見役の該当を相対的に見込みにくいものとする読みを採用する。外側を比較候補とする二分法と、条件付きの全内容同士を比較する作用範囲は明示した解釈選択である。',
 'この期待尺度はsogarやevenの全用法の必要十分条件ではない。確率値、頻度、心理的驚きの実際の生起、比較候補にも該当者がいることは補わない。',
 'hzptは比較判断の意味規約であり、内容の真理や身体的・制度的事実から期待を自動計算する規則ではない。Noemaで期待そのものを記述するための関係で、自然言語の語句を検索して置換する対訳表ではない。',
 '比較不能は両方向の不成立が与えられている場合である。未知の比較は偽で埋めず、評価器へ渡す解釈でも未確定をエラーとして保持する。',
 '新しい合成は、既存の存在する経路・自由の条件を共用した枠に接続する。無制限の経路を評価可能な候補一覧へ縮めず、背景の検査を伝播内容全体の成立証明としない。',
 '既存34文と七単位の確認を保持する。尺度・視点・比較対象の採用読解を具体化するが、残る解釈値を充足した本文への全内容の帰属と、段落全体の意味確認は未完である。',
]


def definitions():
    compare=lambda a,b:'c[v weak][v observer v '+a+' v '+b+' v anchor]'
    reflexive=scalar.every('v contents','item',compare('item','item'))
    transitive=scalar.every('v contents','first',scalar.every('v contents','second',scalar.every('v contents','third',
        'y['+both(compare('first','second'),compare('second','third'))+']['+compare('first','third')+']')))
    text=declaration('rqtq',[('contents','j['+PC+']'),('observer','a'),('anchor','d'),('weak',WEAK)],'c',both(reflexive,transitive))
    fields=[('observer','a'),('left',PC),('right',PC),('anchor','d'),('weak',WEAK)]
    text+=declaration('rqtr',fields,'c',both(compare('right','left'),'u['+compare('left','right')+']'))
    full='m[l['+PC+'][v focus]][v alternatives]'
    strict='i[view a left '+PC+' right '+PC+' context d]['+k('rqtr','v view','v left','v right','v context','v ranking')+']'
    text+=declaration('rqts',scalar.BACKGROUND,'e','b point['+both(
        k('rqtq',full,'v observer','v anchor','v ranking'),
        k('rtb','v focus','v alternatives','v observer','v anchor',strict))+']')
    complement='r[i[property h[a d] c][i[person a point d][u[c[v property][v person v point]]]]]'
    text+=declaration('rqtt',[('predicate',PREDICATE)],PREDICATE,'o a['+complement+'][v predicate]')
    text+=declaration('hzpu',fields[:-1],'c',k('rqtr',*('v '+n for n,t in fields[:-1]),'p hzpt'))
    fields=[('frame',FRAME),('focus',PREDICATE),('observer','i[a]'),('anchor','i[d]')]
    foreground='o r['+k('rqtk','v frame','v focus')+']'
    alternatives=k('rtk',k('rqtl','v frame','l['+PREDICATE+']['+k('rqtt','v focus')+']'))
    text+=declaration('hzpv',fields,scalar.PAIR,k('rtf','r c[p rqts]',foreground,alternatives,'v observer','v anchor','r[p hzpt]'))
    text+=declaration('hzpw',fields[:2],scalar.PAIR,k('hzpv','v frame','v focus','r[k wa[]]','r[k hzp3[]]'))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not (set(MEANINGS)|{'hzpt'})&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='r hzpt[a '+PC+' '+PC+' d] c.'
    doc=parse(format_graph(doc,'compact')+text+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[]
    core['declarations']=closure(doc,['hzpw','hzpr','hzps','rqtp','rsx','rsy','rsw','hzny','rqsx','hzhb','hzpu'])
    library=deepcopy(doc);library['statements']=[]
    library['declarations']=closure(doc,['rqts','rqtt','hzpv','rsx','rsy','rsw','hzpu'])
    primitive=next(d for d in doc['declarations'][size:] if d['kind']=='primitive')
    basis=dict(status='adopted_qualitative_expectation_scale_for_guardian_focus',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={'hzpt':dict(parameters=primitive['parameters'],result=primitive['result'],
            arguments=['observer','left','right','context'],meaning_ja=PRIMITIVE_MEANING)},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        reading_manifest=READING,limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Qualitative expectedness reading attached to shared comparison frames',flush=True)


if __name__=='__main__':main()
