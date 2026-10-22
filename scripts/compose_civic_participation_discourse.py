"""Keep universal criticism, clerical focus and optional partial participation distinct."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_institutional_criticism import NAMES as CRITICS

PARENTS=('data/legislative-touchstone-basis-v1.json','data/institutional-criticism-basis-v1.json','data/protective-petition-basis-v1.json')
LIBRARY='examples/v016/civic-participation-discourse.noema'
BASIS='data/civic-participation-discourse-basis-v1.json'
FAMILY='i b[h[j[a] d d d] e]'
CONTEXT='reference d candidate d anchor d'
CONTEXT_ARGS='v reference v candidate v anchor'
PETITION=('group','community','recipient','policy')
PRIMITIVES={
 'h26d5':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['node','author','whole','general','scope','focus','claim','context'],
   '著者が同じ全体内容の指定箇所で、一般内容を維持したまま、その候補範囲のうち焦点条件を満たす対象について同じ主張を特に取り立てる。四つの閉じた内容族には同じ順序の対象列・基準・候補経過・基準点を渡す。焦点によって一般内容の対象範囲を縮めず、焦点対象の唯一性・数値的な優先順位・存在・現実の主張内容の成立を追加しない。一般内容・範囲・焦点・主張は別に構成する。'),
 'h26d6':('[a a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['author','described_node','explaining_node','whole','scope','described','explaining','context'],
   '著者が同じ全体内容と候補範囲で、指定箇所の特徴を、続く指定箇所に示したより具体的な様態によって説明する。三つの閉じた内容族には同じ対象列・基準・候補経過・基準点を渡す。単に二つの性質が同時に成立することと区別し、全場面での両性質の同義性・因果法則・実際の行為や内容の真理を追加しない。説明の向きと同じ対象への対応を保つ。'),
 'h26d7':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['node','author','whole','scope','claim','concessive_condition','context'],
   '著者が同じ全体内容の中で、指定範囲についての同じ主張を、譲歩条件の場合にも排除されないものとして提示する。三つの閉じた内容族へ同じ対象列・基準・候補経過・基準点を渡す。譲歩条件を主張の必須条件にはせず、反対条件の場合の主張も排除しない。譲歩だけから全ての該当対象で主張が成立すること、実際の譲歩条件や成功例の存在は導かない。他の条件は全体内容に保持する。'),
}
MEANINGS={
 'r5gy':'共同体・制度・本人・作成・提出・学識者の立場・所見・公衆・領域の正確な九対象列を、同じ基準・候補・基準点のr5e5の批評候補へ結ぶ。許可や既実行を候補範囲の条件にしない。',
 'r5gz':'r5gyと同じ九対象の候補で、その同じ本人が同じ基準点にspの任用と宗教上の職務を備える聖職者である焦点条件。単なる自己申告や学識者の立場と同一視せず、前段の教理問答の生徒・信条・教示活動をこの候補に加えない。',
 'r5g2':'同じ九対象列・基準・候補・基準点でr5e6の所見作成・提出・両方への衝突のない許可を返す。聖職者かどうかを許可の必要条件にせず、候補の分類はr5gyで別に保持する。',
 'r5g3':'同じ九対象列の本人・作成活動・学識者の立場にr2ziの公的理性使用の分類があり、その同じ作成活動が同じ公衆を本来の宛先ccとする特徴。実際の発言や読者全員の受領を要求しない。',
 'r5g4':'同じ九対象列の本人が同じ所見の作成主体h243yであり、同じ提出活動と学識者の立場によって同じ所見を同じ公衆へ書面で提供する候補r3z/h243zという特徴。公衆や作品を別の候補に置き換えず、現実の刊行は要求しない。',
 'r5g5':'同じ九対象列から共同体・制度を取り、その同じ候補の基準点でr5faの全市民への批評の自由を要求する。注目される本人以外の市民も量化し、聖職者だけが自由なら成立するという条件へ縮めない。',
 'r5g6':'提案集団・政治的共同体・宛先・政策の正確な四対象列について、同じ基準・候補・基準点にr5fwの二人以上の全成員が市民である集団条件を返す。集団が全市民か一部かによって排除しない。',
 'r5g7':'同じ四対象のr5fwの提案集団に、同じ共同体・基準・候補・基準点の少なくとも一人の人間の市民が含まれないという非全員条件。別時点や別共同体の非成員で代用しない。譲歩の描写側に用い、共同提案可能性へ連言しない。',
 'r5ha':'同じ四対象のr5fwの提案集団に、同じ基準点の全市民が含まれるという全員条件。r5g7の対照として明示し、非全員の譲歩が全員参加を禁止する読みでないことを検査する。',
 'r5hb':'同じ四対象列・基準・候補・基準点のr5gkの保護・非妨害を内容とする共同提案可能性。非全員条件r5g7や全員条件r5haを追加せず、同じ政策内容の引用と宛先を保持する。',
 'r5hc':'同じ著者・全体内容・文脈について、全市民への自由r5g5を保持した聖職者r5gzへの取り立てと、公的使用r5g3を同じ書面提供r5g4で説明する提示を接続する。両方に同じ批評候補r5gyを使い、説明箇所の向き・順序・取り立て箇所との区別を保つ。引用した自由・職務・作成・提出は実行しない。',
 'r5hd':'同じ著者・全体内容・文脈について、集団範囲r5g6の同じ保護提案可能性r5hbを、非全員条件r5g7であっても排除しない譲歩として提示し、同じ提案箇所への括弧内補足を結ぶ。部分参加の実在・成功・必須性を断言せず、全員参加も許す。',
}
LIMITS=[
 'u0013第七文[1437,2309)のvornehmlich dem Geistlichen、öffentlich, d. i. durch Schriften、(wenn gleich nicht aller)の提示を構成する依存群。本文全体の著者帰属はまだ追加しない。',
 '全市民の批評の自由と、声を合わせて提案する集団を区別する。前者の範囲はr5faで全員のまま保ち、聖職者の焦点条件で選別しない。後者はr5fwで二人以上の同じ固定集団を扱い、非全員を必須条件にしない。',
 '聖職者は既存spの、主要な宗教上の配慮・任用・共同体の公的奉仕の職務を持つ人という読みを再利用する。第五段落の特定の教示事例r35tを丸ごと転用して、生徒・信条・その教示条件まで付け足さない。市民資格と聖職者性は同じ人・基準点に別々に結ぶ。',
 '公的使用と書面提供はr5e5が既に同じ本人・活動・所見・公衆へ結んでいる。その二つの特徴を内容族として分け、d. i.の説明方向も保持する。あらゆる書面が公的使用である、あらゆる公的使用が書面だけであるという無限定の同値へ一般化しない。',
 '譲歩は、全員の声がそろうことを提案可能性の必要条件としない提示として読む。部分集団なら必ず提案できる、実際に不参加者がいる、全員参加は禁止される、という主張にはしない。利用可能な方法・同じ内容の共同支持・公的な宛先などの他の条件はr5gkに残る。',
 '提示関係は任意の同型の閉じた内容族に適用できる。引用した内容や対象の存在・真理を基本関係が一括して返すものではなく、候補・焦点・自由・集団範囲・提案内容はそれぞれ既存定義から構成する。型は段階1へそろえ、九対象と四対象の列はそれぞれ厳密に束縛する。',
 '全文の量化、保護目的um、etwaと接続法、王座の換喩、Nun・wohl・gleichsam、前文との照応、同じ全体内容への適用と通読は残る。第七文の確認文字数は加算しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    critic=' '.join('v '+n for n in CRITICS)+' '+CONTEXT_ARGS
    scope='k r5e5['+critic+']'
    text=''
    for root,body in (
        ('r5gy',scope),
        ('r5gz',both(scope,'k sp[v person v anchor]')),
        ('r5g2','k r5e6['+critic+']'),
        ('r5g3',both('k r2zi[v person v making v scholar v reference]','k cc[v making v audience v reference]')),
        ('r5g4',both('k r3z[v person v presenting v scholar v notes v audience v reference]',
            'k h243y[v person v making v notes v reference]','k h243z[v presenting v notes v audience v reference]')),
        ('r5g5','k r5fa[v community v regime '+CONTEXT_ARGS+']')):
        text+='d '+root+'[bindings j[a] '+CONTEXT+'] e[b point['+bind(CRITICS,body)+']].\n'
    eligible='k r5fw[v group v community '+CONTEXT_ARGS+']'
    citizen='k h26cu[v person v community '+CONTEXT_ARGS+']'
    member='k h26db[v group v person '+CONTEXT_ARGS+']'
    partial='g person a['+both('k aa[v person]',citizen,'u['+member+']')+']'
    full='f person a[y['+citizen+']['+member+']]'
    for root,body in (('r5g6',eligible),('r5g7',both(eligible,partial)),('r5ha',both(eligible,full)),
        ('r5hb','k r5gk[v group v community v recipient v policy '+CONTEXT_ARGS+']')):
        text+='d '+root+'[bindings j[a] '+CONTEXT+'] e[b point['+bind(PETITION,body)+']].\n'
    q=lambda n:'r b[p '+n+']'
    text+='d r5hc[focusnode a publicnode a writtennode a author a whole i d[e] context d] c['+both(
        'k h26d5[v focusnode v author v whole '+q('r5g5')+' '+q('r5gy')+' '+q('r5gz')+' '+q('r5g2')+' v context]',
        'k h26d6[v author v publicnode v writtennode v whole '+q('r5gy')+' '+q('r5g3')+' '+q('r5g4')+' v context]',
        'k uf[v author v publicnode v writtennode v context]','k ue[v publicnode v writtennode v context]',
        'u[e[v focusnode][v publicnode]]','u[e[v focusnode][v writtennode]]','u[e[v publicnode][v writtennode]]')+'].\n'
    text+='d r5hd[aside a proposalnode a author a whole i d[e] context d] c['+both(
        'k h26d7[v aside v author v whole '+q('r5g6')+' '+q('r5hb')+' '+q('r5g7')+' v context]',
        'k h234k[v aside v author v proposalnode v context]','u[e[v aside][v proposalnode]]')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['sp','uf','ue','h234k'],['r5e5','r5e6','r5fa'],['r5fw','r5gk'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='civic_freedom_focus_explanation_and_participation_concession',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
