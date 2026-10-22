"""Bind personal judgments, grasped views, public presentation and review purpose."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind

PARENT='data/prince-sentence-basis-v1.json'
LIBRARY='examples/v016/offered-judgments.noema'
BASIS='data/offered-judgments-basis-v1.json'
MESSAGE='i[h[a] f]'
TARGET='i b[h[j[a] d] e]'
NAMES=('person','activity','scholar','audience')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
PRIMITIVES={}
MEANINGS={
 'r53m':'同じ固定基準で、引数の認識項目の代表内容r5ccを肯定的に述べる発話関数。内容の真理を評価せず、原文文字列を発話内容の代用にしない。',
 'r53n':'同じ人・項目・固定基準・点で、本人が同じ代表内容を受容し、その内容を肯定する同じ判断を保持する。現に判断行為を行うことや、内容の真理は要求しない。',
 'r53o':'r53nの同じ本人・項目・保持判断について、内容の区別と関係を本人が把握し、その同じ判断で用いる理由が支持し、現在の受容の十分な認識根拠として働く。提出者の根拠ある理解としての読みであり、別の真偽評価による結論の真理は追加しない。',
 'r53p':'同じ本来の公衆の人間の成員が、同じ固定基準の代表項目とr53mの同じ発話内容について判断するという審査目的。宛先範囲を固定基準に保ち、判断の生起・対象・評価内容をhzwで結ぶ。賛同、正しい結論、全員の評価は要求しない。',
 'r53q':'同じ本人・活動・学識者の立場・本来の公衆・項目・固定基準で、公的理性使用r2ziの分類、同じ公衆への宛先cc/ce、本人名義の同じ発話の非空の人間への実際の提示rheを結ぶ。全世界の受領や媒体の指定を追加しない。',
 'r53r':'r53qの同じ発表行為で、本人が同じ公衆・代表項目・発話内容へのr53pの審査を目的とする。発表と目的を別活動へ分けず、審査の実現、内容の真理又は公衆の賛同は含めない。',
 'r53s':'r53rの発表・審査目的と、同じ本人が同じ点で同じ代表内容についてr53nの判断を保持することを結ぶ。単なる他人の見解の引用を自分の判断として通さない。',
 'r53t':'r53rの発表・審査目的と、同じ本人が同じ点で同じ内容についてr53oの把握・根拠ある判断を保持することを結ぶ。自分の洞察として提出する内容の読みで、公開による確証が既にあることは要求しない。',
 'r53u':'判断項目列と洞察項目列の和が非空で、前者の全項目にr53s、後者の全項目にr53tを同じ本人・一つの活動・立場・公衆・固定基準・点で要求する。別々の発表から一つの複合発表を捏造しない。',
 'r53v':'二つの項目列と、本人・活動・学識者・公衆の正確な四個体列から、r53uの複合した発表実行内容を返す。余分又は不足する束縛を捨てず、規範対象へ引用しても実際の発表を断言しない。',
 'r53w':'二項目列の閉じた記述を引用適用でr53vへ固定し、四個体列と固定基準を受ける段階1の発表実行内容の記述を作る。提示・判断・根拠・審査目的を任意の別targetへ取り替えない。',
}
LIMITS=[
 'u0015第二文[574,889)へ向け、ihre Urtheile und Einsichten、in der Qualität der Gelehrten、öffentlich der Welt zur Prüfung darlegenを結ぶ依存群。全文の意味判断はまだ増やさない。',
 '本人の判断は現に保持する肯定見解、本人の洞察はその内容の把握と同じ判断への根拠がある見解として読む。審査に提出される本人の認識上の立場を記述し、著者が全提出内容の客観的真理を保証することにはしない。根拠の適切さは既存h26ajの固定解釈に従う。',
 '各内容はh26aeのNoema命題で与える。代表h26ag、別名での受容r5cd、保持判断h26ai/h245qを共有する。発話、判断対象、審査目的は同じ代表項目と固定基準へ結ぶ。',
 '世界はceの全読者公衆。公的使用と宛先は基準で固定し、実行には少なくとも一人の人間への実際の提示を要求する。公衆全員の受領・理解・判断・賛同、特定の刊行媒体は追加しない。',
 '目的は少なくとも一人の公衆が同じ内容を検討すること。目的の保持と達成を分離し、自由・許可を後で同じ実行記述へ結ぶ。引用の内側にある保持判断や発表の実行を許可時点の前提へ移さない。',
 '二つの有限項目列は一つの発表候補を構成する。各列が必ず二件以上あるという数の制約は置かず、和だけを非空とする。本文の一般的な複数対象は後の全候補量化で保持し、一つの列が全候補を網羅したとはしない。',
 '採用信条との同じ論点での相違、hier oder da、君主への照応、聖職者とverehrungswürdigの評価、職務義務を保つ自由、無制約の他者とnoch mehr、全文帰属は未接続。これらを削って全文の完成とはしない。',
 '新しい基本記号は追加せず既存定義を合成する。正本113主張・登録簿v197・既存17全単位判断と第一文490文字の判断は保持する。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def message(reference='v reference'):return 'o a[r[p r53m]][k h223h['+reference+']]'
def goal():return 'o a[r[p r53p]][k h223g[v audience] k h223g[v item] k h223h[v reference]]'

def definitions():
    canonical='k h26ag[v item v reference]'
    text='d r53m[reference d] h[a] f[i[item a][j s[k r5cc[v item v reference]]]].\n'
    fields='person a judgment a item a reference d point d';args='v person v judgment v item v reference v point'
    own=both('k aa[v person]','k h26ad[v item v reference]','k r5cd[v person v item v reference v point]',
        'k h26ai[v person v judgment v reference v point]',
        'k h245q[v judgment '+canonical+' r[p h26ae] v reference '+TRUE+' v point]')
    text+='d r53n['+fields+'] c['+own+'].\n'
    text+='d r53o['+fields+'] c['+both('k r53n['+args+']','k h26ah[v person '+canonical+' v reference v point]',
        'g reason a['+both('k fc[v judgment v reason v point]','k fd[v reason v judgment v point]',
        'k h26aj[v reason v judgment v reference v point]')+']')+'].\n'
    recipient=both('k aa[v recipient]','k h6t[v audience v recipient v reference]')
    review='g recipient a['+both(recipient,'g judgment a[k hzw[v recipient v judgment '+canonical+' '+message()+' v point]]')+']'
    text+='d r53p[audience a item a reference d] e[b point['+both('k ce[v audience v reference]',review)+']].\n'
    fields=FIELDS+' item a reference d point d';args=ARGS+' v item v reference v point'
    speech='k rhe[v person v activity v scholar i[listener a][e[v listener][v recipient]] '+canonical+' '+message()+' v point p dg p f3 p f2 p h253l]'
    names=['e[s[k '+provider+'[v '+n+']]][v '+n+']' for n,provider in (('audience','h223g'),('item','h223g'),('reference','h223h'))]
    text+='d r53q['+fields+'] c['+both(*names,'k r2zi[v person v activity v scholar v reference]',
        'k cc[v activity v audience v reference]','k ce[v audience v reference]',
        'g recipient a['+both(recipient,speech)+']')+'].\n'
    text+='d r53r['+fields+'] c['+both('k r53q['+args+']','k hzu[v person v activity '+goal()+' v point]')+'].\n'
    for name,condition in (('r53s','r53n'),('r53t','r53o')):
        text+='d '+name+'['+fields+'] c['+both('k r53r['+args+']','g judgment a[k '+condition+'[v person v judgment v item v reference v point]]')+'].\n'
    fold=lambda items,target:'q[v '+items+']['+TRUE+'][i[ok c item a]['+both('v ok','k '+target+'['+args+']')+']]'
    text+='d r53u['+FIELDS+' judgments j[a] insights j[a] reference d point d] c['+both(
        'u[e[d[m[v judgments][v insights]]][n p a b]]',fold('judgments','r53s'),fold('insights','r53t'))+'].\n'
    text+='d r53v[judgments j[a] insights j[a] bindings j[a] reference d] e[b point['+bind(NAMES,
        'k r53u['+ARGS+' v judgments v insights v reference v point]')+']].\n'
    template='r b[i[judgments j[a] insights j[a]][i[bindings j[a] reference d][k r53v[v judgments v insights v bindings v reference]]]]'
    text+='d r53w[judgments i[j[a]] insights i[j[a]]] '+TARGET+'[o a['+template+'][v judgments v insights]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document)
    roots=['r5cc','r5cd','aa','h26ad','h26ag','h26ae','h26ai','h245q','h26ah','fc','fd','h26aj','h6t','hzw','r2zi','cc','ce','rhe','dg','f3','f2','h253l','hzu','h223g','h223h']
    doc.update(declarations=closure(doc,roots),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not set(MEANINGS)&set(old.entries)
    doc=parse(format_graph(doc,'compact')+definitions())
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    basis=dict(status='personal_judgments_and_insights_offered_for_public_review_partial',document=LIBRARY,
        primitives=prims,definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
