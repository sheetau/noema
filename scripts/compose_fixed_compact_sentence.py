"""Integrate the eighth sentence: fixed compacts, barrenness and posterity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_compact_causal_denial import NAMES as FIVE_NAMES,FIVE

PARENT='examples/v016/kant-provisional-order-sentence.noema'
PARENT_BASIS='data/provisional-order-sentence-basis-v1.json'
DEPENDENCIES=('data/persistent-compact-progress-basis-v1.json','data/compact-causal-denial-basis-v1.json','data/posterity-harm-basis-v1.json')
FULL='examples/v016/kant-fixed-compact-sentence.noema'
CORE='examples/v016/fixed-compact-sentence-core.noema'
BASIS='data/fixed-compact-sentence-basis-v1.json'
ANNOTATIONS='data/fixed-compact-sentence-identifiers-v1.json'
NAMES=('group',*FIVE_NAMES)
SIX='l[a]['+' '.join('v '+n for n in NAMES)+']'
ARGS=' '.join('v '+n for n in FIVE_NAMES)
FAMILY='i c[h[j[a] d] e]'
REF='k h26b7[]'
CTX='k h255n[]'
NODE_INFO={
 'h26fi':([2310,2677],'第八文全体。持続的で公に問い直せない宗教制度への合意の全面的不許可。'),
 'h26fj':([2310,2314],'冒頭Aberによる前文の暫定的可能性との対照。'),
 'h26fk':([2399,2445],'auch nur binnen der Lebensdauer eines Menschenという限定例の取り立て。'),
 'h26fl':([2540,2563],'gleichsam zu vernichtenという期間の消去への見立て。'),
 'h26fm':([2569,2578],'fruchtlosという改善の不在の結果。'),
 'h26fn':([2580,2634],'同じ不毛化から後世への害へ進む、推量を伴う因果的帰結。'),
 'h26fo':([2588,2592],'内側aberによる、不毛さから後世への害への対照。'),
 'h26fp':([2593,2597],'wohlによる第二の帰結への推量。'),
 'h26fq':([2598,2601],'garによる不毛さを越える帰結の取り立て。'),
 'h26fr':([2651,2666],'schlechterdingsによる例外なしの不許可の強調。'),
 'h26fs':([2468,2475],'最初のdadurchによる同じ合意実施から期間の不毛化への因果的帰結。'),
}
PRIMITIVES={
 'h26fb':('[a d d] c',['object','candidate','point'],'同じ対象が指定候補経過の指定点で存在する。意味領域の参照個体として名前があることと、その点で実在することを区別する。消失への変化、原因、対象の物理的種類は別に構成し、描写内の適用だけで現実の存在を断言しない。'),
 'h26fc':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','described','depiction','reference','context'],'著者が同じ全体と箇所で、範囲内の同じ対象列・固定基準について、記述した構成を別に記述した姿に見立てて提示する。内容の同義性、描写の字義的な現実性、描写対象の物理的実在は導かない。両内容は同じ束縛を受け、因果や主体・対象を別のものへ交換しない。'),
 'h26fd':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','baseline','focus','reference','context'],'著者が同じ全体・箇所・固定基準・範囲について、焦点内容を基準内容にとどまることを越える帰結として取り立てる。焦点に別に付けた推量や限定を保ち、実際の成立、高確率、数値的な程度差、基準内容の撤回を追加しない。'),
 'h26fe':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','baseline','focus','reference','context'],'著者が同じ全体・箇所・固定基準・範囲について、基準側の内容を受けて、焦点側をそれを越えて考慮すべき対照的な帰結として提示する。単なる順接と区別し、論理的矛盾、基準の撤回、焦点に付けた推量の解除は要求しない。'),
 'h26ff':('[a a i d[e] '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','denial','reference','context'],'著者が同じ全体と箇所で、明示した全対象範囲への同じ否定的規範判断を、例外を認めないものとして強調する。判断自体は別に構成する。範囲外の全行為への禁止、物理的不能、刑罰、数値的強度は追加しない。'),
 'h26fg':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','limited_scope','denial','reference','context'],'著者が同じ全体と箇所で、全対象範囲の中の明示した限定部分にまで同じ禁止判断が及ぶことを、限定してもなおという譲歩的な取り立てとして提示する。限定部分を全範囲に置き換えず、限定例の現実の存在や禁止の免除、数値的な最短期間を含意しない。部分範囲と全範囲の対応は別の構成で保つ。'),
 'h26fh':('[] a',[],'制度の同じ配置と公的な問い直しの禁止を相互の合意として形成する側の立場。全住民・聖職者だけ・国家の職制・同じ年齢の全員に限定しない。役割の指定から形成の実行や正当な権限を導かない。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0013['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r5kb':'正確な集団・合意・共同体・制度・公衆・期間の六対象列から、同じ全履歴の前後点で同じ期間対象が存在から不在へ変わるという字義的描写を返す。参照個体の存在と状況内存在を区別し、期間そのものが現実に消えるとは主張しない。',
 'r5kc':'同じ六対象列の期間消失r5kbと、同じ合意がこの同じ結果を生むh26asを結ぶ描写内容。合意の形成や現実の期間消失は全文の世界条件へ追加せず、見立て側で主体・対象・原因性を保持する。',
 'r5kd':'同じ六対象列と固定基準からr5jsの完全な当事者集団を持つ合意候補範囲を返す。形成・実施・不毛化・害が現に成立した候補だけへ限定しない。',
 'r5ke':'同じ六対象列から、人間の啓蒙・進展の規範h26axと相互合意形成の立場h26fhにおけるr5juの禁止を返す。引用対象は同じ全当事者による形成r5jtであり、成功結果だけを禁止しない。',
 'r5kf':'同じ六対象列から、その同じ合意に基づく方針の実施が同じ期間の不毛化に至るr5jrの帰結を返す。第一のdadurchの内容であり、後世への害という第二の帰結は含めない。',
 'r5kg':'同じ六対象列の先頭集団を除く五対象を、同じ期間の改善不在r5joへ射影する。不毛の結果と原因性を区別し、世界の期間消失を補わない。',
 'r5kh':'同じ候補範囲r5jsのうち、その同じ期間が同じ一人の人間の生涯内に収まるr5jiを満たす限定部分。期間を複数人の生涯の継ぎ合わせで覆わず、全範囲をこの部分に縮めない。',
 'r5ki':'固定基準h26b7で、全合意候補に対する人間の啓蒙・進展の規範と合意形成側の立場からの禁止r5jv、同じ全候補についての不毛化への因果的帰結r5jwを結ぶ。後世への害を無条件の帰結として連言せず、その推量は全文の提示側へ分ける。',
 'r5kj':'第八文の禁止と不毛化の一般命題を著者へ帰属し、前文との対照、一人の生涯内にまで及ぶ禁止、同じ期間の消去への見立て、推量を保った後代の害への対照と増幅、例外なしの禁止を同じ全体・基準・文脈へ結ぶ。各箇所の区別と文章順序を保持する。',
 'r5kk':'宗教制度配置が同じ政治的共同体に属するという性質。前文の暫定的な配置と現文の固定化を対照する共通観点に用い、同じ法や同じ実在合意であることを追加しない。',
}
LIMITS=[
 '第六段落u0013第八文[2310,2677)の320非空白文字を、先の暫定的可能性と対照する一般的な禁止として読む。持続する同じ宗教制度配置への合意と、誰にも公的な問い直しを許さない規範を保持する。心理的な疑いの不在・現実の全員一致・宣誓へ置換しない。',
 'beharrlichは同じ配置を全期間で持続させることと読み、有界と終点なしを共通のr5jfで扱う。auch nurはその全範囲のうち同じ一人の生涯内に収まる限定部分まで禁止が及ぶという焦点である。限定部分だけを禁止する読み、複数人の寿命の継ぎ合わせ、全人間の同一寿命は採らない。',
 '合意の全当事者は固定した複数人で、全住民や全人類とは同一視しない。禁止はその当事者による形成そのものにかかり、実際の実施・不毛化・被害の成功を待たない。規範の出所は先行文と同じ人間の啓蒙・進展の評価h26ax、立場は一般の制度固定化合意を形成する側h26fhに固定する。',
 'fruchtlosは同じ期間の全前後点で、人類の認識獲得・理由ある訂正・理由ある自己判断の三種類の改善がないという明示した強い読み。評価範囲・真偽基準・全人類を固定し、絶滅や未知を不毛さへ代用しない。期間維持は終了直前まで、改善比較は終了点を含む。',
 '最初のdadurchは同じ合意方針の適用・維持から同じ不毛化への因果的帰結。gleichsam zu vernichtenはこの働きを同じ期間対象の存在から不在への変化を起こす姿に見立てる。字義的消失は描写側だけに置き、現実の時間の消滅や人類の絶滅、結果の唯一原因を断言しない。',
 '後世の範囲・比較上の害・第二の因果関係はposterity-harmの明示読解を保持する。後世は合意の先行時代より後に生きる全員で、制度の終了後や血縁だけに限らない。害は同じ後代成員を保つ比較における知的継承・発展の機会の不利益で、全員の個別被害や任意の一人の被害ではない。',
 'wohlは第二の因果的帰結を確定せずに推量として提示する。内側aberは不毛さから後世の害への対照、garは単なる不毛さを越える帰結の増幅としてこの留保を保つ。第二の帰結を別に無条件の著者断言として加えず、客観的高確率や実際の被害を補わない。',
 'schlechterdingsは同じ全候補への例外なしの禁止を強調する。引用内容への著者帰属と各提示関係を構成し、著者の判断の客観的真理や現実の禁止の実施を証明したとはしない。原文全語句との通読は明示読解の下でのアシスタントの判断であり、テストからの自動同値証明や独立査読ではない。',
 '第八文の範囲のみを今回確認する。第六段落残部とアインシュタインを含む二作品全体は未完である。',
]
NODES=('h26ei',*NODE_INFO)

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    gone='g first d[g last d['+both('k h257z[v reference v candidate v first]','k h257z[v reference v candidate v last]',
        'k ic[v first v last v candidate]','k h26fb[v period v candidate v first]','u[k h26fb[v period v candidate v last]]')+']]'
    text='d r5kb[bindings j[a] reference d] e[b candidate['+bind(NAMES,gone)+']].\n'
    caused=both('t[k r5kb['+SIX+' v reference]][v candidate]','k h26as[v agreement r[p r5kb] '+SIX+' v reference v candidate]')
    scope='k r5js[v group '+ARGS+' v reference v candidate]'
    denial='k r5ju[k h26ax[] v group k h26fh[] '+ARGS+' v reference v candidate]'
    lifetime='g person a[g start d[g end d[k r5ji[v person v period v reference v candidate v start v end]]]]'
    for name,body in (('r5kc',caused),('r5kd',scope),('r5ke',denial),('r5kf','k r5jr['+ARGS+' v reference v candidate]'),
        ('r5kg','t[k r5jo['+FIVE+' v reference]][v candidate]'),('r5kh',both(scope,lifetime))):
        text+='d '+name+'[bindings j[a] reference d] e[b candidate['+bind(NAMES,body)+']].\n'
    text+='d r5ki[] e[b point['+both('t[k r5jv[k h26ax[] k h26fh[] '+REF+']][v point]','t[k r5jw['+REF+']][v point]')+']].\n'
    text+='d r5kk[regime a] e[b point[g community a[k h26cs[v regime v community '+REF+']]]].\n'
    a='k wa[]';whole='r d[k r5ki[]]';q=lambda n:'r c[p '+n+']'
    clauses=[
        'k h236i[k h26fi[] '+a+' '+whole+' '+CTX+']',
        'k h222q[k h26fj[] '+a+' k h26ei[] r b[k r5hv[]] k h26fi[] r b[k r5ki[]] r[p r5kk] '+CTX+']',
        'k h26fg[k h26fk[] '+a+' '+whole+' '+q('r5kd')+' '+q('r5kh')+' '+q('r5ke')+' '+REF+' '+CTX+']',
        'k h26fc[k h26fl[] '+a+' '+whole+' '+q('r5kd')+' '+q('r5kf')+' '+q('r5kc')+' '+REF+' '+CTX+']',
        'k r5ka[k h26fp[] '+a+' '+whole+' '+REF+' '+CTX+']',
        'k h26fe[k h26fo[] '+a+' '+whole+' '+q('r5j7')+' '+q('r5j4')+' '+q('r5j6')+' '+REF+' '+CTX+']',
        'k h26fd[k h26fq[] '+a+' '+whole+' '+q('r5j7')+' '+q('r5j4')+' '+q('r5j6')+' '+REF+' '+CTX+']',
        'k h26ff[k h26fr[] '+a+' '+whole+' '+q('r5kd')+' '+q('r5ke')+' '+REF+' '+CTX+']']
    edges=(('h26ei','h26fi'),('h26fj','h26fk'),('h26fk','h26fs'),('h26fs','h26fl'),('h26fl','h26fm'),('h26fm','h26fn'),('h26fo','h26fp'),('h26fp','h26fq'),('h26fn','h26fr'))
    clauses+=['k ue[k '+x+'[] k '+y+'[] '+CTX+']' for x,y in edges]
    distinct=['u[e[k '+x+'[]][k '+y+'[]]]' for i,x in enumerate(NODES) for y in NODES[i+1:]]
    clauses += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5kj[] c['+both(*clauses)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5kj',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='fixed_compact_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/provisional-order-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
