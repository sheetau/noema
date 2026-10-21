"""Compose obtaining all scoped practical benefits from fixed doctrinal content."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_responsible_exposition import FIELDS,ARGS,TARGETS

PARENTS=('data/clerical-report-forecast-basis-v1.json','data/responsible-exposition-basis-v1.json')
LIBRARY='examples/v016/practical-benefit-extraction.noema'
BASIS='data/practical-benefit-extraction-basis-v1.json'
PRIMITIVES={
    'h252p':('[a a i[e] d] c',['outcome','beneficiary','content','reference'],
        'この結果の定式化の同じ閉じた内容は、固定基準で、指定受益対象の行為・生活上の態度や実践の改善に当たる利益を表す。利益の対象と評価基準を固定し、単なる理論的知識の増加、無害だけの状態、別対象だけの利益と区別する。共同体を受益対象にでき、全成員に同じ効果があることや金銭換算、現実の成立、特定の道徳理論の正当性は要求しない。'),
    'h252q':('[a a a a d] c',['person','source','beneficiary','outcome','reference'],
        '固定基準の本人・出所・受益対象と関連する事情・機会について、その出所の内容を適用して得られる結果の、文脈上問題となる完全な範囲にこの定式化が属する。具体的な内容は同じh246eで示す。実際に得られた結果だけを事後に選ばず、未達の利用可能な結果も含む。実践的利益の分類・実際の利用・因果・成果は別に確認し、無関係な出所や別の受益対象、無制限の将来の新事情へ範囲を広げない。'),
    'h252r':('[a a i[e] a i[e] d d] c',['act','source','source_content','outcome','outcome_content','reference','point'],
        '同じ行為の方法・遂行において、この出所の指定内容を、指定した結果内容へ至るための働きのある材料・指針として適用している。内容の同一性と固定基準を保持し、出所への偶然の言及、物理的な併置、別の結果だけのための利用とは区別する。行為の生起・行為者・結果の成立と因果的寄与は別に結ぶ。教義の真理、本人の賛同、形式的演繹、唯一の手段、全内容の一度の伝達は要求しない。'),
}
MEANINGS={
    'r426':'同じ結果定式化・固定基準のh246eの閉じた内容を、一個体を引数に取る閉じた段階0の内容関数へ持ち上げる。内容は構成時に固定し、rqquの結果記述として使う。構成だけでは結果の真理を実行しない。',
    'r427':'同じ本人の同じ生起行為が、規定群の固定列から作るr42hの内容を指定結果へ向けて適用し、その同じ結果の実践的な利益内容を実際に成立させる因果的寄与rqquを持つ。受益対象、出所、結果記述、基準、状況を共用する。目的や共存だけでは足りず、教義内容自体の真理は要求しない。',
    'r43a':'同じ本人・規定群・受益対象・固定基準におけるh252qの全結果のうち、h252pの実践的利益を表す範囲が非空であり、一つの共通する活動がその全てについてr427を満たす。活動は複合的でもよいが、別々の実行不能な代替を寄せ集めず、少なくとも一利益や都合のよい達成済み部分へ弱めない。',
    'r43b':'同じ聖職者事例r35tと同じ規定群・完全な固定列r42jを保ち、本人を行為者、本人の同じ会衆を受益対象としてr43aを結ぶ。聖職者自身や別の会衆だけの利益へ入れ替えない。文脈上の代表的事例への主節内容として用い、著者への帰属とalsdannの接続は別途行う。',
}
LIMITS=[
    'u0012[3899,4278)のallen praktischen Nutzen für seine Gemeinde aus Satzungen ziehenに向けた依存群。主節の内容を構成するが、alsdannの前文への照応、関係節との接続、談話の譲歩・理由・焦点、文全体の帰属は未統合。確認文字数を増やさない。',
    'Nutzen ziehenを、教義を用いて会衆の行為・生活上の態度や実践に利益を生じさせる読みとする。Adelung Nutzenの教えの適用と状態改善の用例を参照する。単なる利益への意図、利用できる可能性、金銭利益だけ、教義の論理的証明とはしない。',
    'allは固定した文脈の利用可能な実益の各面を尽くす読み。範囲の内容と完全性は明示解釈で与え、達成したものだけに狭めない。有限列への限定、効用の加算、期待値の最大化、無関係なあらゆる将来の利益は補わない。範囲に両立しない要求があれば、この強い全利益の主張は成立しない。',
    '実益の内容は各定式化のh246eで実際のNoema内容として供給する。h252p/qは内容を置き換える一文判定ではなく、その利益の分類と文脈範囲の入力。全利益の具体的な一覧を原文へ捏造せず、後続の全文ではこの範囲を量化・束縛する。',
    '会衆は共同の受益対象とする。会員全員に同じ結果が分配されることや本人の金銭報酬を補わず、既存r35tにより誰のどの会衆かを固定する。受益対象が人だけのg3ではなく、一般的な内容間の因果rqqu/hzieを用いる。',
    'r43aの一つの活動は文脈上の複合的な適用でもよい。固定した短時間に全成員へ一斉に教示したこと、教義が全て真であること、唯一原因性は要求しない。実際の因果関係の妥当性は解釈入力であり、有限試験が現実の宗教教育の効用を証明するものではない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r426[outcome a reference d] i[h[a] e][o a[r[i[body e][i[target a][v body]]]][k h246e[v outcome v reference]]].\n'
    content='k h246e[v outcome v reference]'
    source='k r42h[k h252g[v bundle v reference] v reference]'
    args='v person v act v bundle v beneficiary v outcome v reference v point'
    text+='d r427[person a act a bundle a beneficiary a outcome a reference d point d] c['+both(
        'k df[v person v act v point]',
        'k h252p[v outcome v beneficiary '+content+' v reference]',
        'k h252r[v act v bundle '+source+' v outcome '+content+' v reference v point]',
        'k rqqu[v act r[p rqye] v outcome k r426[v outcome v reference] v point]')+'].\n'
    eligible=both('k h252q[v person v bundle v beneficiary v outcome v reference]',
        'k h252p[v outcome v beneficiary '+content+' v reference]')
    text+='d r43a[person a bundle a beneficiary a reference d point d] c['+both(
        'g outcome a['+eligible+']','g act a[f outcome a[y['+eligible+'][k r427['+args+']]]]')+'].\n'
    frame=' '.join('v '+n for n in TARGETS[:-1])+' v reference'
    text+='d r43b['+FIELDS+' point d] c['+both('k r35t['+frame+']',
        'k r42j[v church v creed v subject v standard v bundle k h252g[v bundle v reference] v reference]',
        'k r43a[v person v bundle v congregation v reference v point]')+'].\n'
    return text


def build():
    catalogs=parents();doc=deepcopy(catalogs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for old,roots in zip(catalogs,(('r35t','rqqu','rqye','df'),('r42j','r42h','h252g'))):
        for d in closure(old.document,list(roots)):
            n=d['name'];e=old.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(c.entries) for c in catalogs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in catalogs))
    basis=dict(status='all_scoped_practical_benefits_from_same_doctrinal_content',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
