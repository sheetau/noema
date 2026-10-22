"""Compose emphatic positive expression and two scoped deserved responses."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import FIELDS as PRINCE,ARGS as PARGS

PARENTS=('data/prince-conclusion-basis-v1.json','data/kant-deserved-responses-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/merit-praise.noema';BASIS='data/merit-praise-basis-v1.json'
GROUND='i[h[a] e]';GROUND_NAME='i['+GROUND+']';MESSAGE='i[h[a] f]'
RESPONSE='i[h[a a a] e]';STANDARD='h[a '+RESPONSE+' '+GROUND+'] e'
SCOPE='group a epoch a hearers a reference d candidate d ground '+GROUND
SARGS='v group v epoch v hearers v reference v candidate v ground'
NAMES=('group','epoch','hearers','reference','candidate')
NAME_FIELDS='group i[a] epoch i[a] hearers i[a] reference i[d] candidate i[d] ground '+GROUND_NAME
NAME_ARGS=' '.join('k '+('h223h' if n in ('reference','candidate') else 'h223g')+'[v '+n+']' for n in NAMES)+' o r[v ground]'
MERIT='firstgroup a lastgroup a firstepoch a lastepoch a hearers a candidate d ground '+GROUND+' firststandards j['+STANDARD+'] laststandards j['+STANDARD+']'
MARGS='v firstgroup v lastgroup v firstepoch v lastepoch v hearers v candidate v ground v firststandards v laststandards'
PRIMITIVES={
 'h26nr':('[a a a '+GROUND+' d] c',['speaker','activity','subject','aspect','point'],
   '同じ伝達行為において、話者が対象者を指定された閉じた性質記述の下で捉え、その対象者への肯定的な評価を自分の表明する立場として示す。性質が成立するという事実の報告、他人の評価の引用、反語としての距離だけとは分ける。内心の真摯さや対象の実際の功績、受け手の同意や評価の上昇は含意しない。性質を正しく又は誤って対象へ帰属する内容は別に伝達する。'),
 'h26ns':('[a a a '+GROUND+' d d] c',['speaker','activity','subject','aspect','reference','point'],
   '同じ話者・伝達行為・対象者・性質記述について表明された肯定的評価が、固定した比較基準において、通常の単なる肯定を越える高い程度にある。h26nrとともに用いる評価表明の程度関係。音量や文字数、最大性、他の全対象より優れること、数値尺度、誇張による虚偽、内心の感情の強さとは同一視しない。比較基準は表明の結果から都合よく選び直さない。'),
}
MEANINGS={
 'r5x4':'指定した功績等の人物性質の閉じた記述をro7へ構文的に適用し、同じ対象者がその性質を持つと主張する発話の記述を作る。構築時に功績を真にせず、別の性質の主張へ置き換えない。',
 'r5x5':'同じ話者・伝達行為・対象者・点で、非空の全受け手に同じ性質についての発話を提示し、その性質の下で対象者への肯定的評価を高い程度で表明する。単なる肯定的報告、他人の言葉の引用、反語の距離だけ、弱い賛同と区別する。内心の真摯さや性質の真理は別である。',
 'r5x6':'r5x5の同じ応答者・行為・対象者を、固定集団の成員と同じ時代内の評価点へ限定する。聴衆と応答者集団を取り違えず、後代の応答を現在時代内の行為として扱わない。',
 'r5x7':'集団・時代・聴衆・固定基準・履歴候補と功績記述そのものの閉じた名前をr5x6へ適用する段階0の応答記述。功績はここでは実行されず引用として保持されるため、記述内の引用を保ったまま段階0で構成できる。未来の発話や功績を構築時に実行しない。',
 'r5ya':'応答記述へ渡す三個体・二状況の閉じた呼称を脱引用して元の設定へ照合する。別集団・時代・聴衆の記述を黙って渡さない。功績記述自体の引用名はr5ybで同じ値をo rにより構成する。',
 'r5yb':'r5yaの全参照照合の下で、同じ集団・時代・聴衆・功績によるr5x7の称揚応答に既存ro5の値する評価を接続する人物性質。功績記述そのものの引用はo rで同じ記述から作り、別の名付け関係に委ねない。真の功績と非空の全適用基準を要求し、応答の実行や義務は要求しない。',
 'r5yc':'異なる二つの集団と時代について、同じ対象者・功績・聴衆・基準・候補履歴で、双方のr5ybがともに成立する人物性質。一方だけの適合や両者を混ぜた一つの応答を代わりにしない。二つの全基準は各範囲に明示する。',
 'r5yd':'同じ人物・点のr5xvの宗教的判断の到達状態とr5ycの両範囲からの称揚に値する評価を連言する。人物・点を分けず、称揚や感謝の実際の発生を付加しない。',
 'r5ye':'r5xjの同じ君主の条件を満たす者へr5ydの結論を適用する一般条件。前件の品位判断・名称拒否を保持し、君主の存在又は実際の自由政策を追加しない。',
}
LIMITS=[
 'u0015第一文のvon der dankbaren Welt und Nachwelt als derjenige gepriesen zu werdenに向け、称揚の応答を肯定的事実報告から区別し、両範囲からの適合を連言する。dankbarenの感謝と、derjenige以下の具体的な功績はまだ入力に残る。',
 'preisenは、対象を同じ功績・性質の下で高く評価することを表明する読みとする。DWBの第一のpreisenの語義2と人をals等で形容して称える用例を補助とする。価格を定める語義、実際に他人の評価が高まったという因果、神への礼拝に限定しない。',
 '発話内容の帰属、肯定的評価の表明、その高い程度を分ける。真摯さが欠けるお世辞も表明としては記述でき、表明された評価自体へ批判的に距離を置く反語とは区別する。これを称賛のあらゆる文化的用法や暗黙の称賛の唯一の定義にはしない。',
 'als derjenige以下の功績は対象者を引数に取る同じ閉じたNoema性質記述で伝達する。発話の記述だけではその功績を真にせず、値する評価では同じ功績の実際の成立を別に要求する。',
 '功績記述は表明関係へそのまま渡し、その内容を応答の中では脱引用して実行しない。o rによる記述自体の引用とo aによる構文適用は段階0を保てるため、既存ro5を変更せず再利用する。真の功績の要求はro5側で保持し、新しい基本関係をverdientの一語判定器にはしない。',
 '世界と後代の双方からの適合はr5ycの連言で保持し、旧hzgjの選言で片側だけを認めない。全員の実際の発話、未来の必然、両側同時の発生、集団代表の資格は補わない。集団の人間範囲・完全性と時代の順序の本文束縛はまだ別に要る。',
 'dankbarの人格的な用法と行動による表出の違いをDWBで確認した。感謝を発話の実演だけにせず、同じ行為者への恩恵認識と好意的な承認を含む態度として次に構成する。現在保存した辞書だけで、その態度や後代の全員について真と証明しない。',
 '最初の政府側の解放・良心事項についての各人の自由という功績、恩恵への感謝、応答適合の全基準と二つの集団・時代の本文束縛、名称評価の著者帰属、sondern、一文全体と後続は未完。本文112主張と17単位判断を維持する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5x4[ground '+GROUND+'] '+MESSAGE+'[o a[r[p ro7]][v ground]].\n'
    speech='t[c[k hzgb[v audience k r5x4[v ground]]][v speaker v activity v subject]][v point]'
    text+='d r5x5[audience h[a] c ground '+GROUND+' reference d] h[a a a] e[i[speaker a activity a subject a][b point['+both(
        'k aa[v speaker]','k aa[v subject]',speech,'k h26nr[v speaker v activity v subject v ground v point]',
        'k h26ns[v speaker v activity v subject v ground v reference v point]')+']]].\n'
    hearers='i[recipient a][k h246c[v hearers v recipient v reference]]'
    response='t[c[k r5x5['+hearers+' v ground v reference]][v speaker v activity v subject]][v point]'
    text+='d r5x6['+SCOPE+'] h[a a a] e[i[speaker a activity a subject a][b point['+both(
        'k h246c[v group v speaker v reference]','k h26ab[v epoch v reference v candidate v point]',response)+']]].\n'
    text+='d r5x7['+NAME_FIELDS+'] '+RESPONSE+'[o a[r[p r5x6]][v group v epoch v hearers v reference v candidate v ground]].\n'
    valid=['e[s[k '+('h223h' if n in ('reference','candidate') else 'h223g')+'[v '+n+']]][v '+n+']' for n in NAMES]
    text+='d r5ya['+SCOPE+'] c['+both(*valid)+'].\n'
    text+='d r5yb['+SCOPE+' standards j['+STANDARD+']] h[a] e[i[subject a][b point['+both(
        'k r5ya['+SARGS+']','t[k ro5[v subject k r5x7['+NAME_ARGS+'] v ground v standards]][v point]')+']]].\n'
    def side(which):return 't[c[k r5yb[v '+which+'group v '+which+'epoch v hearers v reference v candidate v ground v '+which+'standards]][v subject]][v point]'
    text+='d r5yc[reference d '+MERIT+'] h[a] e[i[subject a][b point['+both('u[e[v firstgroup][v lastgroup]]','u[e[v firstepoch][v lastepoch]]',side('first'),side('last'))+']]].\n'
    text+='d r5yd[topic a reference d '+MERIT+'] h[a] e[i[subject a][b point['+both(
        't[c[k r5xv[v topic v reference]][v subject]][v point]',
        't[c[k r5yc[v reference '+MARGS+']][v subject]][v point]')+']]].\n'
    text+='d r5ye['+PRINCE+' '+MERIT+'] e[k r5xk['+PARGS+' k r5yd[v topic v reference '+MARGS+']]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5xv','r5xk','h223g','h223h','ro5'],['ro7','hzgb'],['aa','h246c','h26ab'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='emphatic_positive_response_and_two_scoped_merit_evaluations',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
