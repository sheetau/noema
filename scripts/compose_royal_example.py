"""A realized legislative example, shared regard, and no superior monarch yet."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_legislative_safety_insight import FIELDS,ARGS

PARENT='data/religious-emphasis-sentence-basis-v1.json';DEPENDENCY='data/enlightened-thinking-basis-v1.json'
LIBRARY='examples/v016/royal-example.noema';BASIS='data/royal-example-basis-v1.json'
FRAME=FIELDS+' manner a topic a';FARGS=ARGS+' v manner v topic'
NAMES=('ruler','community','group','reference','history','anchor','manner','topic')
DATES=('reference','history','anchor')
CONTENT='i e[e]';SCHEMA='i e[h[a a a d d d a a] e]'
PRIMITIVES={
 'h26t4':('[a '+CONTENT+' d d] c',['example','instance_content','instance','reference'],
   'この例が指す具体的な配置・経過は、固定基準の下でこの点に現実化した、指定された閉じた段階4内容の事例である。h26qwの具体的実例関係を高い段階へ保つ。例は配置を指す対象で、人や発話箇所そのものではない。同時に別の内容が成立するだけ、想像例だけでは満たさず、同じ内容の成立を合成側でも検査する。'),
 'h26t5':('[a '+CONTENT+' a d d] c',['example','content','public','reference','assessment'],
   'この同じ具体例は、指定された内容を例示するものとして、同じ公衆と固定評価基準にとって際立って優れ、内容の特徴が鮮明に示される例である。肯定的な例の評価であり、単なる存在や平均的な一例、物理的な発光、対象人物の全人格の完全性とは区別する。例の現実性・同じ内容・公衆への利用可能性は別に要求する。唯一の最良例や、そこから全事例への演繹的証明は含意しない。'),
 'h26t6':('[a a d d] c',['example','public','reference','assessment'],
   '同じ人間公衆にとって、この具体例の情報がこの評価点で共有可能な経験・報告・公開情報として利用できる。物としての所有、全構成員の直接目撃や現実の注意・同意、世界のどこかに情報があるだけとは区別する。公衆の範囲と例の実在は合成側で確認する。'),
 'h26t7':('[a d '+SCHEMA+' d d] c',['person','point','pattern','reference','assessment'],
   '同じ比較基準・評価時までの君主について、この人物のこの点の実践が、指定された閉じた内容型の実例としてどこまで進んでいるかを比較する評価がそろっている。内容型の人物・共同体・臣民・解釈基準・履歴・起点・思考態度・主題の八役割を、各君主のその時点の固有の設定へ適切に具体化して比較する。他国を基準君主の国へ同一化せず、現代の基準点を歴史的な点へ流用しない。良い例だけの選別、無記録を低評価で補うこと、内容の完全実現は含意しない。'),
 'h26ua':('[a d a d '+SCHEMA+' d] c',['left','left_point','right','right_point','pattern','reference'],
   '同じ固定基準と同じ閉じた内容型の下で、左の人物の指定点の実践は、右の人物の指定点の実践より、その型を具体化する例として進んでいる。厳密な質的優越で、同等の場合・比較不能の場合は優越としない。双方の国・臣民・法・基準点等は各々の設定へ内容型を具体化して保つ。単に年代が早いこと、軍事力・国土・人気一般、相手への敬意、数値の差を尺度に替えない。厳密な優越の意味規約を持ち、未評価は偽で補わない。'),
}
MEANINGS={
 'r6d4':'同じ八設定の啓蒙支持・思考態度と安全性への洞察r6d2に、同じ六設定の全臣民三対象への許可方針r6dkの現実の成立を結ぶ。実例側の内容であり、一般的な洞察だけから政策の実施を推論しない。',
 'r6d5':'同じ八対象の閉じた呼称をr6d4へ適用し、実例が具体化する段階4の閉じた内容を作る。呼称確認は使用側で行い、引用構築時に政策や思考を実行しない。',
 'r6d6':'同じ具体例と閉じた段階4内容の現実化h26t4に、同じ事例点でその内容が成立することを要求する。別の内容が真なだけの例や架空例を実例として認めない。',
 'r6d7':'非空の厳密な全順序履歴で基準点までの全候補人物・時点の評価を要求し、その範囲の誰も指定人物の指定点を厳密に上回らない。指定人物・点自身も範囲に含み、指定点は基準点以前である。同等・比較不能を上回ったことへ変えず、時間的に最初の実現を要求しない。',
 'r6ea':'同じ解釈基準・履歴・現在評価までの、いずれかの共同体で君主であった全人物・時点をr6d7へ渡す。比較は共通r6d4の八引数内容型の具体化について行い、他国の君主や過去の例を省かない。将来の人物・時点は今回のまだ誰もという範囲の外である。',
 'r6eb':'相手を人として捉える性質。敬意の対象記述に用い、功績、政治上の全面的賛同、恩恵への感謝を人であることへ混ぜない。',
 'r6ec':'著者を含む同じ非空の人間公衆の全構成員が、同じ相手を人として肯定的に受け止め価値を認め敬意を保つh26nu。wirの指定範囲についての読みであり、全世界の人々や全臣民へ無断で拡張しない。敬意の客観的な正当性や発話行為を必須にしない。',
 'r6ed':'同じ国家元首と八設定の現実の実例、同じ公衆への利用可能性と際立つ例としての評価、公衆の同じ君主への敬意、同じ内容型について評価時まで上回る君主がいないことを結ぶ。実例の現在点と方針の起点を同じanchorに置き、別の王の例・敬意・比較結果を寄せ集めない。',
}
LIMITS=[
 'u0016第二文後半davon wir ein glänzendes Beispiel haben, wodurch noch kein Monarch demjenigen vorging, welchen wir verehrenを扱う。davonは立法にも及ぶ先行の思考態度・安全性の認識・許可のあり方を受け、実例では同じ許可方針が実際に成立する読みを採る。一般条件の全対象者へ現実の政策成立を追加するのではない。',
 'vorgingは、この点で他の君主が上回ったという質的比較の読みを採る。Adelung Vorgehen 1(1)は優越の比喩用法を記し、1(3)には先に模範を示す用法もある。文脈のglänzendes Beispielとwodurchを、同じ実践の例としての比較へ結ぶ。時間的に初めての達成、他の君主が同じ方針を持った例の不存在、唯一の最大を述べる読みにはしない。旧引継ぎの先行者不在という仮見出しをこの採用解釈で具体化する。',
 'nochは本文現在までを上限とする。過去と現在の全関連君主を各時点の共同体と役割で扱い、将来の優越例までは否定しない。同等の先行例は許し、評価不足や未知を上回る者なしへ変えない。比較不能もあり得る質的な厳密優越であり、全候補の全順序的順位や数値尺度は仮定しない。',
 '比較対象には実現済みの良い例だけを選ばず、その時点に君主である全人物を入れる。共通の八引数内容型は各人の国・臣民・法・歴史的な設定へ具体化して比較する。全君主を同じ国又は同じ現在の役職へ置換しない。比較評価の現実的な妥当性と完全性は解釈入力である。',
 'glänzendは肯定的に際立ち、内容を鮮明に示す例としての評価。物理的な光、全人格の完全性、例からの普遍命題の演繹にはしない。wir habenは指定公衆に利用可能な例があることと読み、所有や全員の直接目撃にしない。',
 'wir verehrenは著者を含む指定公衆が同じ君主への敬意を保持する読み。既存h26nuを再利用し、本人の客観的な徳、感謝の具体的な恩恵、服従又は賞賛の現実の発話を補わない。この公衆を世界中の全人間又は全臣民と同一視しない。',
 '原文には国名・具体的な日付を補わない。先行のフリードリヒへの談話上の対応、一般化の範囲、davon/wodurch/welchenの原文箇所への照応、Aber/noch/selbst/sogar、全文帰属と通読は後で結ぶ。これは依存群であり、新しい意味確認文字数を加算しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def named(n):return 'k '+('h223h' if n in DATES else 'h223g')+'[v '+n+']'
def definitions():
    text='d r6d4['+FRAME+'] e[b point['+both('t[k r6d2['+FARGS+']][v point]','t[k r6dk['+ARGS+']][v point]')+']].\n'
    text+='d r6d5['+' '.join(n+' i['+('d' if n in DATES else 'a')+']' for n in NAMES)+'] '+CONTENT+'[o a[r e[p r6d4]]['+FARGS+']].\n'
    text+='d r6d6[example a content '+CONTENT+' instance d reference d] c['+both('k h26t4[v example v content v instance v reference]','t[s[v content]][v instance]')+'].\n'
    le=lambda t:'x[e[v '+t+'][v anchor]][c[v before][v '+t+' v anchor]]'
    selected=both('c[v history][v when]',le('when'),'c[v candidates][v other v when]')
    text+='d r6d7[history h[d] c before h[d d] c candidates h[a d] c assessed h[a d] c better h[a d a d] c person a point d anchor d] c['+both(
        'k ta[v history v before]','c[v history][v point]','c[v history][v anchor]',le('point'),'c[v candidates][v person v point]',
        'f other a[f when d[y['+selected+']['+both('c[v assessed][v other v when]','u[c[v better][v other v when v person v point]]')+']]]')+'].\n'
    hist='i[at d][k h257z[v reference v history v at]]';order='i[first d last d][k ic[v first v last v history]]'
    scope='i[person a at d]['+both('k aa[v person]','g community a[k r2uj[v person v community v at]]')+']'
    assessed='i[person a at d][k h26t7[v person v at r e[p r6d4] v reference v assessment]]'
    better='i[left a first d right a last d][k h26ua[v left v first v right v last r e[p r6d4] v reference]]'
    text+='d r6ea[ruler a reference d history d instance d assessment d] c[k r6d7['+' '.join((hist,order,scope,assessed,better))+' v ruler v instance v assessment]].\n'
    text+='d r6eb[person a] e[b point[k aa[v person]]].\n'
    text+='d r6ec[author a public a ruler a reference d point d] c['+both('k r5ty[v public v reference]','k aa[v ruler]',
        'k h246c[v public v author v reference]',
        'f person a[y[k h246c[v public v person v reference]][k h26nu[v person v ruler r b[p r6eb] v point]]]')+'].\n'
    code='k r6d5['+' '.join(named(n) for n in NAMES)+']'
    text+='d r6ed[example a author a public a '+FRAME+' assessment d] c['+both(
        *('e[s['+named(n)+']][v '+n+']' for n in NAMES),
        'k r6d6[v example '+code+' v anchor v reference]',
        'k h26t6[v example v public v reference v assessment]',
        'k h26t5[v example '+code+' v public v reference v assessment]',
        'k r6ec[v author v public v ruler v reference v assessment]',
        'k r6ea[v ruler v reference v history v anchor v assessment]')+'].\n'
    return text
def build():
    sources=(parent(),dependency());roots=(('h26nu','r5ty','h246c','aa','ta','h257z','ic'),('r6d2','r6dk','r2uj','h223g','h223h'))
    doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,rs in zip(sources,roots):
        for d in closure(source.document,rs):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(s.source_sha256 for s in sources))
    basis=dict(status='realized_royal_example_and_as_of_no_superior_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
