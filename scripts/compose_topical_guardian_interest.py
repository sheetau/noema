"""Separate interest in topical guardianship from actually exercising it."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/self-departure-sentence-basis-v1.json'
LIBRARY='examples/v016/topical-guardian-interest.noema';BASIS='data/topical-guardian-interest-basis-v1.json'
PRIMITIVES={
 'h26r5':('[a d] c',['topic','reference'],
   '同じ基準において、この領域は習得した技法・熟練を用いて制作・表現・実践を行い、そのあり方や出来栄えを吟味する技芸に関わる。ここでKünsteを美術だけに限定せず、工芸や諸技術の実践も含む広い技芸領域として読む。特定作品の美、作り手の技能、現在の制作の成功、科学との排他的な境界は要求しない。'),
 'h26r6':('[a d] c',['topic','reference'],
   '同じ基準において、この領域は事柄について体系的な認識を得て、理由・方法・関連付けを検討し伝える学問的探究に関わる。ここでWissenschaftenを自然科学だけに限定せず、学問諸分野の広い領域として読む。現代の特定の学部区分、全学説の真理、専門職資格、宗教的対象の全面排除は要求しない。'),
 'h26r7':('[a a a a d d] c',['activity','actor','target','matter','reference','point'],
   '同じ活動で同じ行為者が同じ対象者の判断・行為を指図する立場を引き受け又は称する、その担当内容に、この固定基準の事柄についての判断・指示が含まれる。活動が別途その話題にも触れるだけ、別対象への別の指図の担当、単に職名を持つこととは分ける。引受け・自称そのもの、行為の生起・参加・人であることは別に構成する。合法的な権限、実際の服従、相手の能力不足は含意しない。'),
 'h26sa':('[a i[e] d d] c',['person','target','reference','point'],
   '同じ人がこの点で、同じ固定基準の閉じた内容が表す行為・立場の実現へ向けて、関与する理由となる利害や動機を持ち、そこに積極的な関心を向けている。内容を真だと信じること、単に話題を知る又は好奇心を持つこと、職務の所管、規範上の義務、行為の実行・成功とは分ける。Interesseをこの実践的な関心として読む一般関係で、内容の未来の真理や実現可能性は関心の有無を述べる際に実行しない。'),
}
MEANINGS={
 'r6bj':'同じ異なる二人について、一つの活動が生起し当人が参加し、その活動で相手への指図の立場を引き受け又は称するob。担当内容h26r7の同じ事柄がh255iにより同じ主題に属する。地位や職名だけ、別活動・別相手・無関係な話題を混ぜない。',
 'r6bk':'同じ人が、固定した対象集団の少なくとも一成員について、同じ主題のr6bjを行うという内容。集団全員への一斉の行為や、法律上の後見資格を要求しない。関心の対象として引用し、関心の外で実際の後見行為を断言しない。',
 'r6bl':'当人・対象集団・主題・固定基準の四つの閉じた呼称をr6bkへ構文的に適用し、同じ後見活動の内容を閉じる。本人・対象・主題を未充足の引数へ残さず、構築時に内容の真理を実行しない。',
 'r6bm':'同じ人と非空の人間集団について、当人・集団・主題・基準の呼称の参照一致を検査し、同じr6blの内容へのh26saの関心を否定する。実際の不実行、動機の不明、別主題への無関心から代用しない。',
 'r6bn':'技芸領域h26r5と学問領域h26r6を別々に指定し、同じ人・集団・基準・評価点でそれぞれへのr6bmを要求する。一方への無関心だけをundの全体にしない。領域の対象事項の重なりは許し、全関心一般の不在へ広げない。',
 'r6bo':'固定基準の同じ非空の人間集団の成員が、全個体について、同じ統治者・共同体の臣民r5niと過不足なく一致する。その統治者自身が同じ共同体の君主r2ujであることも要求する。実際に後見される臣民だけや別の統治者の臣民へ範囲を縮めない。',
 'r6bp':'同じ統治者・共同体の全臣民であるr6boの集団と、その同じ人々について技芸・学問の後見役を演じることへの無関心r6bnを結ぶ。統治範囲は固定基準に、関心は指定評価点に置き、引用内の実行点へ臣民を都合よく選び直さない。',
}
LIMITS=[
 'u0016第一文のweil in Ansehung der Künste und Wissenschaften unsere Beherrscher kein Interesse haben, den Vormund über ihre Unterthanen zu spielenという理由内容に向けた依存群。主眼の回顧、啓蒙の説明、unsereの範囲、理由提示、追加の最上級評価、全文帰属は未接続。正本117主張と18全単位判断を保持する。',
 'Künsteは美術だけでなく技芸、Wissenschaftenは自然科学だけでなく体系的な学問の領域として読む。両者は名前ではなく意味規約を持つ主題として与え、同じ対象に関する事柄の重なりを禁止しない。',
 'Vormund spielenは対象の判断・行為を指図する立場を引き受け又は称する活動として読む。役柄の舞台演技、法律上の後見資格、相手が実際に未成熟であること、強制や服従の成功は加えない。担当する主題を同じ行為・主体・対象へ結ぶ。',
 'Interesseはその行為・立場へ関与する理由となる利害や動機を持つ実践的な関心という読み。純粋な好奇心、認識上の信念、職務の所管とは区別する。否定対象は閉じた同じ活動内容への関心であり、実際に行わないこととは同値にしない。',
 '統治者については既存r2uj/r5niの君主的統治の読みを継承する。unsere Beherrscherをどの全範囲へ結ぶかは本文で確定する。関心対象は同じ全臣民への役割で、少なくとも一人を対象とする実行を許す。一人が全臣民へ同時に行為することを関心の前提にしない。',
 '同じ人々への二つの領域の内容をそれぞれ引用して否定する。未来の行為が未知又は不成立でも現在の関心の有無は記述でき、逆に実行があっても関心がない内容を論理的に排除しない。原文の歴史的判断が真かどうかは別問題である。',
 '原刊492頁の第一文とAA VIII 41を局所照合する。固定転記のdie des Ausgangesに対しAAはd. i. des Ausgangesとする。原刊拡大ではdieと読める綴りを保持し、啓蒙を自己に帰責される未成熟からの離脱として説明する読解を本文接続で採る。誤植や編集の原因は断定しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    fields='actor a activity a target a topic a reference d point d'
    scope='g matter a['+both('k h255i[v matter v topic v reference]','k h26r7[v activity v actor v target v matter v reference v point]')+']'
    text='d r6bj['+fields+'] c['+both('k aa[v actor]','k aa[v target]','u[e[v actor][v target]]',
        'k dg[v activity v point]','k df[v actor v activity v point]','k ob[v activity v actor v target v point]',scope)+'].\n'
    text+='d r6bk[actor a group a topic a reference d] e[b point[g activity a[g target a['+both(
        'k h246c[v group v target v reference]','k r6bj[v actor v activity v target v topic v reference v point]')+']]]].\n'
    text+='d r6bl[actor i[a] group i[a] topic i[a] reference i[d]] i[e][o a[r[p r6bk]][v actor v group v topic v reference]].\n'
    names=[('actor','h223g'),('group','h223g'),('topic','h223g'),('reference','h223h')]
    named=['k '+p+'[v '+n+']' for n,p in names]
    valid=['e[s['+c+']][v '+n+']' for (n,p),c in zip(names,named)]
    text+='d r6bm[actor a group a topic a reference d point d] c['+both('k aa[v actor]','k r5ty[v group v reference]',*valid,
        'u[k h26sa[v actor k r6bl['+' '.join(named)+'] v reference v point]]')+'].\n'
    fields='actor a group a arts a sciences a reference d point d'
    text+='d r6bn['+fields+'] c['+both('k h26r5[v arts v reference]','k h26r6[v sciences v reference]',
        'k r6bm[v actor v group v arts v reference v point]','k r6bm[v actor v group v sciences v reference v point]')+'].\n'
    text+='d r6bo[actor a community a group a reference d] c['+both('k r2uj[v actor v community v reference]',
        'k r5ty[v group v reference]','f target a[z[k h246c[v group v target v reference]][k r5ni[v actor v target v community v reference]]]')+'].\n'
    text+='d r6bp[actor a community a group a arts a sciences a reference d point d] c['+both('k r6bo[v actor v community v group v reference]',
        'k r6bn[v actor v group v arts v sciences v reference v point]')+'].\n'
    return text
def build():
    old=parent();roots=('aa','dg','df','ob','h255i','h246c','r5ty','h223g','h223h','r2uj','r5ni')
    doc=deepcopy(old.document);doc.update(declarations=closure(doc,roots),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='topical_guardian_activity_and_nonfactive_practical_interest_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
