"""Compose support for the antecedent liberties apart from princely merit."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_clerical_duty_scope import quantify

PARENT='data/public-offers-sentence-basis-v1.json'
LIBRARY='examples/v016/freedom-ethos.noema';BASIS='data/freedom-ethos-basis-v1.json'
CONTENT='i c[e]'
NAMES=('ruler','rulingoffice','community','group','topic')
PRIMITIVES={
 'h26pg':('[a '+CONTENT+' d] c',['holder','content','point'],
   '本人が、段階2の閉じた内容の実現を肯定的に受け入れ、望ましいあり方として支持する態度を保持する。idやh26ntの好ましい受容を、本人の状態だけに限定しない命題内容へ用いる。対象内容が現実に成立しているという信念、客観的な善、実際の発話・実行・介入、常時の感情喚起とは区別する。引用の同じ真理値だけで別の内容を同一視せず、睡眠など一時的に意識しないことだけで態度の消滅としない。')}
MEANINGS={
 'r55w':'同じ統治者・統治職・共同体がr5xhを満たし、固定集団の成員が同じ職・共同体の下にある人々と正確に一致する。全人への量化で範囲の不足と混入を拒否し、本文第一文の君主の自己報告・名称拒否・功績は条件にしない。',
 'r55x':'同じ統治職・共同体の下にある全ての敬意に値する聖職者の人物・職・教会・信条・主題・学識者の組について、同じr55cの全発表候補への自由と義務の非免除・共充足を要求する。r55dの君主の特別な限定を外し、自由の内容自体を保持する。',
 'r55y':'同じ統治職・共同体の下にある人々からr55jの先行聖職者群を除き、全ての残る人について、同じ学識者の全公的提示が全職務に制限されないr55hを前件、同じ全候補への自由r55iを帰結にする。',
 'r55z':'同じ君主・職・共同体・対象集団・宗教主題・固定基準の下で、r55wの正確な範囲、r5v7の全宗教的自己選択の自由、r55xとr55yの公的提示の自由を結ぶ状態内容。君主の功績や自己報告とは分けた、先行する自由の具体的なあり方である。',
 'r552':'五対象と固定基準の閉じた呼称をr55zへ適用して得る段階2の状態内容記述。態度の成立点とは別に対象の解釈基準を固定し、自由の実現を構築時に実行しない。',
 'r553':'同じ五対象と固定基準について、各呼称の指示先を脱引用して元の対象と照合する。集団・主題・統治者の呼称の食い違いを、単に自由に賛同しない事例へ隠さない。',
 'r554':'同じ本人が人であり、同じ五対象と基準の呼称を確認した上で、そのr55zの自由のあり方を好ましく受け入れ支持する態度h26pgを持つ。本人だけの利益、現在の自由の実現、内容の真理を信じること、実際の発表と同一視しない。',
 'r555':'同じ統治者・職・共同体・集団・宗教主題・基準を固定したr554の人物性質。保持者と評価点を変えても同じ自由内容を態度の対象として保つ。第三文のGeistをこのような態度の共有として読むための内容であり、伝播や海外への到達は別に接続する。',
}
LIMITS=[
 'u0015第三文[890,1049)のDieser Geist der Freiheitの内容依存群。自由の精神を、先行二文で述べられた宗教的自己選択と公的提示の自由のあり方を肯定的に支持する、共有され得る態度として読む。単なる一回の感情や自分だけの許可、自由の現在の実現とは分ける。原文の唯一の語義とする主張ではない。',
 '態度の対象は先行二文の自由の型を、明示した君主・職・共同体・全対象集団・宗教主題・基準へ具体化した内容である。君主の自己報告・寛容という名称への評価・功績を自由自体の必要条件にしない。r5xhの君主的統治職は先行例の設定として残り、これを一般の政府組織の定義とはしない。',
 '人物の立場・公的提示・職務義務・見解と信条の比較・全候補量化は既存定義と意味規約を保つ。敬意に値する聖職者の限定的読解と、他者をその群の外とする読解も保持する。公的提示の規範出所h247bは同じ基準の供給を引き継ぎ、異なる政府の規範を無条件に同じ出所へ同定しない。',
 '保持者の態度を判定する際に、引用した政府の実在・自由・義務・発表内容を実行しない。態度の内容を評価するときには範囲や規範の各条件を別に実行する。態度と認識・客観的正当性を分ける。',
 '国外への広がりでは、態度の対象となる先行の自由の例と、態度を持つ人がいる統治圏とを分ける。国外の人による支持から、国外の政府が君主であることや既に同じ自由を実現したことを導かない。この例を支持することと自由一般への志向の関係、実際の共有・取得・継続とその影響経路、外的障害、政府の自己誤解、auch/selbst、全文帰属は未接続。',
 '全列・全内容の有限評価を行わず、量化と既存の深い内容の接続は検査境界を明示する。本文114主張・17全単位判断・二文763文字を保存し、第三文の確認文字数は加算しない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def named(n):return 'k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']'
def names():return ' '.join('v '+n for n in NAMES)
def definitions():
    member='k h246c[v group v person v reference]'
    under=both('k aa[v person]','k h26hi[v person v rulingoffice v community v anchor]')
    text='d r55w[ruler a rulingoffice a community a group a reference d anchor d] c['+both(
        'k r5xh[v ruler v rulingoffice v community v anchor]',
        'f person a[e['+member+']['+under+']]')+'].\n'
    clerics=('person','office','church','creed','subject','scholar')
    scope=both('k h26hi[v person v rulingoffice v community v anchor]',
        'k r54y[v person v office v church v creed v subject v scholar v reference v anchor]')
    comp='k r546['+' '.join(named(n) for n in ('church','creed','subject','reference'))+']'
    valid=both(*('e[s['+named(n)+']][v '+n+']' for n in ('church','creed','subject','reference')))
    freedom='k r55c[v person v office v church v creed v subject v scholar v reference v anchor '+comp+']'
    text+='d r55x[rulingoffice a community a reference d anchor d] c['+quantify([(n,'a') for n in clerics],
        'y['+scope+']['+both(valid,freedom)+']')+'].\n'
    scholar='k h247d[v person v reference]'
    other=both(under,'u[k r55j[v person v reference v anchor]]',
        'k r55h[v person '+scholar+' v reference v anchor]')
    text+='d r55y[rulingoffice a community a reference d anchor d] c[f person a[y['+other+'][k r55i[v person '+scholar+' v reference v anchor]]]].\n'
    fields=' '.join(n+' a' for n in NAMES)+' reference d'
    text+='d r55z['+fields+'] e[b point['+both(
        'k r55w[v ruler v rulingoffice v community v group v reference v point]',
        't[k r5v7[v ruler v group v community v topic v reference]][v point]',
        'k r55x[v rulingoffice v community v reference v point]',
        'k r55y[v rulingoffice v community v reference v point]')+']].\n'
    text+='d r552['+' '.join(n+' i[a]' for n in NAMES)+' reference i[d]] '+CONTENT+'[o a[r c[p r55z]]['+names()+' v reference]].\n'
    valid=both(*('e[s['+named(n)+']][v '+n+']' for n in (*NAMES,'reference')))
    text+='d r553['+fields+'] c['+valid+'].\n'
    code='k r552['+' '.join(named(n) for n in (*NAMES,'reference'))+']'
    text+='d r554[holder a '+fields+' point d] c['+both('k aa[v holder]',
        'k r553['+names()+' v reference]','k h26pg[v holder '+code+' v point]')+'].\n'
    text+='d r555['+fields+'] h[a] e[i[holder a][b point[k r554[v holder '+names()+' v reference v point]]]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,
        ['r5xh','h246c','h26hi','aa','r54y','r546','r55c','r55j','r55h','r55i','h247d','r5v7','h223g','h223h']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='religious_and_public_liberty_as_shared_attitude_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
