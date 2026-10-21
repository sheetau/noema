"""Integrate the cohort covenant sentence and its scoped supplementary presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_cohort_covenant_purpose import NAMES,FIELDS,ARGS,SIX,REF

PARENT='examples/v016/kant-covenant-nullity.noema'
PARENT_BASIS='data/covenant-nullity-basis-v1.json'
DEPENDENCY='data/cohort-normative-denial-basis-v1.json'
FULL='examples/v016/kant-cohort-covenant-denial.noema'
CORE='examples/v016/cohort-covenant-denial-core.noema'
BASIS='data/cohort-covenant-denial-basis-v1.json'
ANNOTATIONS='data/cohort-covenant-denial-identifiers-v1.json'
FAMILY='i[h[j[a]] e]'
CHANGE='i[h[j[a] d d] e]'
PRIMITIVES={
 'h26az':('[a h[a] c d d] c',['group','items','reference','point'],'同じ集団にとって、指定した全対象事項の領域を認識することが、自身の判断・行為・生き方に関わり、注意と探究を向けるべき切実な関心事となっている。金銭的価値や項目数、全員の実際の心理的興奮、全事項の認識済み・真理・同一の重要度ではない。対象範囲は固定し、関心があると判定できた項目だけを選ばない。程度は別に評価する。'),
 'h26ba':('[a a i d[e] '+FAMILY+' '+FAMILY+' d] c',['node','author','whole','scope','focus','context'],'著者が同じ全体の対象範囲と引数束縛の下で、指定の補足内容を特に注意すべき点として取り立てる。焦点内容は閉じた構成により与え、取り立てだけでその真理・唯一性・数値的な最大順位を追加しない。対象範囲を焦点の成功例だけへ縮めない。'),
 'h26bb':('[a a i d[e] '+FAMILY+' j['+CHANGE+'] '+CHANGE+' d] c',['node','author','whole','scope','details','general','context'],'著者が同じ全体・対象列・前後点・経過の下で、順序付きの個別の進展内容を挙げた上で、より一般的な観点からの進展内容へ論述を広げて提示する。個別内容と一般内容は閉じた関数で指定する。列挙の順序と総括の向きを保持し、個別の成功が一般内容を論理的に含意すること、三つの同時成功、完全な同義や列挙外の事実は追加しない。'),
 'h26bc':('[a a i d[e] '+FAMILY+' '+FAMILY+' d] c',['node','author','whole','scope','undertaking','context'],'著者が同じ全体と対象範囲の下で、指定の共同の引受けを、他者に不利益をもたらす企てへの結束として否定的に性格づけて提示する。結束・相互引受け・共同目的は指定内容で別に構成する。評価的な呼び方から秘密性、現実の成功、刑法上の罪名、全員の内心の一致を導かない。'),
 'h26bd':('[] a',[],'kant-1784:u0013[713,1004)のEin Zeitalterからschreiten.まで、後代を進展不能の状態へ置く合意の資格を否認する一文。'),
 'h26be':('[] a',[],'同原文[727,777)のkann sich nicht verbünden und darauf verschwören,という規範的否認と相互的結束の提示。'),
 'h26bf':('[] a',[],'同原文[859,896)の(vornehmlich so sehr angelegentliche)という認識の切実さを取り立てる括弧内補足。'),
 'h26bg':('[] a',[],'同原文[853,952)のseineからreinigen,まで、同じ後代の認識を拡げ誤りを取り除く対象箇所。'),
 'h26bh':('[] a',[],'同原文[952,1004)のund überhauptからschreiten.まで、啓蒙全般でさらに進むという総括的な展開。'),
 'h26bi':('[] a',[],'同原文[897,924)のErkenntnisse zu erweitern,という認識の拡大の箇所。'),
 'h26bj':('[] a',[],'同原文[924,952)のvon Irrthümern zu reinigen,という誤りの除去の箇所。'),
}
MEANINGS={
 'r5di':'同じ六対象の後続集団にとって、固定基準h26avの認識対象事項h26adの非空の全範囲が切実な関心事であるh26azを返す。seineの対象を先行当事者や別集団へ替えず、認識済みの真なる項目だけへ範囲を狭めない。',
 'r5dj':'同じ六個体列についてr5diの関心事であることと、その同じ性質への既存h225qの高程度評価を結ぶ。重要性だけで認識獲得や真理を代用せず、so sehrに数値的な尺度や最上級を補わない。',
 'r5dk':'中心命題と同じr5dcの全候補について、同じ後続集団の認識事項へのr5djの高い切実さを補足する内容。中心命題の規範条件をこの評価で選別し直さず、形成や目的の外側で認識改善の成功を要求しない。',
 'r5dl':'同じ六対象と明示した前後点から、後続集団の認識獲得r5coを同じ固定基準・真偽評価・候補経過へ結ぶ内容族。',
 'r5dm':'同じ六対象と前後点から、後続集団の理由ある誤りの訂正r5ciを同じ固定基準・真偽評価・候補経過へ結ぶ内容族。',
 'r5dn':'同じ六対象と前後点から、後続集団の理由ある自己判断による啓蒙進展r5crを同じ固定基準・候補経過へ結ぶ内容族。前二族と同じ三種類の選言r5csが不能性の内側で使われる。',
 'r5do':'中心命題r5dhと認識事項の切実さの補足r5dkを同じ著者・第六段落の文脈へ帰属し、括弧、特にという取り立て、個別二進展から啓蒙全般への総括、同じ目的付き相互宣誓の否定的な性格づけを結ぶ。前文との本文順序と箇所の区別を保つ。引用内容を現実の合意形成や達成の事実へ替えない。',
}
LIMITS=[
 'Ein Zeitalterを前後の全生存集団として読み、同じ区分の直後の時代をdas folgendeとする。全候補の目的付き相互宣誓形成について正当な資格を否認し、一つの実例の不存在や物理不能へ替えない。全範囲・全履歴・方法と結果の完全性に関する依存定義の意味規約を保持する。',
 '同じ合意の同じ当事者の引受け・宣誓・共同目的採用を結ぶ。目的内容の中で、同じ合意による原因性、後続時代内の状態成立、状態が成り立つ比較候補での進展不能を要求する。目的を述べる外側で成功・秘密性・誠実さ・全員の署名・代表権を追加しない。',
 '三種類の進展は、把握・真理・十分な根拠を伴う認識獲得、同じ偽の内容への理由ある訂正、通常の理由ある自己判断の新たな取得・広がりとして読む。どの方法にもどの結果・継続にもいずれの進展もないことを不能性とし、一つの固定経過だけの停滞や三種類を同時達成できないことに弱めない。',
 'seineは同じ後続集団の認識を指す。括弧を、認識対象事項が後代自身にとって非常に切実であることを特に取り立てる補足として読む。教会の教義だけや重要と既知の項目だけへ対象を狭めず、全事項が真・全員が既に知る・全員が強い感情を持つとも言わない。vornehmlichは焦点、so sehrは高程度であり、数値順位や最上級は追加しない。',
 'überhauptは認識の拡大と訂正の二つを挙げた上で、啓蒙一般の進展へ論述を広げる提示として読む。自己判断と認識獲得を同義にせず、知識が増えれば必ず自立するという含意を補わない。列挙の各進展は同じ対象・前後点・経過で不能性の内側に保持する。',
 'verschwörenは先の相互的な誓約を受けつつ、後代を害する企てへの結束として否定的に描くものと読む。辞書の現代的な秘密結社の意味を必須の事実条件にせず、古い誓約の用法とこの文脈の評価を区別する。',
 '原刊488頁を再読し、AA VIII 39の対応箇所も照合した。原刊の綴りと固定原文の表記を保持する。現代辞書は語義の区別の補助であり、それだけで十八世紀の一意の読みを証明したとはしない。',
 'これは原文一文について明示した読解の下で行うアシスタントの意味判断であり、原著者の規範判断の真理、自動同値性証明、独立査読、言語の万能性を主張しない。後続文の人間本性からの理由付けと第六段落全体の確認は残る。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
WHOLE='r d[k r5dh[]]'
CTX='k h255n[]'
def definitions():
    items='i[item a][k h26ad[v item '+REF+']]'
    importance=both('g item a[k h26ad[v item '+REF+']]','k h26az[v nextgroup '+items+' '+REF+' v point]')
    text='d r5di[bindings j[a]] e[b point['+bind(NAMES,importance)+']].\n'
    text+='d r5dj[bindings j[a]] e[b point['+both('t[k r5di[v bindings]][v point]','k h225q[r d[p r5di] v bindings v point]')+']].\n'
    supplement='y[k r5dc['+ARGS+' v point]][t[k r5dj['+SIX+']][v point]]'
    for n in reversed(NAMES):supplement='f '+n+' a['+supplement+']'
    text+='d r5dk[] e[b point['+supplement+']].\n'
    for name,target in (('r5dl','r5co'),('r5dm','r5ci'),('r5dn','r5cr')):
        fields='v nextgroup '+REF+(' k h26ar['+REF+']' if target!='r5cr' else '')+' v candidate v first v last'
        text+='d '+name+'[bindings j[a] first d last d] e[b candidate['+bind(NAMES,'k '+target+'['+fields+']')+']].\n'
    a='k wa[]';whole='k h26bd[]';scope='r[p r5df]'
    clauses=['k h236i['+whole+' '+a+' '+WHOLE+' '+CTX+']',
        'k h236i[k h26bf[] '+a+' r d[k r5dk[]] '+CTX+']',
        'k h234k[k h26bf[] '+a+' '+whole+' '+CTX+']',
        'k h26ba[k h26bf[] '+a+' '+WHOLE+' '+scope+' r[p r5dj] '+CTX+']',
        'k h26bb[k h26bh[] '+a+' '+WHOLE+' '+scope+' l['+CHANGE+'][r[p r5dl] r[p r5dm]] r[p r5dn] '+CTX+']',
        'k h26bc[k h26be[] '+a+' '+WHOLE+' '+scope+' r[p r5db] '+CTX+']']
    for left,right in (('h257r','h26bd'),('h26be','h26bg'),('h26bf','h26bi'),('h26bi','h26bj'),('h26bj','h26bh')):
        clauses.append('k ue[k '+left+'[] k '+right+'[] '+CTX+']')
    nodes=('h257r','h26bd','h26be','h26bf','h26bg','h26bh','h26bi','h26bj')
    clauses+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r5do[] c['+both(*clauses)+'].\n'
    return text

def build():
    old,lib=parent(),dependency();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for d in lib.document['declarations']:
        n=d['name'];previous=old.entries.get(n)
        if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5do',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='cohort_covenant_denial_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/covenant-nullity-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
