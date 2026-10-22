"""Bind scoped epoch classification and an explanatory personal epoch name."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_present_epoch_sentence import CTX,AUTHOR,ACTUAL,REF

PARENT='examples/v016/kant-progress-indications-sentence.noema'
PARENT_BASIS='data/progress-indications-sentence-basis-v1.json'
FULL='examples/v016/kant-named-epoch-sentence.noema';CORE='examples/v016/named-epoch-sentence-core.noema'
BASIS='data/named-epoch-sentence-basis-v1.json';ANNOTATIONS='data/named-epoch-sentence-identifiers-v1.json'
C3='i d[e]';P3='i d[h[a] e]';P0='i[h[a] e]'
PRIMITIVES={
 'h26mu':('[] a',[],'第七段落末のFriederichsが指す歴史的人物、プロイセンのフリードリヒ二世。固有名の参照先として編集上固定する。人名の綴りから全称的に一意性を推論せず、1740–1786という在位情報は参照確認の証拠であり原文の追加主張にしない。'),
 'h26mv':('[] a',[],'同じ箇所のFriederichsという名称対象。人物h26muとは別で、同じ箇所のhzihで参照先を結ぶ。原刊の属格形と編集上の展開形は識別注記で区別する。'),
 'h26mw':('[] a',[],'h26muの時代呼称において参照するプロイセン王の公的な統治の役職。後の版の称号表記や地理的地域の参照を役職そのものと同一視しない。具体的な統治政策・正当性・啓蒙への単独の功績は含めない。'),
 'h26mx':('[a a d] c',['person','office','point'],'同じ人が同じ公的な役職を、その時点で現に占めて職務を担う。在職関係であり、名称だけの保有、私的所有、在職期間と時代全体の同一性、政策の正しさや成功ではない。'),
 'h26my':('[a a '+C3+' '+C3+' d] c',['node','author','whole','respect','context'],'著者が同じ全体の時代判定と呼称を、指定した先行内容に示された観点に限って提示する。他の観点でも同じ分類が真であることや、他の観点で必ず偽であることを加えない。指定内容は引用として受け、実際の真理をこの提示関係だけから実行しない。'),
 'h26mz':('[a a a '+P3+' '+P0+' d] c',['node','author','subject','first','second','context'],'著者が同じ対象に用いた第一の性質による呼称を、第二の性質による呼称で説明的に言い換える。二記述を段階の異なる閉じた記述として保ち、排他的な二選択肢や一般的な同義語にしない。世界の内容と呼称の説明的な結合を区別する。'),
 'h26m2':('[a a a a '+P0+' d] c',['node','author','epoch','person','profile','context'],'著者が同じ時代を指定人物に特徴づけて呼ぶため、その人物の在職と結ぶ指定プロフィールを用いる。偶然同時代にいるだけの人物への言及とは区別するが、その人物だけの因果的功績・所有物・全時代の長さを加えない。前後の観点指定は別に保持する。'),
 'h26m3':('[a a a a d] c',['node','author','antecedent','referent','context'],'著者が指示表現を、指定した先行箇所と同じ対象への照応として用いる。別の類似対象、著者と対象の同一性、近接した場所や別の時代を補わない。'),
}
NODE_INFO={
 'h26m4':([675,778],'第四文全体。'),
 'h26m5':([675,693],'In diesem Betrachtによる観点限定。'),
 'h26m6':([698,714],'dieses Zeitalterの同じ時代への照応。'),
 'h26m7':([715,743],'啓蒙の時代という第一の分類。'),
 'h26na':([745,777],'oder以下の同じ時代の説明的な呼称。'),
 'h26nb':([766,777],'Friederichsの固有名使用。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0014['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
MEANINGS={
 'r5vs':'同じ現在の時代h26kiについて、第一文と同じr5u4の機会開放・障害漸減があるという性質。到達済みのr5u2へ交換せず、他の時代には適用しない。',
 'r5vt':'同じ基準・実際の候補履歴・時代区間を既存rmwへ渡し、h26muの王職h26mwの在職点と重なる時代のプロフィールを返す。百年の長さ、在位期間との一致、因果的独占は要求しない。',
 'r5vu':'現在の同じ時代について進行の性質r5vsと人物在職の時代プロフィールr5vtを連言する。説明的な呼称として用いる関係・観点限定・著者帰属はr5vvで別に構成する。',
 'r5vv':'第四文の内容を段階3で著者へ帰属する。同じ進行の観点限定、第一文の同じ時代への指示、二つの呼称の説明的な言い換え、人物で時代を特徴づける呼称と固有名参照、第三文からの本文順序を結ぶ。',
}
LIMITS=[
 'u0014第四文[675,778)の90非空白文字。In diesem Betrachtは前の三文で具体化した、未到達でも機会開放と障害減少が進むという観点に限る。同じ進行r5u4を引用し、全観点での時代評価へ拡げない。',
 'dieses Zeitalterは第一文と同じh26kiである。Zeitalter der Aufklärungは同じ進行の性質であり、aufgeklärtes Zeitalterという達成済みへの転換ではない。',
 'oderは同じ時代への説明的な第二呼称と読む。Jahrhundertは百年の厳密な長さでなく、人によって特徴づけた時代という広い用法。歴史辞書はこの用法の存在を支持するが、著者の意図を一意に証明するものではない。',
 'フリードリヒ二世が王職を担う時点と重なる同じ時代に、著者がその人物の呼称を与えるという読み。在職の重なりだけでは時代呼称にしないためh26m2を別に結ぶ。同じ進行の観点でその人物を特徴として取り上げるが、全ての進展をその人物一人の政策の効果とはしない。',
 '人物と名称と役職は別対象。原刊のFriederichsを保存し、Friedrich II.は編集上の参照確認に用いる。1740–1786、具体的政策、厳密な時代の端点、後続段落の君主賛辞を追加の著者主張にしない。',
 '内容帰属は引用を実行しない。有限反例検査、原刊と一次資料の照合、全語句・文全体の読解を区別する。独立査読又は自動的な意味同値証明ではない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
def definitions():
    candidate='k h26kl['+ACTUAL+']'
    history='i[at d][k h257z['+REF+' '+candidate+' v at]]'
    before='i[first d last d][k ic[v first v last '+candidate+']]'
    periods='i[era a at d][k h26ab[v era '+REF+' '+candidate+' v at]]'
    text='d r5vs[epoch a] e[b outer['+both('e[v epoch][k h26ki[]]','t[k r5u4[]][v outer]')+']].\n'
    text+='d r5vt[] h[a] e[k rmw[k h26mu[] k h26mw[] '+history+' '+before+' '+periods+' p aa p h26mx]].\n'
    text+='d r5vu[] e[b outer['+both('t[k r5vs[k h26ki[]]][v outer]','t[c[k r5vt[]][k h26ki[]]][v outer]')+']].\n'
    whole='r d[k r5vu[]]';aspect='r d[p r5vs]';label='r[k r5vt[]]'
    parts=['k h236i[k h26m4[] '+AUTHOR+' '+whole+' '+CTX+']',
        'k h26my[k h26m5[] '+AUTHOR+' '+whole+' r d[k r5u4[]] '+CTX+']',
        'k h26mz[k h26na[] '+AUTHOR+' k h26ki[] '+aspect+' '+label+' '+CTX+']',
        'k h26m2[k h26na[] '+AUTHOR+' k h26ki[] k h26mu[] '+label+' '+CTX+']',
        'k h26m3[k h26m6[] '+AUTHOR+' k h26la[] k h26ki[] '+CTX+']',
        'k hzih[k h26nb[] k h26mv[] k h26mu[] '+CTX+']',
        'k ue[k h26mj[] k h26m4[] '+CTX+']','k ue[k h26m7[] k h26na[] '+CTX+']']
    nodes=(*NODE_INFO,'h26mj','h26la','h26mu','h26mv','h26mw','h26ki')
    parts+=['u[e[k '+x+'[]][k '+y+'[]]]' for i,x in enumerate(nodes) for y in nodes[i+1:]]
    return text+'d r5vv[] c['+both(*parts)+'].\n'
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[]
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r5vv',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new])
    basis=dict(status='named_epoch_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=MEANINGS,primitives={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/progress-indications-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    annotations['entries'].append(dict(symbol='h26mv',role='designation',forms=[
        dict(text='Friederichs',language='de',role='edition_transcription'),
        dict(text='Friedrich II.',language='de',role='editorially_identified_referent_name')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
