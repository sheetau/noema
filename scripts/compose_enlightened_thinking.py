"""Bind practical favour, a person's manner of thinking, and legislative insight."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_legislative_safety_insight import CONTENT,NAMES,TIMES,FIELDS,ARGS,names

PARENT='data/religious-emphasis-sentence-basis-v1.json'
DEPENDENCY='data/legislative-safety-insight-basis-v1.json'
LIBRARY='examples/v016/enlightened-thinking.noema';BASIS='data/enlightened-thinking-basis-v1.json'
PROPERTY='i[h[a] e]'
PRIMITIVES={
 'h26tx':('[a a '+PROPERTY+' d d] c',['person','activity','process_kind','reference','point'],
   '本人が同じ活動において、閉じた性質記述が指定する種類の過程を進める機会・条件を支える向きに、実務上の寄与を供している。資源、保護、制度上の余地を与えることや障害を取り除くことなどを含み、私的な賛意、未着手の願望、無関係な寄与、偶然の副作用だけと区別する。活動の生起と本人の能動的参加は別に結ぶ。特定の手段、過程の現実の達成、全対象者の成功、唯一原因性又は全背景での増分を含意しない。進める過程の種類を引用のまま同定し、別の種類や同じ真偽値の記述へ交換しない。'),
 'h26ty':('[a a d d] c',['manner','person','reference','point'],
   'この精神的な構成要素は、同じ本人が対象を捉え、論点を選び、判断を組み立てる際の持続する方針・理解・習慣のあり方である。一つの結論の内容、今だけの気分、他人の習慣、物理的な脳部位とは区別する。持続とはその点で本人の判断の仕方として保持されることで、全生涯の不変、全分野の無誤謬、道徳的な人格の完成、独立した自己判断の全条件は要求しない。本人の精神的な営みへの所属はh4mで別に結ぶ。'),
 'h26tz':('[a a d d] c',['manner','judgment','reference','point'],
   'この同じ保持判断は、指定した判断の仕方に沿って対象の捉え方・区別・論点の処理を具体化したものである。単なる同時存在、偶然の同じ結論、別の人の判断の流用と区別する。判断の保持者・内容・理由・真理、思考態度の持ち主は別に検査し、思考態度そのものを人や判断行為へ同定しない。'),
 'h26t2':('[a a a d d] c',['manner','person','topic','reference','point'],
   '同じ本人が同じ判断の仕方を、この主題に関する考察にも用いている。指定領域を扱うという関係であり、その領域でのあらゆる判断の正解、一つの具体的な教義への同意、領域内の政策実施、別の領域への適用を自動的には導かない。主題、思考態度と本人の対応は合成側で検査する。'),
 'h26t3':('[a a a '+PROPERTY+' d] c',['mention','author','antecedent','process_kind','context'],
   '著者がこの指示表現で、指定した先行箇所と同じ過程の種類を、同じ閉じた性質記述によって受ける。先行箇所と現在の箇所の同一性、過程の現実の生起、語の綴りだけ、近くにある別の状態概念への置換を含意しない。性質の合成内容と原文箇所は別に指定する。'),
}
MEANINGS={
 'r6dv':'同じ人が実際に生起する同じ活動に能動的に参加し、その活動で指定された過程の種類への実務的な後押しh26txを供する。引用された過程の達成を評価せず、私的な好意だけや他人の支援活動を本人の支持へ数えない。',
 'r6dw':'同じ共同体の国家元首r2ujが、先行第一文と同じbiの啓蒙過程をr6dvとして後押しする。人が自己に帰責される未成熟から離脱するという一般概念を受け、未成熟状態自体や宗教だけの別定義を支援対象にしない。',
 'r6dx':'同じ本人の同じ保持判断が、指定された段階3内容を肯定し、その同じ判断に使用され支持された十分な認識根拠がある。r6ds内の判断と理由の束縛を、判断を引数として取り出す。受容・把握・真理は別に結ぶ。',
 'r6dy':'同じ人の精神的な営みの構成要素h4mであり、同じ本人の持続する判断の仕方h26tyである。同じ一つの意見や抽象物の擬人的な認識へ置き換えない。',
 'r6dz':'同じ本人のr6dyの思考態度が具体化された同じr6dxの保持判断について、本人の同じ段階3内容の受容・把握と指定評価点の真理を結ぶ。r6dtの認識要件に、その認識を担う同じ判断と思考態度の対応を加える。別判断の根拠や別人の思考態度では代用しない。',
 'r6d2':'同じ国家元首・共同体・全臣民について、biの啓蒙への実務的な支持と、同じ本人の思考態度の宗教領域への適用、同じ六対象の立法上の許可方針の安全性r6drへのr6dzの認識を結ぶ。宗教を越えて同じ本人の立法を扱う内容へ及ぶという接続であり、実際にその許可方針を施行したことはここから導かない。',
 'r6d3':'die erstereの箇所と著者・先行箇所・提示文脈を受け、同じbiの啓蒙過程の性質をh26t3へ渡す。第一文r6caと同じ展開を持つ概念への照応を固定し、宗教的未成熟r6ciへの照応にしない。原文の各箇所の供給と全文提示は統合側で行う。',
}
LIMITS=[
 'u0016第二文のDenkungsart eines Staatsoberhaupts, der die erstere begünstigtから立法上の安全性を洞察する主節までの依存群。derはStaatsoberhaupt、die erstereは第一文のAufklärungを受ける読みとする。先行する未成熟は支持される対象ではない。',
 'begünstigtを、啓蒙を進める条件への実務的な後押しとして読む。内心の好意だけへ弱めず、啓蒙の完成や各臣民の成功、特定の政策の実施まで強めない。継続して運用している支援も活動に含め、全瞬間に新しい行為を始めることは要求しない。これは当該文脈で採る明示的な読みであり、語の全用法の唯一の定義ではない。',
 'Denkungsartは本人の持続する判断の仕方である。既存h4mの精神的な構成要素へ結び、sieht einの認識はその仕方に沿って組み立てられた本人の保持判断へ帰属する。旧r2qnの全通常場面での独立判断や、人格の道徳的完成を新たな条件として持ち込まない。',
 '宗教領域で用いられる同じ思考態度が、本人の立法に関する許可方針の安全性をも認識するという範囲の拡張として読む。空間移動、時間的に後から初めて悟ったという変化、宗教上の政策の現実の成立、思考態度という抽象物自身の人間的認識を補わない。selbst/nochの取り立てとAber/sogarの談話作用は全文統合時に別に記述する。',
 '認識の対象には前群の同じr6drをそのまま用い、同じ六対象の呼称、全三対象の許可方針、公共的条件と背景、因果比較の読みを保つ。r6dzは同じ保持判断に十分な根拠と思考態度への対応を要求する。r6dtの既存定義は変更しない。',
 '全体はまだ条件を組み立てる依存群であり、一般化の範囲、実例、尊敬される君主と先行者不在、談話提示、全文通読は未接続。正本118主張、18全単位判断と第一文336文字を保持し、今回の検査を意味確認文字数へ加算しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def definitions():
    text='d r6dv[person a target '+PROPERTY+' reference d point d] c['+both('k aa[v person]',
        'g activity a['+both('k dg[v activity v point]','k df[v person v activity v point]',
          'k h26tx[v person v activity v target v reference v point]')+']')+'].\n'
    text+='d r6dw[ruler a community a reference d point d] c['+both('k r2uj[v ruler v community v reference]',
        'k r6dv[v ruler r[p bi] v reference v point]')+'].\n'
    text+='d r6dx[person a judgment a content '+CONTENT+' reference d point d] c['+both(
        'k h26ai[v person v judgment v reference v point]','k h26tv[v judgment v content v reference '+TRUE+' v point]',
        'g reason a['+both('k fc[v judgment v reason v point]','k fd[v reason v judgment v point]',
          'k h26aj[v reason v judgment v reference v point]')+']')+'].\n'
    text+='d r6dy[person a manner a reference d point d] c['+both('k aa[v person]',
        'k h4m[v manner v person v point]','k h26ty[v manner v person v reference v point]')+'].\n'
    text+='d r6dz[person a manner a content '+CONTENT+' reference d assessment d point d] c['+both(
        'k r6dy[v person v manner v reference v point]','k h26nf[v person v content v point]',
        'k h26tw[v person v content v reference v point]',
        'g judgment a['+both('k r6dx[v person v judgment v content v reference v point]',
          'k h26tz[v manner v judgment v reference v point]')+']','t[s[v content]][v assessment]')+'].\n'
    text+='d r6d2['+FIELDS+' manner a topic a] e[b point['+both(
        'k r6bo[v ruler v community v group v reference]',
        'k r6dw[v ruler v community v reference v point]',
        'k h26j7[v topic v reference]','k h26t2[v manner v ruler v topic v reference v point]',
        'k r6dz[v ruler v manner k r6dr['+names()+'] v reference v point v point]')+']].\n'
    text+='d r6d3[mention a author a antecedent a context d] c[k h26t3[v mention v author v antecedent r[p bi] v context]].\n'
    return text
def build():
    sources=(parent(),dependency());roots=(('bi','r6ca','h4m','aa','df','dg','r2uj','r6bo','h26j7'),('r6dr','r6dt'))
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
    basis=dict(status='practical_enlightenment_support_and_personal_thinking_manner_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
