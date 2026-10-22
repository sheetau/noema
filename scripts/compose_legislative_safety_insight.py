"""Connect policy-induced political risk to grasped, grounded factive insight."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE

PARENT='data/religious-emphasis-sentence-basis-v1.json';DEPENDENCY='data/legislative-public-permissions-basis-v1.json'
LIBRARY='examples/v016/legislative-safety-insight.noema';BASIS='data/legislative-safety-insight-basis-v1.json'
STATE='h[a] c';EQUATIONS='h[a '+STATE+'] c';WORLDS='h['+STATE+'] d';POLICY='i c[e]';CONTENT='i d[e]'
MODEL='variables j[a] equations '+EQUATIONS+' factor a harmfactor a worlds '+WORLDS+' policy e harm e'
MARGS='v variables v equations v factor v harmfactor v worlds v policy v harm'
CONTEXT='policy '+POLICY+' community a interest a reference d anchor d assessment d background d'
CARGS='v policy v community v interest v reference v anchor v assessment v background'
NAMES=('ruler','community','group');TIMES=('reference','history','anchor')
FIELDS=' '.join(n+' a' for n in NAMES)+' '+' '.join(n+' d' for n in TIMES)
ARGS=' '.join('v '+n for n in (*NAMES,*TIMES))
MODEL_LABELS=['policy','community','interest','reference','anchor','assessment','background']
PREFIX='['+POLICY+' a a d d d d] '
PRIMITIVES={
 'h26to':('[a a d] c',['community','interest','reference'],
   '同じ政治的共同体について、この固定基準の統治上の安全評価で保持すべき公共的な状態・機能を問う全関連条件の一つ。公共の平穏、共同生活を規律する制度の機能、統治の安全など、当該議論で問題となる損失の範囲を固定する。批判への不快感や現行法が訂正されること自体を直ちに損失にせず、結果が安全な条件だけを残さない。条件の具体的な充足内容はh243uとh243vで別に指定する。'),
 'h26tp':(PREFIX+'c',MODEL_LABELS,
   '同じ方針・共同体・公共的条件・固定基準・起点について、この評価点から考慮すべき因果的な背景候補の全範囲に、この背景が属する。許可の有無だけを介入で切り替える比較を行い、関連する外的事情と機構は背景ごとに固定する。安全な結果、政策の現実の成立、本人の信念又は許可の正当性で範囲を絞らない。現実的な背景・機構の妥当性と網羅は解釈入力の責任で、全論理的可能世界や数値確率そのものではない。'),
 'h26tq':(PREFIX+'j[a]',MODEL_LABELS,
   '同じ方針と公共的条件、固定した文脈・背景における因果比較モデルの全変数列。許可方針の成立と公共的条件の喪失を別の要因として含める。重複・包含・解の有無は合成側で検査し、良い結果に合わせて変数を削らない。'),
 'h26tr':(PREFIX+EQUATIONS,MODEL_LABELS,
   '同じ対象・文脈・背景で各変数の値を状態割当てから定める構造方程式。許可方針の有無を切り替える間も同じ機構と背景を保持し、片方の結果だけ別のモデルから借りない。モデルと現実の機構との適合は解釈の責任であり、解と内容の対応は合成側で確認する。'),
 'h26ts':(PREFIX+'a',MODEL_LABELS,
   '同じモデルで指定の閉じた許可方針が成立するかを表す要因変数。発言の実行や君主の信念、別の許可方針を代入せず、方針内容との一致を比較状況ごとに検査する。'),
 'h26tt':(PREFIX+'a',MODEL_LABELS,
   '同じモデルで、同じ共同体の指定公共的条件が満たされず損失となることを表す要因変数。政策要因と区別し、具体的な損失内容との一致を比較状況ごとに検査する。'),
 'h26tu':(PREFIX+WORLDS,MODEL_LABELS,
   '同じ因果モデルの状態割当てに対応する反事実的な評価状況。許可方針と同じ公共的条件の損失をその状況で評価でき、双方がモデル内の要因値に一致することを合成側で検査する。現実の現在点への一致や、同じ真偽になる別の共同体・方針への置換は要求しない。'),
 'h26tv':('[a '+CONTENT+' d c d] c',['judgment','content','reference','polarity','point'],
   '同じ固定認識基準において、この保持判断が指定の閉じた段階3内容をこの点で指定極性により認めている。h245qの判断内容・極性の関係を高い内容段階へ保つ。判断の保持者、受容、使用理由、支持・十分な根拠、把握、内容の真理は別に検査する。単なる記述への言及や同じ真理値の別内容に置換しない。'),
 'h26tw':('[a '+CONTENT+' d d] c',['person','content','reference','point'],
   '同じ人が、固定した認識基準で、この閉じた段階3内容の指示対象・区別・関係を捉えて扱える状態にある。h26ahの把握を高い内容段階へ保ち、文字列の記憶だけや単なる受容と分ける。全ての帰結を知ること、客観的真理、根拠、現在の政策実施を含意しない。'),
}
MEANINGS={
 'r6dm':'同じ変数・方程式・異なる政策要因と損失要因・状況対応・二内容について、政策なしで損失を免れる解があるなら政策ありの全解も損失を免れるrktと、両側の全解で政策と非損失内容を対応させるrkvを要求する。両側の解は非空。別原因で避けられない損失を政策のせいにせず、無解や内容不一致を安全としない。',
 'r6dn':'r6dmと同じ有効な要因・二内容対応について、政策なしで非損失の解があり、政策ありで損失の解が一つ以上あるという危険側の対照。無解・内容不一致の場合にはこちらも成立せず、安全の単純否定で危険を補わない。',
 'r6do':'同じ方針・共同体・公共的条件・固定文脈・背景の全モデル入力をr6dmへ渡し、損失を同じ共同体へのr326の条件不充足として明示する。同じ方針記述を脱引用した実内容とモデルの政策要因を比較し、方針名だけで一致としない。',
 'r6dp':'同じ固定基準の公共的条件範囲が非空で、全条件について少なくとも一つ背景候補があり、その全背景にr6doの比較上の危険不在があるという内容。良い背景一つだけや空の範囲で安全を認定しない。条件と背景は安全性の結果を見て選び直さない。',
 'r6dq':'同じ統治者・共同体・全臣民集団・内容基準・履歴・起点の六呼称を確認し、r6dlの全許可方針をr6dpの危険不在へ結ぶ。許す行為の対象と、許可方針そのものの安全性を区別する。',
 'r6dr':'六対象の閉じた呼称をr6dqへ適用し、同じ許可方針の危険不在を閉じた段階3内容として作る。認識へ渡す際に政策や安全性を引用の外側で実行しない。',
 'r6ds':'同じ本人が、同じ閉じた段階3内容を受容し把握していることと、その内容を肯定する同じ保持判断の同じ理由が使用・支持され十分な認識根拠として働くことを結ぶ。r5clの受容・把握・保持・根拠の区別を高い内容段階へ保ち、真理はr6dtで別に要求する。',
 'r6dt':'r6dsの同じ把握された根拠ある受容に加え、同じ内容が指定した真偽評価点で成立するという事実的な認識。誤った信念、偶然の正答、根拠のない確信、別内容への根拠を見抜いたことへ換算しない。',
 'r6du':'同じ六対象のr6drの危険不在内容を、同じ統治者本人が現在点でr6dtとして把握・受容し、同じ点の真理と十分な根拠を持つという内容。国家元首の思考態度への帰属と文全体の談話接続は後で行う。',
}
LIMITS=[
 'ohne Gefahrを、この同じ許可を与えることによって公共的な損失の危険が生じないという因果比較の読みで扱う。公共の平穏・制度の機能・統治の安全など当該議論に関係する条件を明示し、単なる批判への不快感や訂正を危険としない。世界の全ての害の絶滅、あらゆる背景の絶対安全、数値確率ゼロを主張しない。',
 '既存rktの強い質的比較を採る。同じ背景で政策なしなら損失を免れる可能性があるとき、政策ありで損失の解を一つも残さない。両側に解を要求し、既存の背景だけで不可避の同じ損失を許可のせいにしない。確率的な増分や損失額はこの比較へ追加せず、関連する損失の条件は全範囲で量化する。',
 '政策要因は前回の全臣民・全候補・三対象の許可方針の実内容へ、損失要因は同じ共同体の固定された条件の不充足へ、両側の全介入解で一致させる。発言したことの危険と許可方針の危険、別共同体の安全性、別の政策による好結果を混ぜない。',
 '因果モデルの背景・機構とその全範囲の現実的な妥当性は解釈入力の責任である。有限試験は現実の歴史的政策が安全であったことや未知の脅威の網羅を証明しない。原著者の主張の真理を実証することと、その内容の記述を分ける。',
 'sieht einを、同じ内容を受容し、その区別・関係を把握し、同じ保持判断に十分な認識根拠が働き、内容が真であるという読みで扱う。突然の直観、現在まさに判断を始める行為、演繹的証明だけ、感情的な確信や全知を要件にしない。根拠が何であるかは原文にないため捏造しない。',
 '高い引用段階の内容を低いh26aeへ隠して代入しない。既存h26nfの受容、h26aiの保持、fc/fd/h26ajの根拠を再利用し、判断内容・把握の一般関係だけを段階3へ拡張する。真偽評価は同じ内容で別に実行し、受容だけから真理を推論しない。',
 '国家元首のDenkungsartへの帰属、啓蒙を支持するdie erstere、宗教領域からの拡張・selbst、実例・尊敬する君主の先行者不在、Aber/sogar、全文提示・通読は残る。今回の依存群の検査を第二文全文の意味判断へ換算しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def names():return ' '.join('k '+('h223g' if n in NAMES else 'h223h')+'[v '+n+']' for n in (*NAMES,*TIMES))
def definitions():
    valid=both('k rz[v variables v factor]','k rz[v variables v harmfactor]','u[e[v factor][v harmfactor]]')
    safe='i[state '+STATE+'][u[c[v state][v harmfactor]]]';harm='i[state '+STATE+'][c[v state][v harmfactor]]'
    inverse='b point[u[t[v harm][v point]]]'
    linked='k rkv[v variables v equations v factor '+safe+' v worlds v policy '+inverse+']'
    text='d r6dm['+MODEL+'] c['+both(valid,linked,'k rkt[v variables v equations v factor '+safe+']')+'].\n'
    mask='i[item a][e[v item][v factor]]'
    possible=lambda sign,goal:'k rv[v variables v equations '+mask+' i[item a]['+sign+'] '+goal+']'
    text+='d r6dn['+MODEL+'] c['+both(valid,linked,possible(FALSE,safe),possible(TRUE,harm))+'].\n'
    providers=['k '+n+'['+CARGS+']' for n in ('h26tq','h26tr','h26ts','h26tt','h26tu')]
    text+='d r6do['+CONTEXT+'] c['+both('k h243v[v interest v community v reference]',
        'k r6dm['+' '.join(providers)+' s[v policy] k r326[v community v interest v reference]]')+'].\n'
    selected='k h26tp['+CARGS+']'
    perinterest=both('k h243v[v interest v community v reference]','g background d['+selected+']',
        'f background d[y['+selected+'][k r6do['+CARGS+']]]')
    text+='d r6dp[policy '+POLICY+' community a reference d anchor d] e[b assessment['+both(
        'g interest a[k h26to[v community v interest v reference]]',
        'f interest a[y[k h26to[v community v interest v reference]]['+perinterest+']]')+']].\n'
    validnames=['e[s[k '+('h223g' if n in NAMES else 'h223h')+'[v '+n+']]][v '+n+']' for n in (*NAMES,*TIMES)]
    policy='k r6dl['+names()+']'
    text+='d r6dq['+FIELDS+'] e[b assessment['+both(*validnames,'t[k r6dp['+policy+' v community v reference v anchor]][v assessment]')+']].\n'
    text+='d r6dr['+' '.join(n+' i[a]' for n in NAMES)+' '+' '.join(n+' i[d]' for n in TIMES)+'] '+CONTENT+'[o a[r d[p r6dq]]['+ARGS+']].\n'
    grounded='g judgment a[g reason a['+both('k h26ai[v person v judgment v reference v point]',
        'k h26tv[v judgment v content v reference '+TRUE+' v point]',
        'k fc[v judgment v reason v point]','k fd[v reason v judgment v point]','k h26aj[v reason v judgment v reference v point]')+']]'
    text+='d r6ds[person a content '+CONTENT+' reference d point d] c['+both('k aa[v person]',
        'k h26nf[v person v content v point]','k h26tw[v person v content v reference v point]',grounded)+'].\n'
    text+='d r6dt[person a content '+CONTENT+' reference d assessment d point d] c['+both(
        'k r6ds[v person v content v reference v point]','t[s[v content]][v assessment]')+'].\n'
    text+='d r6du['+FIELDS+'] e[b point[k r6dt[v ruler k r6dr['+names()+'] v reference v point v point]]].\n'
    return text
def build():
    sources=(parent(),dependency());roots=(('rkt','rkv','rv','rz','r326','h26nf','h26ai','fc','fd','h26aj','aa','h223g','h223h'),('r6dl',))
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
    basis=dict(status='policy_induced_risk_and_grounded_factive_insight_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
