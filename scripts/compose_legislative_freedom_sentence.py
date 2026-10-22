"""Integrate the generalized legislative insight and its present royal example."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_prince_sentence import ANCHOR,CANDIDATE,TOPIC
from scripts.compose_royal_example import SCHEMA

PARENT='examples/v016/kant-religious-emphasis-sentence.noema';PARENT_BASIS='data/religious-emphasis-sentence-basis-v1.json'
DEPENDENCY='data/royal-example-basis-v1.json'
FULL='examples/v016/kant-legislative-freedom-sentence.noema';CORE='examples/v016/legislative-freedom-sentence-core.noema'
BASIS='data/legislative-freedom-sentence-basis-v1.json';ANNOTATIONS='data/legislative-freedom-sentence-identifiers-v1.json'
C5='i f[e]';F4='i e[h[a a] e]';COMPARE='i e[h[a d d d d] c]'
AUTHOR='k wa[]';KING='k h26mu[]';REF='k h26uj[]';CTX='k h26uk[]';PUBLIC='k h26ul[]'
PRIMITIVES={
 'h26ub':('[a a '+C5+' d] c',['node','author','content','context'],'著者が同じ箇所・文脈で指定した閉じた段階5内容を主張する。内容帰属であり、内容の現実の真理、前件の成立、例の歴史的な実証をこの提示関係から導かない。'),
 'h26uc':('[a a '+C5+' '+C5+' '+C5+' d] c',['node','author','whole','previous','current','context'],'著者が同じ全体の現在内容を、先行内容に対する観点又は範囲の転換を伴う対照として提示する。先行内容の撤回、二内容の論理矛盾、どちらかだけの採用を含意しない。二つの具体的な内容は引用で保持する。'),
 'h26ud':('[a a '+C5+' '+F4+' '+F4+' d] c',['node','author','whole','condition','conclusion','context'],'著者が同じ全体の中で、人物・共同体の同じ二引数に対する条件と帰結を一般的な条件付き述定として提示する。量化と条件の真理内容は合成側で構成する。現実の一人だけへの限定、全人物の条件成立、条件から帰結への形式的必然を追加しない。'),
 'h26ue':('[a a '+C5+' '+F4+' a d] c',['node','author','whole','focus','clause','context'],'著者が同じ全体に埋め込まれた同じ人物・共同体の焦点内容について、指定箇所に示す領域にまで及ぶことを通常の期待を越える取り立てとして示す。全体内の認識・条件の作用範囲を保ち、焦点だけの無条件の真理や、その領域だけという排他性を追加しない。'),
 'h26uf':('[a a '+C5+' '+F4+' '+F4+' d] c',['node','author','whole','baseline','addition','context'],'著者が同じ全体に埋め込まれた同じ二引数の基本内容を保持し、追加内容にまで及ぶことを期待を越える強い追加として提示する。許可や認識に埋め込まれた対象を現実の実行に変えず、基本内容から追加内容を論理的に導かない。'),
 'h26ug':('[a a '+C5+' '+C5+' '+F4+' d] c',['node','author','whole','earlier_focus','extension','context'],'著者が先行内容で焦点とされた領域を基準に、同じ全体の人物・共同体に関する考察がさらに別の領域へ及ぶものとして提示する。領域への接続は帰結内で構成し、空間移動、考察の新規獲得という時間変化、先行焦点の撤回を意味しない。'),
 'h26uh':('[a a '+C5+' '+C5+' '+C5+' '+SCHEMA+' d] c',['node','author','whole','general','instance','pattern','context'],'著者が同じ全体の一般内容について、指定された実例内容をその具体化として提示する。同じ八役割の内容型が何を具体化するかを固定し、実例側で付加した現実の政策成立を一般内容の全対象へ移さない。一例から普遍命題を演繹したことや実例の真理をこの提示関係だけでは導かない。'),
 'h26ui':('[a a '+C5+' '+C5+' '+SCHEMA+' '+COMPARE+' d] c',['node','author','whole','instance','pattern','comparison','context'],'著者が同じ実例で具体化された内容型のあり方を、同じ全体内の比較が行われる観点として受ける。比較の人物・解釈基準・履歴・事例点・評価点は全体内の同じ証人へ結ぶ。例の単なる有名さや別人物の功績を比較の観点へ交換せず、比較結果そのものは合成側で構成する。'),
 'h26uj':('[] d',[],'第九段落第二文の国家元首・全臣民・立法・許可・安全性・判断・実例・君主比較に共用する固定解釈基準。第一文の基準、本文現在、履歴と提示文脈を区別し、好ましい結果に合わせて範囲を変更しない。'),
 'h26uk':('[] d',[],'固定原文kant-1784:u0016第二文を著者が提示する論述文脈。第一文の提示文脈と内容評価の基準、本文現在と区別する。'),
 'h26ul':('[] a',[],'第二文のwirが指す、著者と同時代の読者を含む文脈上の人間公衆。全世界の人々や全臣民と同一視しない。範囲を敬意の成立や試験結果から選ばず、著者所属と全成員の敬意は合成側で要求する。'),
}
NODE_INFO={
 'h26um':([390,905],'第二文全体。'), 'h26un':([390,394],'Aberの対照。'),
 'h26uo':([395,461],'啓蒙を後押しする国家元首の思考態度という一般条件の主体。'),
 'h26up':([463,479],'geht noch weiterの領域拡張。'), 'h26uq':([439,450],'die erstereの啓蒙への照応。'),
 'h26ur':([500,506],'selbstの立法領域にまで及ぶ取り立て。'),
 'h26us':([507,538],'同じ元首自身の立法への限定。'),
 'h26ut':([708,713],'sogarの批判付きの追加。'), 'h26uu':([651,706],'同じ立法の改善についての思想。'),
 'h26uv':([714,763],'既に与えた同じ法への率直な批判。'),
 'h26uw':([797,802],'davonの同じあり方の実例への接続。'), 'h26ux':([838,845],'wodurchの同じ実例による比較観点。'),
 'h26uy':([864,874],'demjenigenの同じ君主。'), 'h26uz':([884,904],'welchen wir verehrenの同じ君主への敬意。'),
 'h26u2':([485,494],'sieht einの同じ内容への認識。'), 'h26u3':([559,795],'三対象への許可。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0016['+str(s[0])+','+str(s[1])+')の'+m) for n,(s,m) in NODE_INFO.items()})
MEANINGS={
 'r6ee':'同じ本文現在と第二文の基準で、人物・共同体がr6dwの啓蒙を実務的に後押しする国家元首の条件を満たす内容。特定の現実の君主一人に量化範囲を狭めない。',
 'r6ef':'同じ人物・共同体について、同じ全臣民h26sp・基準・履歴・現在・宗教領域に、r6d2を満たす本人の思考態度があるという帰結。宗教で用いられる同じ態度と、同じ立法上の方針の安全性への事実的な認識を結ぶ。政策の現実の実施は要求しない。',
 'r6eg':'本文現在の全人物・共同体について、r6eeの同じ条件ならr6efの同じ帰結を述べる一般条件。前件不成立の場合に帰結を要求せず、例の現実性は別のr6ehで要求する。',
 'r6eh':'前に名指したh26muの君主について、同じ現在点・履歴・基準・宗教領域・公衆の下で、同じ共同体・思考態度・実例をr6edへ束縛する。全臣民は同じh26spで供給し、実例の許可成立、敬意、まだ上回られていない比較を同じ証人に保つ。',
 'r6ei':'一般条件r6egと同じ現在の具体例r6ehを共に保つ第二文全文の内容。一般条件だけの空虚な成立や、実例一つだけでは全文にならない。',
 'r6ej':'同じ二引数・全臣民・基準・現在の思想提示r6dgへの許可という埋込み焦点内容。全臣民の一致と学識者の役割を保ち、許可の対象を現実の発表へ変えない。',
 'r6ek':'同じ二引数と設定について率直な批判付き思想提示r6djへの許可という追加焦点内容。r6ejと対象・起点を共用し、基本的な思想の許可だけから追加を補わない。',
 'r6el':'同じ二引数・全臣民・基準・履歴・現在について、立法上の許可方針の危険不在r6dqを焦点内容として取り出す。sieht einの対象に埋め込まれたまま提示し、現実の方針実施へ変えない。',
 'r6em':'全文を著者へ帰属し、第一文との対照、二引数の一般条件、啓蒙への照応、宗教からの領域拡張、立法までと批判付きまでの取り立て、同じ実例と比較観点、前に名指した君主への照応と本文順序を結ぶ。引用された政策や歴史的評価を外側で実行しない。',
}
LIMITS=[
 '固定原文u0016第二文[390,905)・444非空白文字を対象とする。eines Staatsoberhauptsは本文現在の人物・共同体に対する一般条件とし、啓蒙への実務的な後押しを前件、同じ本人の思考態度による立法方針の安全性の認識を帰結とする。後半の具体例にだけ現実の同じ方針の成立を加える。',
 'die erstereは第一文のAufklärung、derは同じ国家元首を受ける。宗教上の未成熟を後押しする読みにはしない。Denkungsartの持ち主と洞察の保持判断は同じ本人に結び、宗教から立法への拡張を空間運動や新しい時点への変化にしない。',
 '許可の三対象、全臣民・全候補、本人の理解力、公的な学識者の使用、改善についての思想、既存法への率直な批判、世界読者への提示は依存群の同じ内容を保つ。所有代名詞とderselben/der schon gegebenenの参照は同じ人物・共同体・法・定式の束縛に保持する。',
 'ohne Gefahrは同じ許可方針に由来する公共的損失の危険不在、sieht einは同じ内容の把握・受容・十分な根拠を持つ保持判断と真理を要求する既存の読みを継承する。現実の全災害の不存在、単なる確信、別内容の根拠へ置き換えない。',
 '実例の君主は先行u0014で名指したフリードリヒ二世h26muと読む。国名や在位年を追加の著者主張にはせず、共同体はその同じ君主の設定として束縛する。wirは著者を含む指定公衆であり、全世界や全臣民の敬意を付け足さない。',
 'vorgingは同じ実践の点で現在まで他の君主に上回られていないという比較。Adelungの二用法を記録した前群の明示解釈を継承し、同等の先行例は許す。時間的な最初の達成や、将来の優越例の否定へ強めない。',
 'Aberは宗教を最大の論述重点にした前文から立法にまで及ぶ考察への対照、noch weiterはその領域拡張、selbstは自分の立法にまで及ぶ取り立て、sogarは批判付き提示への強い追加と読む。全体内の認識・許可の作用範囲を保ち、引用された焦点を外側の現実の実行へ昇格させない。',
 'davonは同じあり方の実例、wodurchは同じ実例で具体化したあり方についての比較、demjenigen/welchenは同じ君主を受ける。実例の存在と一般条件は別々に要求し、一例からの論理的な普遍証明を追加しない。',
 '全文判断は明示した読みを用いたアシスタントの原文通読判断であり、独立査読、自動同義証明、著者の歴史的主張の実証ではない。従来118主張を保持し、第十段落とEinsteinは未完のまま扱う。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def group(ruler='v ruler',community='v community'):return 'k h26sp['+ruler+' '+community+' '+REF+']'
def frame(ruler='v ruler',community='v community'):return ruler+' '+community+' '+group(ruler,community)+' '+REF+' '+CANDIDATE+' '+ANCHOR
def definitions():
    text='d r6ee[ruler a community a] e[b outer[k r6dw[v ruler v community '+REF+' '+ANCHOR+']]].\n'
    text+='d r6ef[ruler a community a] e[b outer[g manner a[t[k r6d2['+frame()+' v manner '+TOPIC+']]['+ANCHOR+']]]].\n'
    text+='d r6eg[] e[b outer[f ruler a[f community a[y[t[k r6ee[v ruler v community]][v outer]][t[k r6ef[v ruler v community]][v outer]]]]]].\n'
    text+='d r6eh[] e[b outer[g community a[g manner a[g example a[k r6ed[v example '+AUTHOR+' '+PUBLIC+' '+frame(KING)+' v manner '+TOPIC+' '+ANCHOR+']]]]]].\n'
    text+='d r6ei[] e[b outer['+both('t[k r6eg[]][v outer]','t[k r6eh[]][v outer]')+']].\n'
    for n,target in (('r6ej','r6dg'),('r6ek','r6dj')):
        local='v ruler v community v person k h247d[v person '+REF+'] '+REF+' '+ANCHOR+(' '+CANDIDATE if target=='r6dj' else '')+' '+ANCHOR
        text+='d '+n+'[ruler a community a] e[b outer['+both('k r6bo[v ruler v community '+group()+' '+REF+']',
          'f person a[y[k h246c['+group()+' v person '+REF+']]['+both('k cd[k h247d[v person '+REF+'] '+REF+']', 'k '+target+'['+local+']')+']]')+']].\n'
    text+='d r6el[ruler a community a] e[b outer[t[k r6dq['+frame()+']]['+ANCHOR+']]].\n'
    return text
def discourse():
    node=lambda n:'k '+n+'[]';code=lambda n:'r f[k '+n+'[]]';fn=lambda n:'r e[p '+n+']';whole=code('r6ei')
    parts=[
      'k h26ub['+node('h26um')+' '+AUTHOR+' '+whole+' '+CTX+']',
      'k h26uc['+node('h26un')+' '+AUTHOR+' '+whole+' '+code('r6ch')+' '+whole+' '+CTX+']',
      'k h26ud['+node('h26uo')+' '+AUTHOR+' '+whole+' '+fn('r6ee')+' '+fn('r6ef')+' '+CTX+']',
      'k r6d3['+node('h26uq')+' '+AUTHOR+' '+node('h26sw')+' '+CTX+']',
      'k h26ug['+node('h26up')+' '+AUTHOR+' '+whole+' '+code('r6cc')+' '+fn('r6ef')+' '+CTX+']',
      'k h26ue['+node('h26ur')+' '+AUTHOR+' '+whole+' '+fn('r6el')+' '+node('h26us')+' '+CTX+']',
      'k h26uf['+node('h26ut')+' '+AUTHOR+' '+whole+' '+fn('r6ej')+' '+fn('r6ek')+' '+CTX+']',
      'k h26uh['+node('h26uw')+' '+AUTHOR+' '+whole+' '+code('r6eg')+' '+code('r6eh')+' r e[p r6d4] '+CTX+']',
      'k h26ui['+node('h26ux')+' '+AUTHOR+' '+whole+' '+code('r6eh')+' r e[p r6d4] r e[p r6ea] '+CTX+']',
      'k h26m3['+node('h26uy')+' '+AUTHOR+' '+node('h26nb')+' '+KING+' '+CTX+']',
      'k h26m3['+node('h26uz')+' '+AUTHOR+' '+node('h26uy')+' '+KING+' '+CTX+']']
    pairs=(('h26sv','h26um'),('h26sw','h26uq'),('h26uo','h26up'),('h26up','h26u2'),('h26uu','h26uv'),('h26u3','h26uw'),('h26uw','h26ux'),('h26uy','h26uz'))
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in pairs]
    nodes=(*NODE_INFO,'h26sv','h26sw','h26nb');parts+=['u[e['+node(a)+']['+node(b)+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    middle=len(parts)//2
    return 'd r6em[] c['+both(both(*parts[:middle]),both(*parts[middle:]))+'].\n'
def build():
    old=parent();lib=dependency();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for d in closure(lib.document,('r6ed','r6d2','r6dw','r6dg','r6dj','r6dq')):
        n=d['name'];e=lib.entries[n]
        if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=e
    # The process-anaphora helper is not needed by the royal example itself.
    from scripts.compose_enlightened_thinking import BASIS as THINKING
    thinking=load_catalog(ROOT,THINKING)
    for d in closure(thinking.document,('r6d3',)):
        n=d['name'];e=thinking.entries[n]
        if n in old.entries or n in imported:
            prior=old.entries.get(n,imported.get(n));assert d==prior['declaration'] and e['meaning_ja']==prior['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6em',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r6em']),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(lib.source_sha256)|set(thinking.source_sha256)
    basis=dict(status='legislative_freedom_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
      new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/religious-emphasis-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
