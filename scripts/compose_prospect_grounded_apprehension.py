"""Require grounds for each feared adverse prospect, retaining the old reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_supported_apprehension import RELATIONS, EPISODE, FIELDS, GENERAL
from scripts.compose_described_apprehension import DESCRIPTION, params

OLD_LIBRARY='examples/v016/supported-apprehension.noema'
OLD_BASIS='data/supported-apprehension-basis-v1.json'
LIBRARY='examples/v016/prospect-grounded-apprehension.noema'
BASIS='data/prospect-grounded-apprehension-basis-v1.json'
PRIMITIVES={
 'h26u4':('[a a d] c',['person','episode','point'],
  '同じ本人がこの評価点でこの心理状態を経験している。状態の名前、他人の状態、単なる傾向から現実の経験を補わない。'),
 'h26u5':('[a '+DESCRIPTION+' d] c',['episode','topic','point'],
  'この心理状態が同じ点で指定の閉じた性質記述を対象としている。記述の真理や対象の実在を要求せず、同じ外延の別記述へ対象関係を自動移転しない。'),
 'h26u6':('[a d] c',['episode','point'],
  'この心理状態には同じ点で不快な情動が伴う。不利益の冷静な予測、単なる否定判断、回避した事実とは分ける。'),
 'h26u7':('[a d d] c',['episode','point','prospect'],
  'この心理状態で同じ評価点に恐れの対象として具体的に予期している候補経過。思い浮かべただけの可能性や本人が除外している仮定は含めない。実際の未来や確実視とは分け、根拠の有無によって候補を選別しない。'),
 'h26va':('[a d d] c',['person','reference','prospect'],
  '同じ固定評価基準で、この候補経過の実現はこの本人にとって不利益となる。候補での評価であり、現在又は実際の未来の害、他人だけの不利益を意味しない。'),
 'h26vb':('[a a d d] c',['person','reason','reference','point'],
  '同じ固定基準で、この評価点に本人が検討の根拠として利用できる理由。世界のどこかに存在するだけの資料、他人にだけ利用可能な理由と分ける。実際の採用や判断の正しさは要求しない。'),
 'h26vc':('[a a '+DESCRIPTION+' d d d] c',['person','reason','topic','reference','point','prospect'],
  '同じ本人・対象記述・固定基準・評価点について、この理由は、この不利益候補を恐れの対象として見込む十分な認識的根拠になる。利用可能な反対証拠による敗北も同じ基準で考慮する。感情が発生した原因、本人の確信、単なる理由の存在、演繹的証明、実際の害とは区別する。支持の十分性は固定した解釈入力であり、未評価を支持の不在へ変換しない。'),
}
MEANINGS={
 'r6en':'同じ本人・対象記述・評価点・一つの候補経過について、利用できる理由の少なくとも一つがその同じ候補を支持する。別候補の理由を流用しない。',
 'r6eo':'同じ情動状態で予期され本人に不利益なこの候補について、r6enの利用可能な支持理由がない。情動の経験・対象・不快さはr6epで結ぶ。',
 'r6ep':'同じ本人・情動状態・対象記述・点に既存rvvの不快な不利益予期があり、その同じ状態の候補にr6eoが少なくとも一つある。支持される別候補が混在していても、支持のない候補を見落とさない。',
 'r6eq':'同じ本人・対象記述・点にr6epを満たす情動状態が存在する。別状態の根拠は当該候補への支持にならない。',
 'r6er':'全ての閉じた対象性質記述についてr6eqがない。根拠のある恐れや実際の害を否定せず、実行器が列挙できない記述全域を有限標本に置き換えない。',
 'r6es':'同じ本人・対象記述・固定基準について、r6eqへ経験・対象・情動・候補・不利益・利用可能性・支持の各関係を接続し、その不成立を点ごとに返す。固定基準を変えて支持を借用しない。',
 'r6et':'r6esと同じ具体的な七関係・本人・固定基準でr6erの全対象範囲を接続する。影の比喩を根拠のない恐れの不在とする読みの内容候補であり、字義的な影、啓蒙、軍隊、発言能力はここから導かない。',
}
LIMITS=[
 'u0017第一文のsich nicht vor Schatten fürchtetを、本人が対象として恐れる不利益候補の各々に利用可能な認識的根拠があるという明示的な読みで進める。関連するAdelungの慣用表現は補助であり、カントの意図の唯一性を証明しない。',
 '旧rvyは一状態に支持される候補が一つあれば足りた。この群は各恐れられる不利益候補について支持を要求する強い読みで、旧定義・旧判断・本文を変更せず別識別子に置く。',
 '理由は恐れの心理的発生原因ではなく候補を見込む認識的根拠。支持されても害が実現しないことがあり、根拠なく恐れた害が実現することもある。感情の強さの適切さ、身体反応、全知、無謬性、生涯の性格は要件にしない。',
 '心理状態の対象は個体性質の閉じた構文で表す既存rvvを再利用する。全記述への量化を保持し、検査ではその本体を明示した二記述に適用する。全域の直接評価は拒否する。',
 '一般現在の人物条件への束縛、比喩対応と否定の談話上の提示、selbst aufgeklärtの宗教から立法への範囲、軍隊・平穏・Freistaat・引用命令・第一文全体はまだ未統合。確認文字数は増やさない。',
]

def refs():return ' '.join('v '+n for n,_ in RELATIONS)
def fixed_relations():
    return ' '.join(('p h26u4','p h26u5','p h26u6','p h26u7',
      'i[person a prospect d][k h26va[v person v reference v prospect]]',
      'i[person a reason a point d][k h26vb[v person v reason v reference v point]]',
      'i[reason a topic '+DESCRIPTION+' point d prospect d][k h26vc[v person v reason v topic v reference v point v prospect]]'))

def definitions():
    base='v person v topic v anchor';tail=refs()
    text='d r6en[person a topic '+DESCRIPTION+' anchor d prospect d available h[a a d] c supports h[a '+DESCRIPTION+' d d] c] c[g reason a['+both('c[v available][v person v reason v anchor]','c[v supports][v reason v topic v anchor v prospect]')+']].\n'
    text+='d r6eo['+params(EPISODE)+' prospect d] c['+both('c[v anticipated][v episode v anchor v prospect]','c[v adverse][v person v prospect]','u[k r6en['+base+' v prospect v available v supports]]')+'].\n'
    text+='d r6ep['+params(EPISODE)+'] c['+both('k rvv[v episode '+base+' '+tail+']','g prospect d[k r6eo[v episode '+base+' '+tail+' v prospect]]')+'].\n'
    text+='d r6eq['+params(FIELDS)+'] c[g episode a[k r6ep[v episode '+base+' '+tail+']]].\n'
    text+='d r6er['+params(GENERAL)+'] c[f topic '+DESCRIPTION+'[u[k r6eq['+base+' '+tail+']]]].\n'
    text+='d r6es[person a topic '+DESCRIPTION+' reference d] e[b point[u[k r6eq[v person v topic v point '+fixed_relations()+']]]].\n'
    text+='d r6et[person a reference d] e[b point[k r6er[v person v point '+fixed_relations()+']]].\n'
    return text

@lru_cache(None)
def inherited():
    old=parse((ROOT/OLD_LIBRARY).read_text(encoding='utf-8'))
    meanings=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']
    doc=deepcopy(old);doc.update(declarations=closure(old,('rvv','rvw','rvx','rvy')),statements=[])
    return doc,{d['name']:meanings[d['name']] for d in doc['declarations']}

def build():
    old,meanings=inherited()
    doc=parse(format_graph(old,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    basis=dict(status='each_feared_adverse_prospect_requires_available_grounds_partial',document=LIBRARY,
      primitives={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()},
      definitions=meanings|MEANINGS,imported_symbols={n:OLD_BASIS for n in meanings},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in (OLD_LIBRARY,OLD_BASIS)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
