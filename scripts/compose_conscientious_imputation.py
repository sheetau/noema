"""Compose conscientious fault judgments, warranted possibility and scoped absence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/clerical-public-freedom-basis-v1.json'
LIBRARY='examples/v016/conscientious-imputation.noema'
BASIS='data/conscientious-imputation-basis-v1.json'
PRIMITIVES={
    'h247h':('[a a a d d] c',['judgment','person','matter','reference','point'],
        'この判断は、固定基準時に特定された同じ事柄を、この本人の選択・不作為に関する落ち度として本人へ帰している。判断行為の実行・判断主体・道徳的評価であること・その正当性は別に結ぶ。原因であるだけ、単なる不快、他人の落ち度、法的制裁とは区別する。hziqの状況上の帰責評価と異なり、個体として指定された事柄への判断内容を扱い、誤った帰責も記述できる。'),
    'h247i':('[a d d] c',['judgment','reference','point'],
        'この判断は、同じ固定基準時の対象事情について、当該判断に適用される評価基準と利用すべき根拠に照らして正当化できる。実際の確信、発言、単なる根拠の存在、反論がまだないこととは区別する。道徳的自己判断かどうかはfa/seと対象への結合で別に示す。正当化の全理論・決定手続を与えたとはしない。'),
    'h247j':('[a a d d d] c',['person','matter','reference','evaluation','candidate'],
        'この本人が、固定基準時に特定された同じ事柄を評価するという事情を保ったまま、同じ評価点から判断の候補として考慮する状況。評価を試みる候補の完全な範囲を解釈で固定し、帰責が成功する候補だけを選ばない。判断の実行・帰責・正当化、現実の結果や規範的許可はそれぞれ別である。出来事自体を別のものへ変更する将来の経路や、あらゆる論理的可能世界と同一視しない。'),
}
MEANINGS={
    'r37r':'同じ本人が同じ判断を行い、その判断が本人の行為を道徳的要求に照らして評価し、同じ事柄を対象として、それを本人の落ち度として帰する内容。smのfa/seの結合へfbと帰責内容を加える。罪悪感の有無や帰責の正しさは追加しない。',
    'r37s':'同じ本人・判断・事柄・基準・評価点の良心的自己帰責r37rと、その同じ判断の正当化可能性h247iを合わせる。誤った自己非難だけでは成立しない。',
    'r37t':'同じ本人・事柄・固定基準に対する全候補範囲h247jのいずれかに、同じ本人の正当化できる道徳的自己帰責r37sとなる判断がある。現実に判断・罪悪感・処罰が生じたことも、その義務・許可も含意しない。',
    'r37u':'呼出側が固定した事柄の範囲の全対象について、同じ本人・基準・評価点のr37tが成立しない。既に非難した対象だけへ縮めず、一つでも帰責可能な対象があれば不成立。範囲外の人生全体の無過失を含意しない。',
}
LIMITS=[
    'u0012[3453,3527)のdem Gewissen zur Last gelegt werden könnteを、道徳的な自己評価において正当化できる帰責の可能性として読むための依存群。唯一の語義や作者の意図の証明ではない。',
    '既存smは良心の機能上の自己判断であり、感情や能力の全語義ではない。fa/seを同じ判断へ再利用する。hziqは個体で指定された事柄・判断への非事実的帰責内容を持たないため、意味を変えて流用しない。',
    'könnteを、人が心理的に誤って自責し得るという可能性だけにはしない。後続Dennの理由提示と整合する、根拠をもって帰責できるという採用解釈。正当化h247iと候補範囲h247jは明示された基本関係であり、その一般理論は未完。',
    'r37uの範囲は外部引数で受ける。この段階ではhiebeiの先行する二立場への照応、auch、著者帰属を本文へ接続していない。全文確認文字数を増やさない。',
    '有限モデルは同じ判断・事柄・本人・基準・候補の接続と否定範囲を検査する。実際の候補や根拠の完全な列挙、意味同値性の自動証明、教義の真理の判定ではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    fields='person a judgment a matter a reference d'
    args='v person v judgment v matter v reference'
    text='d r37r['+fields+'] e[b point['+both(
        'k fa[v person v judgment v point]','k se[v judgment v person v point]',
        'k fb[v judgment v matter v point]','k h247h[v judgment v person v matter v reference v point]')+']].\n'
    text+='d r37s['+fields+'] e[b point['+both('t[k r37r['+args+']][v point]',
        'k h247i[v judgment v reference v point]')+']].\n'
    text+='d r37t[person a matter a reference d] e[b point[g candidate d['+both(
        'k h247j[v person v matter v reference v point v candidate]',
        'g judgment a[t[k r37s['+args+']][v candidate]]')+']]].\n'
    text+='d r37u[person a scope h[a] c reference d] e[b point[f matter a[y[c[v scope][v matter]][u[t[k r37t[v person v matter v reference]][v point]]]]]].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['fa','se','fb']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS)) & set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='conscientious_fault_and_warranted_possibility_dependency',document=LIBRARY,primitives=prims,
        definitions=MEANINGS,imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
