"""Integrate the entire provisional-order sentence under an explicit generic reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_provisional_self_legislation import NAMES,ARGS,REF

PARENT='examples/v016/kant-legislative-touchstone.noema'
PARENT_BASIS='data/legislative-touchstone-basis-v1.json'
DEPENDENCIES=('data/provisional-self-legislation-basis-v1.json','data/civic-participation-discourse-basis-v1.json','data/protective-petition-discourse-basis-v1.json')
FULL='examples/v016/kant-provisional-order-sentence.noema'
CORE='examples/v016/provisional-order-sentence-core.noema'
BASIS='data/provisional-order-sentence-basis-v1.json'
ANNOTATIONS='data/provisional-order-sentence-identifiers-v1.json'
FRAME='i b[h[j[a] d d d d] e]'
SCOPE='i[h[j[a]] e]'
QUESTION='i b[h[j[a]] f]'
POSSIBLE='i b[h[j[a] d] e]'
PROJECTION='i[h[j[a] j[a]] c]'
CTX='k h255n[]'
NODE_INFO={
 'h26ei':([1437,2309],'第七文全体、Nun wäreからbewenden lassen.まで。'),
 'h26ej':([1446,1452],'diesesによって直前の自己賦課の問いを受ける箇所。'),
 'h26ek':([1453,1457],'wohlによって、後続条件の下で可能性を肯定する箇所。'),
 'h26el':([1459,1499],'gleichsam in der Erwartung eines bessernという期待への見立て。'),
 'h26em':([1617,1644],'vornehmlich dem Geistlichenという聖職者への取り立て。'),
 'h26en':([1690,1700],'öffentlichという公的使用の特徴。'),
 'h26eo':([1702,1723],'d. i. durch Schriftenという同じ公的使用の書面による説明。'),
 'h26ep':([2001,2026],'(wenn gleich nicht aller)という全員参加を必須にしない括弧内譲歩。'),
 'h26eq':([1961,2071],'daß sieからbringen könnteまで、同じ市民の声を合わせた提案可能性。'),
 'h26er':([2043,2056],'vor den Thronという公的な宛先を王座によって指す箇所。'),
 'h26es':([2073,2116],'um diejenigen Gemeinden in Schutz zu nehmenという同じ共同提案の保護目的。'),
 'h26et':([2118,2232],'die sich etwaからgeeinigt hättenまで、本人たちの認識に従う改革合意による仮定的な対象選択。'),
 'h26eu':([2234,2309],'ohne dochからbewenden lassen.まで、旧配置の維持を望む共同体への非妨害の留保。'),
 'h26ev':([1965,2000],'sie durch Vereinigung ihrer Stimmenという、公的洞察が市民の声を通じて働くという表現。'),
}
PRIMITIVES={
 'h26ef':('[a a i d[e] '+FRAME+' d] c',['node','author','whole','qualification','context'],
   '著者が同じ全体内容の指定箇所で、指定した限定条件を保った場合の可能性を、差し当たり認めるという譲歩的な肯定の調子で提示する。限定条件は同じ対象列・固定真偽評価・候補・開始・終了を受ける閉じた内容族で与える。無限定の全面的承認、数値確率、必然性、条件の現実の実施、別の箇所で述べる対照内容の先取りを加えない。'),
 'h26eg':('[a a i d[e] '+SCOPE+' '+FRAME+' '+FRAME+' d] c',['node','author','whole','scope','described','depiction','context'],
   '著者が同じ全体内容の指定箇所で、範囲内の同じ対象列について、記述された構成を別に記述した態度の姿になぞらえて提示する。両内容族は同じ固定真偽評価・候補・開始・終了を受け、実際の構成の主体・活動・対象を描写側でも保つ。見立てから字義的な態度の現実の成立、態度対象の到来や成功を加えず、構成と態度を同義にはしない。'),
 'h26eh':('[a a a '+QUESTION+' '+QUESTION+' '+PROJECTION+' '+POSSIBLE+' '+SCOPE+' i d[e] d] c',
   ['node','author','antecedent_node','antecedent_question','lifted_question','projection','qualified_possibility','scope','whole','context'],
   '著者が指定箇所で先行する同じ問いを受け、その問いを同じ対象へ引き継いだ上で、限定された可能性を現在の全体内容として述べる。先行の対象列と現在の対象列の対応は閉じた射影関係で指定し、持ち上げた問い・限定可能性・範囲は現在の同じ対象列を用いる。別の人民や別の法への問いへ替えず、先行範囲の全法案への無条件の肯定や、読者に実際に答えさせる行為にはしない。'),
 'h26ew':('[a a i d[e] '+SCOPE+' '+FRAME+' '+FRAME+' d] c',
   ['node','author','whole','scope','public_cognition','collective_capacity','context'],
   '著者が同じ全体内容・範囲で、公的な認識の状態を、対応する人々の共同の声と行為能力を通じて働く主体のように提示する。二つの閉じた内容族へ同じ対象列・固定真偽評価・候補・開始・終了を渡し、同じ集団・事柄・提案能力への対応を保つ。抽象的な認識状態に身体や独立した人格があること、全成員が全ての認識内容を個別に知ること、現実の共同行為は追加しない。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0013['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r5hq':'正確な十対象列・固定真偽評価・候補・開始・終了について、r5gsの規範的に許される同じ人民の短期の自己賦課と、制度・批評自由・導入目的・洞察到達を返す限定内容。外側の評価点を変えて候補や期間を選び直さない。',
 'r5hr':'r5hqと同じ十対象列・真偽評価・候補・開始・終了の入力から、固定基準h26b7とその同じ候補・開始点でr5gwの期待描写を返す。よりよい法の期待は同じ人民・採択活動・元の法へ結び、期間終端で実現するという追加はしない。',
 'r5hs':'正確な十対象列の先頭三対象について、前文と同じr5esの自己賦課可能性を問う正極性の問い。r5gxを用いて前文のr5euをこの対象列へ持ち上げる。問いを提示しても肯定回答や実際の自己賦課を断定しない。',
 'r5ht':'正確な十対象列と、その先頭の人民・共同体・法からなる正確な三対象列の対応関係。照応時に人民や法を取り替えず、余分な対象を含む列も認めない。自然言語ラベルによる参照ではなく構成した射影関係である。',
 'r5hu':'同じ人民・政治的共同体について、法・制度・採択活動・領域・公衆・提案集団・公的宛先・政策の一組が存在し、固定真偽評価h26ar(h26b7)の下でr5gtの暫定的自己賦課可能性を満たす。各対象を別々の成功例から集めず、任意の全法案の許容や同じ法が全人民に共通することは要求しない。',
 'r5hv':'固定基準h26b7でr45dの完全な人民・政治的共同体を成す全組について、r5huの条件を満たす暫定的な法と実施構成があり得るという一般命題。人民ごとの一般的な可能性として採る読み。現在の各国で直ちに実施できること、現実の採択、全ての法律・制度・候補での成功を主張しない。',
 'r5hw':'第七文の一般的な可能性r5hvを同じ著者と第六段落の提示文脈へ帰属する。前文の自己賦課の問いへの照応、Nunの説明的な展開、wohlの限定付き肯定、期待への見立て、全市民の自由を保つ取り立てと書面の説明、非全員の譲歩、保護目的・仮定的な改革対象・非妨害の留保・王座の換喩を同じ全体内容へ接続し、文章順序と箇所の区別を保つ。引用した世界内容を実行しない。',
 'r5hx':'同じ十対象列・固定真偽評価・候補・開始・終了から、終了点で同じ政策の共同提案に十分となる公的洞察の到達r5gpを返す。公的洞察を主体のように述べる提示の認識側であり、別集団の能力や別の認識状態へ替えない。',
 'r5hy':'同じ十対象列・固定真偽評価・候補・開始・終了のうち、同じ提案集団・共同体・宛先・政策・候補・終了点のr5gkの能力を返す。r5hxの到達内容に対応する共同の声による提案能力であり、実際の提出や全員の個人的知識を追加しない。',
}
LIMITS=[
 'u0013第七文[1437,2309)の747非空白文字。原刊489頁を再読し、同じ法の暫定的な自己賦課、全市民の批評自由、洞察と共同提案、改革側への保護と維持側への非妨害を一つの可能性の構成として読む。',
 '直前の任意のein Volkを受け、人民・政治的共同体の組について一般化する。その各組に、後続条件を満たして許容される暫定的な法・制度・実施構成があり得るという読みを採る。法以下の八対象は人民の全称の内側で存在量化する。あらゆる法案が短期なら許容されるという読み、たった一つの特定国の出来事、現実の各国で現在ただちに実行できるという読みにはしない。',
 '一般化の範囲はr45dの完全な人民であり、成功が既知の人民に絞らない。候補の制度配置は既存h26cfの反事実的範囲を用いる。現行の統治形態や賛否を固定しないため、現在の制度的権能や物理的能力の主張ではない。これは明示した一般的読解であり、自然言語の総称を一意に決定したとの主張ではない。',
 'diesesは直前の同じ人民による同じ法の自己賦課の可能性を受ける。十対象から先頭三対象への射影r5htと、持ち上げた同じ問いr5hsにより前文のr5euへ接続する。先行する全法案への肯定回答を一括して与えない。Nunは先行する問い・基準から暫定例へ論述を進める説明的な展開としてufへ結び、暦上の現在を補わない。',
 'wohlは限定条件の下なら可能性を認める譲歩的な肯定の調子と読む。次文のAberによる不許可例と対照されるが、その次文の内容をこの文の既確認部分には加えない。前文の疑問的なwohlと同じ作用にせず、数値確率や必然性へ置き換えない。',
 'gleichsam in der Erwartungは同じ暫定構成を、よりよい法の到来を待つ態度になぞらえる描写と読む。eines bessernは前文のGesetzを受けるよりよい法。比較・未来性・同じ人民と活動を保持するが、実際の心理的期待、全員一致の内心、改善法の到来を本文の可能性へ連言しない。',
 '一定の短期は導入時に定まる期間と文脈上の短さを別に要求する。indem・zugleich・indessenは同じ候補の同じ期間に制度と全市民の批評自由を保つことへ結ぶ。期間の終点は公的洞察の同じ到達内容が初めて成立する点という採用読解であり、終点後の廃止や現実の必然到達を追加しない。',
 '全市民の書面批評の自由は、非空の全批評候補への積極的許可と反対要求の不在という既存構成を保持する。聖職者は焦点であって対象範囲の制限ではない。d. i.は同じ公的使用の書面による説明であり、書面一般と公的使用一般の無限定の同値ではない。',
 '公的洞察は同じ制度・関連認識内容についての把握・根拠・公開・確証を含む。十分な程度は、認識以外の背景を固定した比較で、以前の認識ではできなかった同じ共同提案が、到達後の内容以上を持つ全比較点で可能になるというinsight-thresholdの明示した強い質的読解を保持する。比較範囲の現実的な網羅性は入力責任であり、数値・唯一の最小閾値の主張ではない。',
 '提案集団は同じ市民の二人以上で、全員でも一部でもよい。同じ声・行為・政策・公的宛先を保持し、代表による提出を排除しない。Thronは公的統治者への換喩として描写を分け、椅子の存在・身体的位置・対面・採用・保護の成功を可能性から導かない。',
 'daß sie ... bringen könnteの単数形は直前のEinsichtを受けると読む。公的な洞察が市民の声を通じて提案能力を持つという主体的な描写を、同じ洞察r5hxと集団の能力r5hyの対応として保持する。sieを無説明に複数の市民へ置換せず、抽象的洞察の物理的発声や全成員の全知識を加えない。',
 '保護対象は本人たちの認識に従った改革合意、非妨害対象は旧配置を維持したい肯定的意向で独立に選ぶ。選択点を固定し、結果の成功で選び直さない。etwaと接続法を仮定的な対象として扱い、現実の改革共同体の存在を追加しない。同じ政策の保護目的と非妨害の留保を共に保持する。',
 '全てを同じ著者への記述として提示し、引用から世界内容を実行しない。通読による判断は明示読解下でのアシスタントの判断であり、テストからの自動同値認定、独立査読、唯一の読解や著者の規範判断の真理の証明ではない。第六段落全体と二作品全体は未完。',
]
NODES=('h26co','h26cq',*NODE_INFO)

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    frame='bindings j[a] assessment d candidate d start d end d'
    text='d r5hq['+frame+'] e[b point['+bind(NAMES,'k r5gs['+ARGS+' v assessment v candidate v start v end]')+']].\n'
    text+='d r5hr['+frame+'] e[b point[t[k r5gw[v bindings '+REF+' v candidate v start]][v point]]].\n'
    text+='d r5hs[bindings j[a]] f[k rij[k r5gx[v bindings] '+TRUE+']].\n'
    projection='e[v prior][l[a][v people v community v law]]'
    text+='d r5ht[bindings j[a] prior j[a]] c['+bind(NAMES,projection)+'].\n'
    cognition='k r5gp[v group v community v regime v field v audience v recipient v policy '+REF+' v assessment v candidate v start v end]'
    capacity='k r5gk[v group v community v recipient v policy '+REF+' v candidate v end]'
    for root,body in (('r5hx',cognition),('r5hy',capacity)):
        text+='d '+root+'['+frame+'] e[b point['+bind(NAMES,body)+']].\n'
    possible='k r5gt['+ARGS+' k h26ar['+REF+']]'
    for n in reversed(NAMES[2:]):possible='g '+n+' a['+possible+']'
    text+='d r5hu[people a community a] c['+possible+'].\n'
    text+='d r5hv[] e[b point[f people a[f community a[y[k r45d[v people v community '+REF+']][k r5hu[v people v community]]]]]].\n'
    a='k wa[]';whole='r d[k r5hv[]]';q=lambda n:'r b[p '+n+']'
    clauses=[
        'k h236i[k h26ei[] '+a+' '+whole+' '+CTX+']',
        'k h26eh[k h26ej[] '+a+' k h26cq[] '+q('r5eu')+' '+q('r5hs')+' r[p r5ht] '+q('r5gu')+' r[p r5gv] '+whole+' '+CTX+']',
        'k uf['+a+' k h26co[] k h26ei[] '+CTX+']',
        'k h26ef[k h26ek[] '+a+' '+whole+' '+q('r5hq')+' '+CTX+']',
        'k h26eg[k h26el[] '+a+' '+whole+' r[p r5gv] '+q('r5hq')+' '+q('r5hr')+' '+CTX+']',
        'k h26ew[k h26ev[] '+a+' '+whole+' r[p r5gv] '+q('r5hx')+' '+q('r5hy')+' '+CTX+']',
        'k r5hc[k h26em[] k h26en[] k h26eo[] '+a+' '+whole+' '+CTX+']',
        'k r5hd[k h26ep[] k h26eq[] '+a+' '+whole+' '+CTX+']',
        'k r5hp[k h26er[] k h26es[] k h26et[] k h26eu[] '+a+' '+whole+' '+CTX+']']
    edges=(('h26co','h26ei'),('h26ej','h26ek'),('h26ek','h26el'),('h26el','h26em'),('h26eo','h26eq'),('h26ev','h26ep'),('h26ep','h26er'))
    clauses+=['k ue[k '+x+'[] k '+y+'[] '+CTX+']' for x,y in edges]
    distinct=['u[e[k '+x+'[]][k '+y+'[]]]' for i,x in enumerate(NODES) for y in NODES[i+1:]]
    # Group independent inequalities to remain below the syntax nesting limit.
    clauses += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5hw[] c['+both(*clauses)+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r5hw',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='provisional_order_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/legislative-touchstone-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
