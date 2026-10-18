"""Share existential dissemination and permission conditions across alternatives."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_thinking_disseminators import call as k
from scripts.compose_described_dissemination import declaration
from scripts.compose_existential_dissemination import FUTURE
from scripts.compose_focused_dissemination import PREDICATE,FRAME
from scripts.compose_conditional_dissemination import FIELDS

PARENT='examples/v016/kant-yoke-depiction.noema'
PARENT_BASIS='data/yoke-depiction-basis-v1.json'
FULL='examples/v016/kant-existential-focus.noema'
CORE='examples/v016/existential-focus-core.noema'
LIBRARY='examples/v016/conditional-subgroup-frames.noema'
BASIS='data/existential-focus-basis-v1.json'
FAMILY='h['+PREDICATE+' d] e'
DESCRIBED=[(n,t if n=='state' else 'i['+t+']') for n,t in FUTURE]
BRANCH_FIELDS=[(n,'h[d] '+t) for n,t in FUTURE]
CONDITION_FIELDS=FIELDS[:-1]+[('family',FAMILY)]
MEANINGS={
 'hzpq':'同じ22引数に、部分集団の閉じた述語記述だけを適用してhzpfの内容を作る。独立判断・共有する自己離脱・受け手ごとの存在する経路を共通に保ち、特定経路の供給関数を再導入しない。',
 'hzpr':'22引数の閉じた記述からhzpqの閉じた階数1の枠を作る。性向の記述は値として持ち上げる。この枠は既存rqtmで焦点と比較対象の双方へ共用できる。',
 'hzps':'候補場面ごとの22引数の供給関数から、部分集団記述と候補場面を受ける内容族を作る。同じ候補を全供給関数に渡してhzpfを構成する。内容族の自由引数に部分集団を混ぜず、比較時に履歴・母集団・内容基準を差し替えない。',
 'rqtp':'自由の許可に関わる同じ公衆・参照・出所・期間枠・基準点対応・候補範囲と、同じ内容族を保ち、部分集団記述だけを差し替えられる枠を作る。各候補の内容は同じ部分集団と候補から作り、hzpaで同じ候補の基準点において評価する。',
}
LIMITS=[
 '比較の対象を全将来内容または条件付きの全内容とする明示的な作用範囲の候補である。各将来点の内部で比較する読みと自動的に同一視しない。',
 '比較背景は既存rqtmの尺度だけの背景を使う。比較対象側に該当者が実在すること、尺度が確率であること、原文が唯一の比較対象を指定することは加えない。',
 '自由の許可・候補場面・基準点・内容族を同じ閉じた枠に保つ。候補場面の供給関数は全候補で同じ値を返す必要はないが、全て同じ候補の値を使う。',
 '全ての有限経路を量化するhzpfを保持する。比較の背景や引用内容の同一性は検査できるが、無制限の経路の全探索や集団命題全体の真理を有限検査で証明したとはしない。',
 '一般の条件付き内容の検査と、存在する伝播の引用構造の検査を区別する。伝播の定義を不透明な真偽基本述語に置き換えたものを実際の伝播の証明とは扱わない。',
 '既存34文・七単位の確認を保持し、新しい本文主張・原文対応範囲・意味確認済み単位は加算しない。原文に適した比較対象・尺度・視点・解釈値と、本文への全内容の接続は残る。',
]


def definitions():
    text=declaration('hzpq',FUTURE,'h['+PREDICATE+'] e',
        'i[subgroup '+PREDICATE+']['+k('hzpf',*('v '+n for n,t in FUTURE),'s[v subgroup]')+']')
    args=['o r[v state]' if n=='state' else 'v '+n for n,t in FUTURE]
    text+=declaration('hzpr',DESCRIBED,FRAME,'o a[r b[p hzpq]]['+' '.join(args)+']')
    branches=['c[v '+n+'][v branch]' for n,t in FUTURE]
    text+=declaration('hzps',BRANCH_FIELDS,FAMILY,'i[subgroup '+PREDICATE+' branch d]['+
        k('hzpf',*branches,'s[v subgroup]')+']')
    contents='i[branch d][c[v family][v subgroup v branch]]'
    text+=declaration('rqtp',CONDITION_FIELDS,'h['+PREDICATE+'] e',
        'i[subgroup '+PREDICATE+']['+k('hzpa',*('v '+n for n,t in FIELDS[:-1]),contents)+']')
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[]
    core['declarations']=closure(doc,['hzpr','hzps','rqtp','rqtm','rsx','rsy','rsw','rsz','hzny','rqsx','hzhb'])
    library=deepcopy(doc);library['statements']=[]
    library['declarations']=closure(doc,['rqtp','rqtm','rsx','rsy','rsw','rsz'])
    basis=dict(status='shared_existential_focus_with_permission_conditioned_alternatives',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Existential contents and permission conditions shared across focus alternatives',flush=True)


if __name__=='__main__':main()
