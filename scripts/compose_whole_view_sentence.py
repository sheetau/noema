"""Integrate the human-affairs course and the conditional whole-view comparison."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_prince_sentence import ANCHOR
from scripts.compose_qualified_speech_sentence import TOPIC,STANDARD,ROLE,REF as OLD_REF

PARENT='examples/v016/kant-qualified-speech-sentence.noema';PARENT_BASIS='data/qualified-speech-sentence-basis-v1.json'
DEPENDENCY='data/counterexpected-affairs-basis-v1.json'
FULL='examples/v016/kant-whole-view-sentence.noema';CORE='examples/v016/whole-view-sentence-core.noema'
BASIS='data/whole-view-sentence-basis-v1.json';ANNOTATIONS='data/whole-view-sentence-identifiers-v1.json'
PC='i b[e]';C5='i f[e]';PROFILE='i d[h[a] e]'
COURSE='k h26x3[]';ASPECT='k h26x4[]';REF='k h26x5[]';CTX='k h26x6[]';AUTHOR='k wa[]'
PRIMITIVES={
 'h26xu':('[a a d] c',['course','aspect','reference'],'同じ固定基準で、指定した人間の事柄の推移を構成する全関連側面の一つ。人の行為・判断・実践的又は制度的な条件・帰結に関わる側面を、結果の予期されやすさと独立に一定の広さで区切る。局所の成功例だけを選んだ標本ではなく、文脈上の全体の粒度と範囲を先に固定する。'),
 'h26xv':('[a a a d] c',['course','first','second','reference'],'同じ推移・固定基準で、第一側面と第二側面との間に属する関連。行為の条件や帰結、制度上の制約、時間的な展開など、採用する関連の種類を解釈入力で明らかにする。単なる同じ集合への所属とは分け、全因果の説明又は全側面間の直線的な時間順序とはしない。'),
 'h26xw':('[a d] j[a]',['course','reference'],'同じ固定基準で推移を構成するh26xuの全関連側面を一度ずつ挙げる有限列。全体としての範囲は観察者又は逆説性の結果によって変更しない。正確な全数列であることはrcmで検査する。'),
 'h26xx':('[a a d] c',['aspect','person','reference'],'この固定基準において、この側面には指定した人の行為・判断・実践的又は制度的な立場が関わるか、その帰結が及ぶ。単に同じ場所にいたことではない。人間であることはaaで別に確認する。'),
 'h26xy':('[a a a d d] c',['person','activity','course','reference','point'],'同じ固定基準・点で、この人がこの一つの考察行為において指定した推移を思考の対象とする。発話の実行、第三者の注視や身体的な見物とは分ける。行為の実際の成立と対象全体への注意は別に構成する。'),
 'h26xz':('[a a d d] c',['activity','aspect','reference','point'],'同じ考察行為・基準・点で、指定した側面を考慮に入れる。別の考察行為又は別の点での考慮によってこの行為の欠落を補わない。'),
 'h26x2':('[a a a d d] c',['activity','first','second','reference','point'],'同じ考察行為・基準・点で、指定した二側面の間の関連を関連として考慮に入れる。二側面を個別に列挙しただけとは分ける。'),
 'h26x3':('[] a',[],'第十段落第二文のGangとihn/darinが共に指す、人の行為・制度的条件・帰結に関する推移の文脈上の全体。当の政治的対比を一側面として含み、他の場合への一般的な比較もこの広い範囲で扱う。歩行や、必ず二つの現実の事件が順次起こることは意味しない。'),
 'h26x4':('[] a',[],'同じ人間の事柄の推移に属する、直前の第一文の人物条件と共和国への禁止の政治的対比という局所的側面。具体的内容はr6g3の閉じた記述への一致を本文中で要求し、逆説というラベルで済ませない。'),
 'h26x5':('[] d',[],'第十段落第二文の推移・側面の区切り・考察・標準予測・説明枠・比較と許容比率を固定する解釈基準。第一文の政治的条件の基準h26wpを変更せず、第二文の評価のための範囲と観点を追加する。'),
 'h26x6':('[] d',[],'固定原文kant-1784:u0017第二文を著者が提示する論述文脈。内容評価の本文現在と、解釈基準とは分ける。'),
 'h26x7':('[a a '+C5+' '+C5+' a '+PC+' d] c',['node','author','whole','previous','previous_node','pattern','context'],'著者が同じ全体を、指定された直前の箇所の内容からここに見て取れる結果として提示する。局所的な場合の内容は指定した閉じた可変状況の記述へ対応させる。先行の提示からの論理的必然や、現実に特定の観察行為があったことは要求しない。'),
 'h26ya':('[a a '+C5+' '+C5+' '+C5+' d] c',['node','author','whole','local','general','context'],'著者が同じ全体で、当の局所的な場合に見られる特徴を、その場合以外にも見られる一般的なあり方へ類比として結び付ける。一般的内容に付された条件を保ち、局所と一般の形式的同値や、全ての現実の事例の無条件な逆説性を付け加えない。'),
 'h26yb':('[a a '+C5+' '+PROFILE+' '+PROFILE+' d] c',['node','author','whole','condition','conclusion','context'],'著者が同じ全体で、一般の人を同じ人引数に保った条件と帰結の関係を提示する。条件はその人が全体として考察すること、帰結はその同じ観点での判断であり、全体内容が人間に限定した全称と含意を構成する。実在の考察者を導入する提示とはしない。'),
 'h26yc':('[a a '+C5+' a a d d] c',['node','author','whole','antecedent_node','course','reference','context'],'著者が同じ全体のこの照応箇所で、指定した先行箇所と同じ推移・固定基準を指す。異なる推移や単なる隣の名詞へ置き換えず、ihnの目的語とdarinの内側の範囲の双方を同じ対象へ結ぶ。'),
}
NODE_INFO={
 'h26yd':([304,466],'第二文全体。'),'h26ye':([304,322],'So zeigt sich hierの先行内容からここに見て取れる提示。'),
 'h26yf':([327,357],'不可解さと予期されなさ。'),'h26yg':([358,381],'Gang menschlicher Dingeの同じ人間の事柄の推移。'),
 'h26yh':([383,401],'so wie auch sonstの他の場合への一般的な類比。'),
 'h26yi':([402,435],'wennによる全体的考察の条件。'),'h26yj':([407,410],'manの一般的な人。'),
 'h26yk':([411,414],'ihnの同じ推移への照応。'),'h26yl':([415,424],'im Großenの全体の関連まで含む考察。'),
 'h26ym':([437,442],'darinの同じ推移の範囲への照応。'),'h26yn':([443,466],'fast alles paradox istのほとんど全ての反期待性。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0017['+str(r[0])+','+str(r[1])+')の'+m) for n,(r,m) in NODE_INFO.items()})
MEANINGS={
 'r6gw':'固定基準の全関連側面が正確な有限列で与えられ、複数あり、各側面が少なくとも一人の人間の行為・立場・帰結に関わり、異なる側面間に関連があり、指定した全関連の両端が同じ全体の中にあるという人間の事柄の推移。全歴史の線形時間順序や全因果の理論は要求しない。',
 'r6gx':'一人の人間の同じ実際の考察行為・点について、同じ人間の事柄の推移の全関連側面と全関連を考慮に入れ、反期待性の評価範囲がその同じ全体と正確に一致すること。別々の不完全な考察行為を合わせて全体的な一行為にしない。',
 'r6gy':'同じ人・推移・基準について、評価点でr6gxを満たす一つの考察行為があるという条件内容。',
 'r6gz':'同じ人間の事柄の推移について、一般の全ての人に、その人が全体として考察するならばその同じ人・推移・基準・点でr6gvのほとんど全ての反期待性が成り立つと条件付ける。実際の考察者は存在量化しないが、推移そのものの構成は条件の外で要求する。',
 'r6g2':'第一文と同じ主題・基準・政治的判断基準・役割で、人間側の必要条件r6f4と共和国側の禁止r6gcを指定された評価状況で組み合わせる。本文現在への固定を外した同じ条件パターンであり、別の主張へ変更する操作ではない。',
 'r6g3':'r6g2を各評価状況で評価する内容。本文現在では先行のr6gkと一致し、通常予測の候補ではその候補状況における同じ政治的条件を評価する。候補状況を後の日付とする必要はなく、既に固定された本文現在の真偽を全候補へ複写しない。',
 'r6g4':'同じ推移の局所的側面を全体に含め、その閉じた具体的内容が第一文の可変状況パターンr6g3であることを確認し、同じ人の観点でr6guの実際の成立・非期待・不可解さを結ぶ。',
 'r6g5':'同じ推移・固定基準で、人引数を保った全体的考察の条件r6gyを取り出す。',
 'r6g6':'同じ推移・固定基準で、人引数を保ったr6gvのほとんど全ての反期待性を帰結性質として取り出す。',
 'r6g7':'本文現在で、当の政治的対比という同じ側面について、著者が採る観点でr6g4が成り立つという局所内容。歴史上の著者の心理的な驚き又は考察行為の実在を補わない。',
 'r6ha':'本文現在で、当の局所例も含む同じ広い推移にr6gzの一般的な全体考察条件を適用する。',
 'r6hb':'局所の不可解で予期されないあり方r6g7と、全体として考察する場合の一般的なほとんど全ての反期待性r6haを合わせた第二文内容。',
 'r6hc':'第二文の全内容を著者に帰属し、So/zeigt sich/hierの先行内容に基づく提示、so wie auch sonstの類比、wenn/manの同じ人への条件、ihn/darinの同じ推移への照応と本文順序を結ぶ。記述を引用する段階で、その内容を現実の真理として実行しない。',
}
LIMITS=[
 '固定原文u0017第二文[304,466)・137非空白文字を対象とする。Gang menschlicher Dingeは人の行為・制度的条件・帰結に関わる複数の側面とその関連を持つ推移として読む。必ず二つの事件が前後して起こること、全歴史の単一方向の発展又は全因果の説明は付加しない。',
 'im Großenは、評価前に固定した文脈上の全関連側面とその間の全関連を、同じ一つの考察行為で考慮することと読む。全体を別の局所標本へ狭めず、逆説性の結果で粒度・対象列・小さい許容比率を変えない。有限の等重みの全側面という明示したモデルであり、全歴史の無限測度への一般化ではない。',
 'manは任意の人が全体的に考察する場合という一般条件で、現実の誰かが考察したという存在主張にしない。ihn/darinと局所・一般の対象は同じ広い推移に保持し、特定の他の現実の事件を追加しない。',
 'befremdlichは馴染みの理解の枠に無理なく収まらないこと、nicht erwartetは非空の標準的な通常予測に一貫した肯定的見通しとして含まれないこと、paradoxは成立する内容がその否定より見込まれにくいことと区別する。fast allesは少数の正の例外を持つ読みを保持する。',
 '当の局所側面の具体的内容は第一文の政治的対比を可変状況で評価するr6g3に一致させる。本文現在では変更していないr6gkと一致する。想定状況での同じ条件の成立は可変であり、本文現在の既定の真偽をそのまま全想定へ複写しない。前文の規範的基準・必要条件の向き・主題・役割・引用内容は変更しない。',
 'So zeigt sich hierは前文からここに見て取れるものとしての提示、so wie auch sonstはその局所例以外にも認める一般的なあり方との類比として読む。先行主張からの形式的演繹や、著者の現実の感情・全観察者の実際の逆説認定は補わない。',
 '第二文の原文全体との通読判断と機械的検査を区別する。全記述域を含む下位式の無制限の有限実行は保持された制約に従い拒否し、可変状況の接続試験ではr6f4/r6gcを明示した境界とする。u0017後続二文、段落全体の判断、およびEinstein全文は未完。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def node(n):return 'k '+n+'[]'
def code(n):return 'r f[k '+n+'[]]'
def definitions():
    selected='k h26xu[v course v aspect v reference]';edge='k h26xv[v course v first v second v reference]'
    text='d r6gw[course a reference d] c['+both(
      'k rcm[k h26xw[v course v reference] i[aspect a]['+selected+']]',
      'k hc[n p b b d[k h26xw[v course v reference]]]',
      'f aspect a[y['+selected+'][g person a['+both('k aa[v person]','k h26xx[v aspect v person v reference]')+']]]',
      'g first a[g second a['+both('u[e[v first][v second]]',edge)+']]',
      'f first a[f second a[y['+edge+']['+both('k h26xu[v course v first v reference]','k h26xu[v course v second v reference]')+']]]')+'].\n'
    text+='d r6gx[person a activity a course a reference d point d] c['+both('k aa[v person]','k dg[v activity v point]',
      'k h26xy[v person v activity v course v reference v point]','k r6gw[v course v reference]',
      'f aspect a[y['+selected+'][k h26xz[v activity v aspect v reference v point]]]',
      'f first a[f second a[y['+edge+'][k h26x2[v activity v first v second v reference v point]]]]',
      'f aspect a[e[k h26xm[v course v person v reference v aspect v point]]['+selected+']]')+'].\n'
    text+='d r6gy[course a person a reference d] e[b point[g activity a[k r6gx[v person v activity v course v reference v point]]]].\n'
    text+='d r6gz[course a reference d] e[b point['+both('k r6gw[v course v reference]',
      'f person a[y[k aa[v person]][y[t[k r6gy[v course v person v reference]][v point]][k r6gv[v course v person v reference v point]]]]')+']].\n'
    text+='d r6g2[point d] c['+both('f community a[t[k r6f4['+TOPIC+' v community '+OLD_REF+']][v point]]',
      't[k r6gc['+STANDARD+' '+ROLE+' '+OLD_REF+']][v point]')+'].\n'
    text+='d r6g3[] e[b point[k r6g2[v point]]].\n'
    text+='d r6g4[course a observer a aspect a reference d point d] c['+both('k r6gw[v course v reference]',selected,
      'e[k h26xn[v course v aspect v reference]][r b[k r6g3[]]]','k r6gu[v course v observer v reference v aspect v point]')+'].\n'
    text+='d r6g5[course a reference d] h[a] e[i[person a][k r6gy[v course v person v reference]]].\n'
    text+='d r6g6[course a reference d] h[a] e[i[person a][b point[k r6gv[v course v person v reference v point]]]].\n'
    text+='d r6g7[] e[b outer[k r6g4['+COURSE+' '+AUTHOR+' '+ASPECT+' '+REF+' '+ANCHOR+']]].\n'
    text+='d r6ha[] e[b outer[t[k r6gz['+COURSE+' '+REF+']]['+ANCHOR+']]].\n'
    text+='d r6hb[] e[b outer['+both('t[k r6g7[]][v outer]','t[k r6ha[]][v outer]')+']].\n'
    whole=code('r6hb')
    profile=lambda n:'o a[r d[p '+n+']][r['+COURSE+'] r['+REF+']]'
    parts=['k h26ub['+node('h26yd')+' '+AUTHOR+' '+whole+' '+CTX+']',
      'k h26x7['+node('h26ye')+' '+AUTHOR+' '+whole+' '+code('r6gk')+' '+node('h26w4')+' r b[k r6g3[]] '+CTX+']',
      'k h26ya['+node('h26yh')+' '+AUTHOR+' '+whole+' '+code('r6g7')+' '+code('r6ha')+' '+CTX+']',
      'k h26yb['+node('h26yi')+' '+AUTHOR+' '+whole+' '+profile('r6g5')+' '+profile('r6g6')+' '+CTX+']']
    parts+=['k h26yc['+node(n)+' '+AUTHOR+' '+whole+' '+node('h26yg')+' '+COURSE+' '+REF+' '+CTX+']' for n in ('h26yk','h26ym')]
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in (('h26w4','h26yd'),('h26ye','h26yf'),('h26yf','h26yg'),('h26yg','h26yh'),('h26yh','h26yi'),('h26yj','h26yk'),('h26yk','h26yl'),('h26yi','h26ym'),('h26ym','h26yn'))]
    return text+'d r6hc[] c['+both(*parts)+'].\n'

def build():
    old=parent();lib=dependency();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for d in closure(lib.document,('r6gu','r6gv')):
        n=d['name'];e=lib.entries[n];prior=old.entries.get(n)
        if prior:assert d==prior['declaration'] and e['meaning_ja']==prior['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6hc',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r6hc']),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='whole_view_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
      new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/qualified-speech-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
