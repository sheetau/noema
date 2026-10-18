"""Build closed ranked contents for appointed thinkers' relative dissemination."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_relative_dissemination import SCOPED
from scripts.compose_thinking_disseminators import THINKING,call,variable

PARENT='examples/v016/kant-relative-dissemination.noema'
PARENT_BASIS='data/relative-dissemination-basis-v1.json'
FULL='examples/v016/kant-described-dissemination.noema'
CORE='examples/v016/described-dissemination-core.noema'
BASIS='data/described-dissemination-basis-v1.json'
PER_PERSON={'reference','subject','message','frame','anchor','departure','prior','attained'}
PER_RECIPIENT={'firsts','tails','processes','starts','ends'}
BINDINGS=[(n,'h[a d] '+t if n in PER_PERSON else 'h[a d a] '+t.removeprefix('h[a] ') if n in PER_RECIPIENT else t)
    for n,t in SCOPED if n not in ('origin','initial')]+THINKING
GROUP=[('history','h[d] c'),('before','h[d d] c'),('members','h[a d] c'),('governed','a'),
    ('appoints','h[a a a a d] c'),('guardianrole','h[a a d] c')]
FIELDS=GROUP+BINDINGS
DESCRIBED=[(n,t if n=='state' else 'i['+t+']') for n,t in FIELDS]
PRIMITIVES={
 'hzon':('[a a i b[e] d] c',['文章箇所','著者','階数1の内容記述','帰属文脈'],
    'この著者がこの箇所で指定された内容を主張するという帰属。ucと同じ主張帰属の意味を、階数0の記述評価を内側に含む階数1の内容記述へ拡張する。帰属時に引用内容を実行せず、その真理・実現・合理性を含意しない。ucの型を変更せず、記述を低い階数へ強制変換しない。'),
}
MEANINGS={
 'hzoo':'同じ人・同じ評価機会で、各人の参照文脈・話題・発話・期間枠・基準時・自己離脱の前後を供給関数から取り出し、hzolへ渡す。受け手ごとの経路と取得過程も同じ人・機会に結ぶ。人物・機会ごとに別の行為を持てるが、共通の性向記述を保つ。',
 'hzop':'同じ履歴と順序について、内容を評価する基準点より後の全機会にhzojを適用する。任用された同じ人々の複合条件としてhzooを渡す。人と機会を独立判断・自己離脱・相対範囲への伝播の全てへ共用し、各点で人物が交替することを許す内容。',
 'hzoq':'hzopの階数1の関数記述へ、明示した閉じた引数記述を適用して、閉じた階数1の内容記述を作る。共通の性向記述はo rで値として持ち上げ、記述の中身を内容構築の段階では評価しない。',
 'hzor':'同じ箇所・著者・帰属文脈へ、hzoqが構成する完全に引数を充足した内容記述をhzonで帰属する。関数ひな形そのものへの帰属や、内容の実行結果への帰属に置き換えない。',
}
LIMITS=[
 'hzonは新しい主張の種類ではなく、既存ucと同じ意味を高い引用階数へ与える型付きの基本関係である。低い記述と高い記述の自動同一化・任意の同義性の判定は加えない。',
 'hzopは内容の評価点を全将来機会の基準とする。帰属の文脈はhzonの別引数であり、帰属時点を内容の評価点へ自動代入しない。',
 '人・機会ごとの供給関数はNoemaで定義できる。氏名、発信行為、経路、対象期間を関数ひな形の未充足引数に残したまま一つの命題と呼ばない。閉じた記述でも、その記号が何を指すかは解釈を必要とする。',
 '個々人の基準時・離脱・経路は別々に設定できる。各機会の本人と初期点を別の人や点へ交換する自由は与えない。全員の発話表記を同一化せず、伝達される性向記述を共用する。',
 '原文に適した履歴・母集団・社会的範囲・性向評価・広がり、sogarとDenn、比喩、自由と将来の様相は未完。引数を充足できる構造を、原文の正しい読みや引用内容の真理の保証にしない。',
 '既存32文と全意味規約・七単位の確認を保存する。新しい無条件の著者主張は加えず、今回の接続候補を完成した本文に数えない。',
]


def declaration(name,fields,result,body):
    return 'd '+name+'['+' '.join(n+' '+t for n,t in fields)+'] '+result+'['+body+'].'


def definitions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    def supplied(n):
        if n in PER_PERSON:return 'c[v '+n+'][v origin v initial]'
        if n in PER_RECIPIENT:return 'i[target a][c[v '+n+'][v origin v initial v target]]'
        return variable(n)
    body=call('hzol',*(supplied(n) for n,t in SCOPED+THINKING))
    text+=declaration('hzoo',[('origin','a'),('initial','d')]+BINDINGS,'c',body)
    qualified='i[origin a initial d]['+call('hzoo','v origin','v initial',*(variable(n) for n,t in BINDINGS))+']'
    body=call('hzoj','v history','v before','v base','v members','v governed','v appoints','v guardianrole',qualified)
    text+=declaration('hzop',FIELDS,'e','b base['+body+']')
    args=['o r[v state]' if n=='state' else variable(n) for n,t in FIELDS]
    text+=declaration('hzoq',DESCRIBED,'i b[e]','o a[r b[p hzop]]['+' '.join(args)+']')
    text+=declaration('hzor',[('node','a'),('author','a'),('context','d')]+DESCRIBED,'c',
        call('hzon','v node','v author',call('hzoq',*(variable(n) for n,t in FIELDS)),'v context'))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzor','hzny','rqsx'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='closed_ranked_claim_with_native_future_dissemination',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Closed ranked dissemination content constructed separately from author attribution',flush=True)


if __name__=='__main__':main()
