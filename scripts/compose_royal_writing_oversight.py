"""Compose clarification through writings and their governmental supervision."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='data/monarchical-religion-sentence-basis-v1.json'
LIBRARY='examples/v016/royal-writing-oversight.noema'
BASIS='data/royal-writing-oversight-basis-v1.json'
NAMES=('actor','community','person','project','work','field','regulation')
PRIMITIVES={
 'h26ih':('[a a a d] c',['person','work','item','reference'],
   'この本人が同じ書かれた作品を通じて検討し明確にしようとする、自分の理解・見識に属する内容項目の全範囲。本人の認識上の立場を整理する対象であり、単に他人の見解を引用・所持することとは区別する。未決・改訂中の項目も扱い、現在の真理・根拠・明確化の成功・君主の承認で範囲を選別しない。内容と別名はh26ad/h26ag/h26aeで別に固定する。'),
 'h26ii':('[a a a d] c',['person','work','criterion','reference'],
   '同じ本人が同じ作品で扱う理解内容を整理し明確にするための、固定した全評価条件の一つ。対象・主張・理由・適用条件の区別、曖昧や混同の解消、未決点の特定、整理した説明可能性を当該内容に即して網羅する。単なる文字の清書や好都合な成功条件だけへ狭めない。条件内容はh26ijへ明示し、現在の達成・内容全体の客観的真理・読者全員の同意をこの範囲だけでは要求しない。'),
 'h26ij':('[a a a d] e',['criterion','person','work','reference'],
   '同じ明確化条件を、同じ本人・作品・固定基準について明示したNoemaの命題内容として返す。曖昧さを除くべき区別や整理すべき関係を具体的に表し、原語ラベルや未知の真理値だけでは代用しない。評価点の移動で対象を取り替えず、現在の充足は内容の評価で別に調べる。'),
 'h26ik':('[a a a d d] c',['person','project','work','reference','point'],
   'この点の同じ本人の同じ探究・検討活動で、指定作品の記された表現を組み立て、改訂し、又は批評的に検討することが、本人の理解を整理する手段として使われている。単なる所持・同時の読書・他人の作業とは区別する。共同執筆や応答を通じた検討を許し、単独著者・刊行済み・全読者への配布・明確化成功は要求しない。活動の生起・本人参加・目的・作品と外部記録は別に結ぶ。'),
 'h26il':('[a a a d d] c',['regulation','office','work','reference','point'],
   '同じ活動において、指定された公的統治職の権限を用い、同じ作品の知的内容を審査・承認・訂正・流通統制の対象に置いている。単に私人として読む又は論駁すること、暴力防止や市民的秩序の保持だけの監督とは区別する。実際の出版禁止・没収・内容改変の成功は必須でなく、その統治職がこの知的審査を正当に所管することは含意しない。職の保持者と活動参加は別に構成する。'),
 'h26im':('[a a a d d] c',['person','activity','target','reference','point'],
   'この本人は同じ活動で、この対象を自分の当該の注意・関与を向けるに値するものとして取り扱っている。対象の客観的価値、関与の正当性、著者自身の賛同とは別の本人側の取り扱い。皮肉や尊大さの論述的な提示はこの関係だけには含めない。'),
 'h26in':('[a a d d] c',['intervention','project','reference','point'],
   '同じ活動はこの点で、別の指定された探究・検討の進め方又はその表現へ外から関与し、統制の対象に置く働きとして介入している。作品名が同じだけの無関係な行為、単なる傍観、当事者の自由な批評的応答だけとは区別する。探究の失敗・完全阻止・内容変更の成功・関与の正当性は要求しない。'),
}
MEANINGS={
 'r5o5':'同じ本人・作品の理解内容h26ihが非空で、その全項目が同じ固定範囲h26adに属し、同じ代表項目h26agが同じ検討領域h26c5に属する。本人の見識の対象を現在の真理又は成功だけで縮めない。',
 'r5o6':'同じ本人・作品・固定基準の明確化条件h26iiが非空である。各条件の内容はh26ijに固定し、条件が満たされたかはまだ要求しない。',
 'r5o7':'本人・作品・領域の正確な三対象列についてr5o5/o6の範囲を保持し、全理解項目の代表内容を本人がh26ahで把握し、同じ明確化条件の全内容h26ijを満たす目標。現に目指すことや目標達成はこの内容の引用からは導かない。',
 'r5pa':'同じ本人の同じ生起する検討活動に参加し、同じ作品が記された表現のまとまりscと外部で参照可能な記録sdを持ち、同じ作品の表現を検討手段h26ikとして用いる。対象範囲r5o5と条件範囲r5o6を固定し、単独著者や完成刊行は要求しない。',
 'r5pb':'同じr5paの活動が、同じ本人・作品・領域の三対象列と固定基準による明確化r5o7を目標h26hfとする。書面での実際の試みと目的を結び、現在の明確化成功・全内容の真理・他人の目的を混ぜない。',
 'r5pc':'同じ君主・共同体への臣民r5niが、その共同体の宗教的検討領域h26g7についてr5pbの書面による明確化の試みを行う。臣民と領域は固定基準に置き、成功した臣民の著作だけを選ばない。',
 'r5pd':'同じ君主が同じ共同体の最高職h234f/r2uiを保持し、同じ生起活動で同じ作品をその職の統治上の内容審査h26ilへ置き、自分の注意に値する対象としてh26imで扱う。審査の正当な所管・出版禁止・審査結果の成功を追加しない。',
 'r5pe':'同じ君主・共同体・臣民・検討活動・作品・領域・監督活動について、r5pcの明確化の試みに対し、同じ最高職でのr5pdの書面監督がh26inとして介入する。別作品への審査と別人の試みを寄せ集めない。',
 'r5pf':'君主・共同体・臣民・検討活動・作品・領域・監督活動の正確な七対象列と固定基準をr5peへ渡す。後の威厳への損傷、二つの介入方法、条件付き全文の対象に引用できる。',
}
LIMITS=[
 'u0013第十二文のwenn er sich hierin mischt, indem er die Schriften, wodurch seine Unterthanen ihre Einsichten ins Reine zu bringen suchen, seiner Regierungsaufsicht würdigtに向けた依存群。書面による本人の理解の明確化の試みと、それへの君主の統治的監督を構成する。威厳への損傷、selbst、würdigtの皮肉の提示、二介入方法の比較、ラテン語の批判引用と全文帰属は未完。',
 'Einsichtenはここでは臣民が著作で明らかにしようとする自分の理解内容として固定する。ins Reine bringenは単なる清書でなく、対象・根拠・条件の区別を整理して明確にする読解。Adelung Reinの比喩的な整理・確定の語義を補助にし、唯一の歴史解釈とはしない。現在既に正しい知識が完成していることや、見解をすべて肯定したまま強化することを要求しない。',
 '明確化の目標は全内容への把握h26ahと、具体的なNoema内容で与える全整理条件を結ぶ。条件には未決・改訂点の特定も含め、宗教的な真理への到達そのものや全認識の獲得r5clを必要条件にはしない。目標条件の完全性・妥当性は解釈入力の責任で、有限検査から現実の認識の完成を証明しない。',
 'suchenは書かれた表現を手段として実際に検討し、その同じ活動を明確化の目標へ向けること。目標だけの保持、他者の試み、所持するだけの書物とは区別し、成功、完成した著作、単独著者、全公衆への提供を追加しない。作品は情報的対象、記録と媒体はsdで別に扱う。',
 'hierinは先行文と同じ共同体の宗教的な理解・自己選択の領域へ結ぶ。Regierungsaufsichtはその知的内容を統治権限による審査・承認・統制の対象に置くことと読み、必要な市民的秩序の監督や私人の批評から分ける。実際の禁止・没収・探究失敗まで強めない。',
 'würdigtの本人側の値するとする取り扱いをh26imへ分ける。著者がその価値判断や統治の所管を正しいと認めることではない。尊大な取り扱いを皮肉に示す談話上の効果は全文で別に接続する。',
 '複数の著作・臣民への適用は後の全文で全候補の量化へ結ぶ。この依存群は一つの作品とそれに関わる一人の試みを取るが、作品の唯一性や著者一人、他の作品・臣民の不在を主張しない。前半・後半とも同じ監督行為を保つ必要がある。',
 '新たな本文主張又は全文の意味判断はまだ加えない。正本107主張、登録簿v190、意味確認11,490文字を保持する。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    items='k h26ih[v person v work v item v reference]'
    criteria='k h26ii[v person v work v criterion v reference]'
    scope=both('k aa[v person]','g item a['+items+']',
        'f item a[y['+items+']['+both('k h26ad[v item v reference]','k h26c5[k h26ag[v item v reference] v field v reference]')+']]')
    text='d r5o5[person a work a field a reference d] c['+scope+'].\n'
    text+='d r5o6[person a work a reference d] c[g criterion a['+criteria+']].\n'
    frame=both('k r5o5[v person v work v field v reference]','k r5o6[v person v work v reference]')
    goal=both(frame,'f item a[y['+items+'][k h26ah[v person k h26ag[v item v reference] v reference v point]]]',
        'f criterion a[y['+criteria+'][t[k h26ij[v criterion v person v work v reference]][v point]]]')
    text+='d r5o7[bindings j[a] reference d] e[b point['+bind(('person','work','field'),goal)+']].\n'
    fields='person a project a work a field a reference d point d';args='v person v project v work v field v reference v point'
    actual=both(frame,'k dg[v project v point]','k df[v person v project v point]','k sc[v work v point]','k sd[v work v point]',
        'k h26ik[v person v project v work v reference v point]')
    text+='d r5pa['+fields+'] c['+actual+'].\n'
    text+='d r5pb['+fields+'] c['+both('k r5pa['+args+']','k h26hf[v person v project r b[p r5o7] l[a][v person v work v field] v reference v point]')+'].\n'
    text+='d r5pc[actor a community a '+fields+'] c['+both('k r5ni[v actor v person v community v reference]',
        'k h26g7[v field v community v reference]','k r5pb['+args+']')+'].\n'
    royal=both('k h234f[v office v community v point]','k r2ui[v actor v office v community v point]',
        'k dg[v regulation v point]','k df[v actor v regulation v point]',
        'k h26il[v regulation v office v work v reference v point]','k h26im[v actor v regulation v work v reference v point]')
    text+='d r5pd[actor a office a community a regulation a work a reference d point d] c['+royal+'].\n'
    text+='d r5pe['+' '.join(n+' a' for n in NAMES)+' reference d point d] c['+both('k r5pc[v actor v community '+args+']',
        'g office a[k r5pd[v actor v office v community v regulation v work v reference v point]]',
        'k h26in[v regulation v project v reference v point]')+'].\n'
    text+='d r5pf[bindings j[a] reference d] e[b point['+bind(NAMES,'k r5pe['+' '.join('v '+n for n in NAMES)+' v reference v point]')+']].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document)
    roots=['aa','h26ad','h26ag','h26ae','h26c5','h26ah','dg','df','sc','sd','h26hf','r5ni','h26g7','h234f','r2ui']
    doc.update(declarations=closure(doc,roots),statements=[]);imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='written_clarification_attempt_and_royal_governmental_oversight_partial',document=LIBRARY,
        primitives=prims,definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
