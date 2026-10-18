"""Connect independent thinking, appointment and the same sender's dissemination."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-emancipated-transmission.noema'
PARENT_BASIS='data/emancipated-transmission-basis-v1.json'
FULL='examples/v016/kant-thinking-disseminators.noema'
CORE='examples/v016/thinking-disseminators-core.noema'
LIBRARY='examples/v016/appointed-qualified-senders.noema'
BASIS='data/thinking-disseminators-basis-v1.json'
FUTURE=[('audience','a'),('reference','d'),('origin','a'),('subject','a'),('message','i[h[a] f]'),('state','i[h[a] e]'),
 ('frame','a'),('initial','d'),('anchor','d'),('departure','a'),('prior','d'),('attained','d'),
 ('firsts','h[a] a'),('tails','h[a] j[a]'),('processes','h[a] a'),('starts','h[a] d'),('ends','h[a] d'),
 ('sender','h[a] a'),('recipient','h[a] a'),('activity','h[a] a'),('point','h[a] d'),('extent','h[h[a] c h[a] c] c')]
THINKING=[('thinkpoints','h[a d] j[d]'),('thinkcases','h[a d d] c'),('thinkassessed','h[a d d] c'),
 ('thinkweights','h[a d d] b'),('thinkthreshold','h[a d] b'),('thinktopics','h[a d d] a'),('thinkpresented','h[a a d] c')]
QUALIFIED=[('members','h[a d] c'),('governed','a'),('appoints','h[a a a a d] c'),
 ('guardianrole','h[a a d] c'),('qualified','h[a d] c')]
MEANINGS={
 'hzog':'同じ発信者について、初期の評価点で独立した理由ある判断への応答傾向hzhhが成立し、その点より後の受け手の取得を含むhzofの伝播が成立する。判断傾向と自己離脱・伝播で人物を交換せず、現在の一回の判断へ置き換えない。',
 'hzoh':'同じ評価点の母集団を人の範囲として確認し、その中で任用された後見役hzhbと指定の複合条件を満たす異なる二人を要求する。原文用の複合条件にはhzogを渡す。二人であることを上限にせず、条件ごとに別人を使わない。',
 'hzoi':'同じ順序付き履歴の基準より後にある非空の指定範囲について、各点でhzohを要求する。各点の任用・複合条件・母集団に同じ点を渡す。点ごとに人物が交替してよく、全点で同じ二人を要求しない。',
 'hzoj':'同じ履歴の基準点より厳密に後の全点を内部で選び、その範囲をhzoiへ渡す。不成立の将来点だけを外した別の範囲を供給できず、将来点が一つもなければ成立しない。',
}
LIMITS=[
 '発信者の独立判断への応答傾向はhzhh、受け手へ広がる理由ある自己評価と規範承認への性向はhznyで別に記述する。両者を一つの同義語にまとめない。場面・基準の適切さと心理機構は未完。',
 '初期の評価点で同じ発信者を自己思考者として評価し、そこから後の取得完了をhzofへ渡す。将来の候補ごとの基準点の対応は明示する必要があり、現実の基準点を全候補へ無条件に共有しない。',
 'hzohは後見役の中に複数の該当者がいるという明示した読解候補である。全ての自己思考者が後見役であること、該当者が正確に二人であること、全員ではないことは追加しない。',
 'qualifiedは同じ人・評価点を受け取る複合条件である。原文の接続例ではhzogの本体を実行する。任意の真偽関数を与えた一般テストを、伝播そのものの検証と扱わない。',
 '各発信者の発話・宛先・伝達経路・将来の評価基準時は異なってよい。共通の性向内容を伝えても、全員の発話の文字列や発信行為を同一にする必要はない。',
 'hzoiは指定された非空の将来点、hzojは同じ履歴内の全将来点を調べる。履歴自体の完全性は解釈の条件であり、有限の試験から無期限の将来や全可能世界を尽くすとはしない。sogarの比較背景、Dennの説明、自由の条件、周囲の範囲、比喩と著者帰属は未完。',
 '既存32文と全意味規約・七単位の確認を保存し、旧範囲の接続を補う。新しい原文範囲や無条件の著者主張、意味確認済み単位は加算しない。',
]


def variable(name):return 'v '+name
def call(name,*args):return 'k '+name+'['+' '.join(args)+']'
def apply(name,*args):return 'c[v '+name+']['+' '.join(args)+']'
def conjunction(*items):return items[0] if len(items)==1 else 'w['+items[0]+']['+conjunction(*items[1:])+']'
def declaration(name,fields,body):return 'd '+name+'['+' '.join(n+' '+t for n,t in fields)+'] c['+body+'].\n'


def definitions():
    text=declaration('hzog',FUTURE+THINKING,conjunction(
        call('hzhh',variable('origin'),variable('initial'),*(variable(n) for n,t in THINKING)),
        call('hzof',*(variable(n) for n,t in FUTURE))))
    human='f person a[y['+apply('members',variable('person'),variable('point'))+']['+call('aa',variable('person'))+']]'
    status='i[person a context d]['+call('hzhb',variable('person'),variable('governed'),variable('context'),variable('appoints'),variable('guardianrole'))+']'
    text+=declaration('hzoh',[('point','d')]+QUALIFIED,conjunction(human,
        call('rpw',variable('point'),variable('members'),status,variable('qualified'))))
    perpoint=conjunction(apply('history',variable('point')),apply('before',variable('anchor'),variable('point')),
        call('hzoh',variable('point'),*(variable(n) for n,t in QUALIFIED)))
    text+=declaration('hzoi',[('history','h[d] c'),('before','h[d d] c'),('anchor','d'),('opportunities','h[d] c')]+QUALIFIED,
        conjunction(call('ta',variable('history'),variable('before')),apply('history',variable('anchor')),
            'g point d['+apply('opportunities',variable('point'))+']',
            'f point d[y['+apply('opportunities',variable('point'))+']['+perpoint+']]'))
    text+=declaration('hzoj',[('history','h[d] c'),('before','h[d d] c'),('anchor','d')]+QUALIFIED,
        call('hzoi',variable('history'),variable('before'),variable('anchor'),
            'i[point d]['+conjunction(apply('history',variable('point')),apply('before',variable('anchor'),variable('point')))+']',
            *(variable(n) for n,t in QUALIFIED)))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzog','hzoj','hzny','rqsx'])
    library=deepcopy(core);library['declarations']=closure(doc,['hzoh','hzoj'])
    basis=dict(status='same_appointed_people_think_depart_and_disseminate',document=FULL,
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
    print('Independent thinking, appointed roles and dissemination bound to the same people',flush=True)


if __name__=='__main__':main()
