"""Integrate civic freedom, nonfactive advantage, barriers and development room."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_prince_sentence import ANCHOR

PARENT='examples/v016/kant-whole-view-sentence.noema';PARENT_BASIS='data/whole-view-sentence-basis-v1.json'
DEPENDENCY='data/faculty-development-room-basis-v1.json'
FULL='examples/v016/kant-civic-spirit-sentence.noema';CORE='examples/v016/civic-spirit-sentence-core.noema'
BASIS='data/civic-spirit-sentence-basis-v1.json';ANNOTATIONS='data/civic-spirit-sentence-identifiers-v1.json'
C5='i f[e]';F3='i e[h[a a a] e]';F4='i e[h[a a a a] e]';F2='i e[h[a a] e]';DOMAIN='i[h[a a a] c]'
REF='k h26zj[]';CTX='k h26zk[]';AUTHOR='k wa[]'
FIELDS='community a lowerorder a higherorder a';ARGS='v community v lowerorder v higherorder'
PRIMITIVES={
 'h26zi':('[a a a d] c',['community','lowerorder','higherorder','reference'],'固定基準で第三文が一般的な比較として扱う、共同体と二法秩序の全組。比較の成功・見かけ・制限・発展機会によって事後選別しない。文脈上の比較事例の非空範囲を指定し、同時に存在する二国家や全歴史の全制度を意味しない。大小はこのラベルでなくr6hgの同じ許可集合で確認する。'),
 'h26zj':('[] d',[],'第十段落第三文の比較対象・成員・市民的行為・精神的課題・能力範囲・候補・因果機構を共有する固定解釈基準。先行文の基準を無言で変更せず、第三文の一般化範囲を明示する。本文現在と提示文脈とは分ける。'),
 'h26zk':('[] d',[],'固定原文kant-1784:u0017第三文の論述提示文脈。評価の本文現在と解釈基準を区別する。'),
 'h26zl':('[a a '+C5+' '+DOMAIN+' '+F3+' '+F3+' '+F3+' d] c',['node','author','whole','domain','premise','retained','combined','context'],'著者が同じ全体の同じ三引数の範囲において、第一内容から第二内容を退ける見通しに反して第二をなお保ち、両者を合わせた内容を提示する譲歩的な対照。h236lと同じ提示の役割を三引数・段階4の内容族で扱う。第一の否定、論理矛盾、全読者の心理的期待、数値確率又は焦点の真理をこの帰属から導かない。'),
 'h26zm':('[a a '+C5+' a '+F4+' d] c',['node','author','whole','antecedent','referent','context'],'著者が同じ全体のこの照応箇所で、指定先行箇所の同じ四引数の性質を指す。引数の順・作用域・基準を保ち、別の性質や現実の実行へ交換しない。渡した閉じた記述が参照内容を構成する。'),
 'h26zn':('[a a '+C5+' a '+F3+' d] c',['node','author','whole','antecedent','referent','context'],'著者が同じ全体のこの照応箇所で、指定先行箇所の同じ三引数の性質を指す。人物・対象・固定基準を保持し、表面上似た別の内容へ取り替えない。参照する性質は渡した閉じた記述で構成し、引用の真理を実行しない。'),
 'h26zo':('[a a '+C5+' a '+F2+' d] c',['node','author','whole','antecedent','referent','context'],'著者が同じ全体のこの照応又は再帰箇所で、指定先行箇所の同じ二引数の性質が表す対象を指す。受け手と展開する本人を別対象にせず、各引数に対応する成員と基準を維持する。現実の実行は追加しない。'),
 'h26zp':('[a a '+C5+' a '+F2+' '+F3+' d] c',['node','author','whole','antecedent','owner','possessed','context'],'著者が同じ全体の所有照応で、指定先行箇所の二引数の対象を所有側とし、それら同じ二引数に第三の所有対象引数を加えた性質を結ぶ。所有関係自体は渡す性質内で構成し、別人・別集団の所有物へ取り替えない。'),
}
NODE_INFO={
 'h26zq':([467,715],'第三文全体。'),'h26zr':([467,610],'高い側の見かけの利益と実際の制限。'),
 'h26zs':([611,715],'低い側での発展の余地。'),'h26zt':([467,506],'より大きな市民的自由の度合い。'),
 'h26zu':([507,562],'精神的自由に有利に見えるという内容。'),'h26zv':([515,549],'民衆の精神的自由。'),
 'h26zw':([532,549],'同じ民衆の精神。'),'h26zx':([564,609],'同じ高い側が課す越えがたい制限。'),
 'h26zy':([574,577],'ihrの精神的自由への照応。'),'h26zz':([578,582],'dochの譲歩的対照。'),
 'h26z2':([611,637],'同じ比較の低い側。'),'h26z3':([632,637],'jenerの市民的自由への照応。'),
 'h26z4':([648,656],'hingegenの二制度側の対照。'),'h26z5':([657,663],'diesemの同じ精神への照応。'),
 'h26z6':([664,668],'Raumの展開機会。'),'h26z7':([670,674],'sichの同じ精神への再帰。'),
 'h27aa':([675,701],'nach allem seinen Vermögenの全関連能力への範囲。'),
 'h27ab':([686,692],'seinenの同じ精神に属する能力への所有照応。'),'h27ac':([702,714],'auszubreitenの固定課題範囲への展開。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0017['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
MEANINGS={
 'r6ic':'同じ三引数の共同体・二法秩序と第三文の固定基準に、著者が提示する観点でのr6hsの非事実的な見かけを結ぶ内容族。見かけを実際の利益へ昇格させない。',
 'r6id':'同じ三引数・基準・評価点でのr6hwの非空全対象への因果的な制限を取り出す内容族。',
 'r6ie':'同じ三引数・基準・評価点でのr6hxの見かけと制限の連言。dochの提示が指す合成内容と高い側の内容を共用する。',
 'r6if':'同じ三引数・基準・評価点で、低い側の発展機会r6h7と高い側制限対象との対応r6iaを合わせる内容族。',
 'r6ig':'同じ三引数・基準・著者の提示観点のr6ib。r6ieとr6ifを同じ比較起点で結ぶ第三文の全命題内容族。',
 'r6ii':'第三文の固定基準で指定した同じ共同体・低い側・高い側の全比較範囲。結果に応じた抽出はしない。',
 'r6ih':'非空の固定した全比較組について、同じ本文現在でr6igの見かけ・制限・低い側の余地が成立するという第三文の一般化した内容。範囲外の全歴史的制度への普遍法則や二国家の実在を付加しない。',
 'r6ij':'r6ihと同じ非空の全比較範囲と本文現在で、高い側のr6ieを取り出す内容。独立に選んだ別の比較へ切り替えない。',
 'r6ik':'r6ihと同じ非空の全比較範囲と本文現在で、低い側のr6ifを取り出す内容。全内容はこの両側の連言に一致する。',
 'r6il':'第三文の固定基準で、共同体・法秩序・本人・市民的行為のr6hfの積極的許可と反対要求の不在を取り出す性質。jenerが受ける市民的自由の具体的な参照内容。',
 'r6im':'第三文の固定基準で、同じ共同体・本人・課題についてr6hiの自分の悟性による理由ある判断の達成機会を取り出す性質。ihrが受ける精神的自由の参照内容。',
 'r6in':'第三文の同じ共同体の人間成員が、関連する本人所有の精神的能力を少なくとも一つ持つ性質。精神を同じ民衆の各人の判断能力へ分配する明示した読みであり、独立した超個人的実体を導入しない。',
 'r6io':'r6inと同じ共同体・本人・基準について、その人に属する全関連能力の一つであり本人が所有するという性質。seinenの所有照応を、発展目標でも使う同じabに接続する。',
 'r6ip':'第三文の全内容と二側を同じ著者へ帰属し、dochの同じ範囲での譲歩的対照、hingegenの二側の対照、五つの代名詞の性質への照応、先行第二文からの本文順序を保持する。引用内容を現実の真理として実行しない。',
}
LIMITS=[
 '固定原文u0017第三文[467,715)・215非空白文字全体を対象とする。原刊493頁との保存済み照合を用い、verschaftなどの綴りを変更しない。明示した比較範囲での一般化として読み、範囲を結果から選ばず、非空の全組へ同じ条件を適用する。世界中の全制度・時代の無条件の普遍法則や実在二国家の比較は付加しない。',
 'bürgerliche Freiheitの度合いは、同じ民衆・市民的行為・役割・基準について、同じ公的法秩序の積極的許可から反対要求を除いた集合の真包含で比較する。ein Grad wenigerはその比較の低い側であり、数値一単位又は隣接する最小刻みを要求しない。',
 'Geist des Volksを同じ民衆各人の自分の悟性による判断の働きへ分配する。Freiheit des Geistesは固定した課題に属する全事項への理由ある判断の達成機会、Vermögenは本人所有の関連能力の全範囲とする。超個人的な集合精神やあらゆる心理機能の唯一の定義とはしない。',
 'scheintは非空の表面的情報の全候補で同じ内容が成立する非事実的な見かけ。有利さは同じ課題機会の真包含拡大であり、現実の利益や見かけの必然的な誤りを補わない。高い側の市民的自由の大小は実際の比較点でも確認する。',
 'setzt … unübersteigliche Schrankenは、同じ因果モデルの高い側の非空全解で指定課題を評価済みで達成できず、低い側の少なくとも一解で達成機会がある制度的な制限と読む。高い側の非介入観測と現在の不能も保持する。未知の方法を不能とせず、全精神活動や全未来の絶対的不能へ強めない。',
 'Raum … auszubreitenは、同じ低い側の制度の下で、本人の全関連能力について固定した潜在的な全課題へ到達する機会と読む。既に行使できる能力には維持を認め、全体には評価済み未達課題を求める。全履歴で法秩序と市民的許可集合を維持し、実際の発展・同時の共同計画・各能力の厳密増大は要求しない。',
 'Schranken・Raum・auszubreitenはこの箇所では抽象的な制限・可能性・能力範囲の展開を表す用法として解釈する。別個の身体的な柵越え、部屋の広さ、物体の膨張を描写する独立内容は立てない。精神的機会の定義を空間語の単なるラベルで代用することとは区別する。',
 'dochは有利に見えることから制限を退ける見通しに反して制限をなお提示する譲歩的な対照、hingegenは高い側の見かけと制限を合わせた内容と低い側の余地の対照と読む。利益と一部の制限は両立し得るため論理的矛盾を要求せず、実際の読者の期待や数値確率を補わない。',
 'ihrは先行する精神的自由、jenerは先行する市民的自由、diesemとsichは同じ民衆の精神、seinenは同じ精神の働きを担う本人の能力へ結ぶ。対比と展開の各内容で共同体・本人・課題・能力・基準を替えない。前文からの説明的な連続は本文順序で保持し、前文からの形式的導出や同一の特定君主・共和国をこの一般比較に補わない。',
 '全語句と文全体の通読判断はアシスタントの明示した解釈によるもので、機械的同義性証明や独立査読ではない。既存121主張と19全単位判断・第一第二文の判断を保存する。第四文、u0017全体とEinstein全文の完成は別に残る。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def node(n):return 'k '+n+'[]'
def code(n):return 'r f[k '+n+'[]]'
def profile(n):return 'r e[p '+n+']'

def definitions():
    ctx=ARGS+' '+REF+' v point';text=''
    targets={'r6ic':'t[k r6hs['+AUTHOR+' '+ARGS+' '+REF+']][v point]',
      'r6id':'k r6hw['+ctx+']','r6ie':'t[k r6hx['+AUTHOR+' '+ARGS+' '+REF+']][v point]',
      'r6if':both('k r6h7['+ctx+']','k r6ia['+ctx+']'),
      'r6ig':'t[k r6ib['+AUTHOR+' '+ARGS+' '+REF+']][v point]'}
    for n,body in targets.items():text+='d '+n+'['+FIELDS+'] e[b point['+body+']].\n'
    text+='d r6ii['+FIELDS+'] c[k h26zi['+ARGS+' '+REF+']].\n'
    selected='k r6ii['+ARGS+']';nonempty='g community a[g lowerorder a[g higherorder a['+selected+']]]'
    for n,part in (('r6ih','r6ig'),('r6ij','r6ie'),('r6ik','r6if')):
        text+='d '+n+'[] e[b outer['+both(nonempty,
          'f community a[f lowerorder a[f higherorder a[y['+selected+'][t[k '+part+'['+ARGS+']]['+ANCHOR+']]]]]')+']].\n'
    text+='d r6il[community a order a person a activity a] e[b point[k r6hf[v community v order v person v activity '+REF+' v point]]].\n'
    text+='d r6im[community a person a task a] e[b point[k r6hi[v community v person v task '+REF+' v point]]].\n'
    owned=both('k r6hd[v person v community '+REF+']','k h26zb[v community v person v faculty '+REF+']','k ab[v faculty v person v point]')
    text+='d r6io[community a person a faculty a] e[b point['+owned+']].\n'
    text+='d r6in[community a person a] e[b point[g faculty a[t[k r6io[v community v person v faculty]][v point]]]].\n'
    whole=code('r6ih');parts=['k h26ub['+node(n)+' '+AUTHOR+' '+code(c)+' '+CTX+']' for n,c in (('h26zq','r6ih'),('h26zr','r6ij'),('h26zs','r6ik'))]
    parts+=['k h26zl['+node('h26zz')+' '+AUTHOR+' '+whole+' r[p r6ii] '+profile('r6ic')+' '+profile('r6id')+' '+profile('r6ie')+' '+CTX+']',
      'k h26uc['+node('h26z4')+' '+AUTHOR+' '+whole+' '+code('r6ij')+' '+code('r6ik')+' '+CTX+']',
      'k h26zm['+node('h26z3')+' '+AUTHOR+' '+whole+' '+node('h26zt')+' '+profile('r6il')+' '+CTX+']',
      'k h26zn['+node('h26zy')+' '+AUTHOR+' '+whole+' '+node('h26zv')+' '+profile('r6im')+' '+CTX+']']
    parts+=['k h26zo['+node(n)+' '+AUTHOR+' '+whole+' '+node('h26zw')+' '+profile('r6in')+' '+CTX+']' for n in ('h26z5','h26z7')]
    parts+=['k h26zp['+node('h27ab')+' '+AUTHOR+' '+whole+' '+node('h26zw')+' '+profile('r6in')+' '+profile('r6io')+' '+CTX+']']
    for a,b in ORDER:
        parts+=['u[e['+node(a)+']['+node(b)+']]','k ue['+node(a)+' '+node(b)+' '+CTX+']','u[k ue['+node(b)+' '+node(a)+' '+CTX+']]']
    return text+'d r6ip[] c['+both(*parts)+'].\n'

ORDER=(('h26yd','h26zq'),('h26zr','h26zs'),('h26zu','h26zx'),('h26zt','h26z3'),('h26zv','h26zy'),('h26zw','h26z5'),('h26z5','h26z7'),('h26z7','h27ab'),('h26z2','h26z4'),('h26z4','h26z6'),('h26z6','h27aa'),('h27aa','h27ac'))
def build():
    old=parent();lib=dependency();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for d in closure(lib.document,('r6ib',)):
        n=d['name'];e=lib.entries[n];prior=old.entries.get(n)
        if prior:assert d==prior['declaration'] and e['meaning_ja']==prior['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6ip',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='civic_spirit_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
      new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/whole-view-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
