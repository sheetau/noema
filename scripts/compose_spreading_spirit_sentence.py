"""Integrate the shared spirit, domestic/foreign spread and even-obstacle focus."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_clerical_duty_scope import quantify
from scripts.compose_prince_sentence import ANCHOR
from scripts.compose_attitude_obstacle_struggle import WITNESSES,MAPS,MODELS

PARENT='examples/v016/kant-public-offers-sentence.noema';PARENT_BASIS='data/public-offers-sentence-basis-v1.json'
DEPENDENCIES=('data/attitude-obstacle-struggle-basis-v1.json',)
FULL='examples/v016/kant-spreading-spirit-sentence.noema';CORE='examples/v016/spreading-spirit-sentence-core.noema'
BASIS='data/spreading-spirit-sentence-basis-v1.json';ANNOTATIONS='data/spreading-spirit-sentence-identifiers-v1.json'
REF='k h26pp[]';CTX='k h26pq[]';AUTHOR='k wa[]';C3='i d[e]';C2='i c[e]';ATTITUDE='i c[h[a] e]'
RULERS=('ruler','rulingoffice','community');PATH_PEOPLE=(*RULERS,'origin','target')
FOREIGN=(*RULERS,'government','foreignoffice','foreigncommunity','origin','target')
DESTINATIONS=('government','foreignoffice','foreigncommunity','target')
PATH_SELECTORS=dict(zip((n for n,t in WITNESSES),('h26pr','h26ps','h26pt','h26pu','h26pv','h26pw','h26px','h26py','h26pz','h26p2','h26p3')))
MODEL_SELECTORS=dict(zip((n for n,t in MODELS),('h26p4','h26p5','h26p6','h26p7','h26qa','h26qb')))
PRIMITIVES={
 'h26pp':('[] d',[],'固定原文kant-1784:u0015第三文の共通自由方針、態度、社会的経路、政府の自己理解、障害モデルと実践的可能経過を解釈する固定基準。先行の宗教的自己選択と公的提示の自由を政府一般へ保った型とし、各段落の異なる基準を同じ状況個体へ黙って同定しない。'),
 'h26pq':('[] d',[],'固定原文kant-1784:u0015第三文を同じ著者が提示する論述文脈。内容基準とは別であり、本文の現在点は先行二文と同じh26kn(h26km)を保つ。'),
 'h26qc':('[j[a] d] j[a]',['bindings','reference'],'固定した八対象列（元の君主・最高職・共同体、外国政府・最高職・共同体、出発者・取得者）について、この読解の当該外国政府に由来する外的障害として扱う条件の有限列。真偽の略記ではなく条件を指す。各条件の出所・適用・外的性格・妨害、異なる複数条件の存在はr57fで別に確認する。'),
 'h26qd':('[j[a] d] h[d] c',['bindings','reference'],'同じ八対象列・基準について、同じ外国政府の同じ障害背景を固定した全関連実践的経過を選ぶ性質。目標達成や対抗的努力の有無で範囲を選ばず、可能経過の完全性は解釈入力の条件とする。障害の全適用はr57hで、達成可能性と必要性はr57bで別に検査する。'),
 'h26qe':('[a a '+C3+' '+C2+' d d] c',['node','author','antecedent','policy','reference','context'],
   '著者が同じ箇所で、指定された先行内容に示した自由のあり方を、指定の共通方針の型として受け継ぐ。先行例の人名・称賛・自己報告の全条件を方針へ複写せず、宗教的自己選択・公的提示という同じ内容面を保持する。先行内容と一般方針の論理的同値、先行命題からの演繹、方針の現実の実現を意味しない。特定文専用の真理判定ではなく、具体例から内容の型を受け継ぐ談話関係。'),
 'h26qf':('[a a '+ATTITUDE+' a d] c',['mention','author','referent','scope','context'],
   '著者が同じ談話範囲・文脈の指定表現で、閉じた段階2の人物性質を同じ指示内容として参照する。語形の一致、別人の別の性質、性質自体を個体の人や政府にすることとは区別する。指示された性質の実際の成立や取得をこの関係だけから導かない。'),
 'h26qg':('[a a '+C3+' '+C3+' '+C3+' d d] c',['node','author','whole','baseline','addition','reference','context'],
   '著者が同じ全体・基準で、基準側の内容を背景として維持し、それに加えて同じ観点で別の範囲にも成立する内容を提示する。二つの閉じた内容が同じ態度・源の条件を扱うことは合成側で保つ。基準内容の撤回、追加側だけの限定、全範囲への無差別な一般化、時間的後発は追加しない。引用の真理は実行しない。'),
 'h26qh':('[a a '+C3+' '+C3+' '+C3+' d d] c',['node','author','whole','general','focus','reference','context'],
   '著者が同じ全体と基準で一般の内容を保ちながら、同じ内容がより不利な条件を伴う適用例にも成立することを、比較上期待しにくい場合まで及ぶものとして取り立てる。焦点の条件と一般内容の共有はそれぞれの記述で構成する。全代替例の成立、実際の読者の驚き、数値的確率、全背景での不可能性、一般内容の撤回を要求しない。'),
}
for n,t in WITNESSES:
    PRIMITIVES[PATH_SELECTORS[n]]=('[j[a] d] h[d] '+t,['bindings','reference'],
        '固定した五対象列（元の君主・最高職・共同体・出発者・取得者）と同じ態度基準について、各候補経過の社会的経路の'+n+'を供給する対応。取得がある候補ではそれを示す証人を与え、見つけ損ねを取得不能へ変換しない。最初の段階・任意有限の後続列・履歴・順序・各段階の七対応は同じ候補と対象列を共有し、実際の経路成立はr56v/r57aで検査する。')
for n,t in MODELS:
    PRIMITIVES[MODEL_SELECTORS[n]]=('[j[a] d] h[a] '+t,['bindings','reference'],
        '固定した八対象列（元の君主・最高職・共同体、外国政府・最高職・共同体、出発者・取得者）と基準について、各障害条件の介入比較モデルの'+n+'を供給する。モデルは条件以外の背景と分岐を対応させ、目標や結果から組を選ばない。全解・評価・対応の有効性と条件の有無の一致はr566で検査し、同じ取得・保持目標を全条件へ渡す。')
NODE_INFO={
 'h26qi':([890,1049],'第三文全体。'),
 'h26qj':([890,915],'Dieser Geist der Freiheitの先行自由例を受ける指示。'),
 'h26qk':([890,948],'国外への広がりを述べる主節。'),
 'h26ql':([929,933],'auchの追加。'),
 'h26qm':([949,958],'selbst daの不利な場合の取り立て。'),
 'h26qn':([963,965],'erの同じ精神への照応。'),
 'h26qo':([949,1049],'自己誤解する政府の外的障害への格闘を要する場合を含む焦点節。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0015['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r57j':'同じ元の君主の統治圏の異なる二人について、候補ごとの証人で同じ自由への態度の社会的取得と現在までの保持r56vを結ぶ。国内というauchの背景を、単に元の一人が態度を持つことへ縮めない。',
 'r57k':'本文の同じ八対象・固定基準の下で、候補ごとの経路設定をr57aへ渡し、同じ現在点の国外到達・保持を返す。国外政府へ君主制や自由政策の実現を課さない。',
 'r57l':'r57kと同じ八対象・経路設定・現在点で、全障害条件・各介入モデル・関連経過をr57iへ渡す。国外到達、同じ政府の自己誤解、外的障害、対抗的努力とその必要性を同じ取得者へ結ぶ。',
 'r57m':'同じ元の君主・職・共同体について出発者を一人存在量化し、その同じ人から国内の別人への広がりと、障害下にある国外への広がりを結ぶ。二つの無関係な出発者の経路を寄せ集めない。',
 'r57n':'同じ元の君主・職・共同体において、r57jの国内への社会的取得・保持の証人が存在する。auchで維持する基準側の内容。',
 'r57o':'同じ元の君主・職・共同体において、r57kの国外取得・保持の証人が存在する。全世界への到達や全ての外国政府についての主張ではない。',
 'r57p':'同じ元の君主・職・共同体において、r57lの自己誤解する政府の複数障害下で努力と必要性を伴う国外取得の証人が存在する。selbst daの焦点側で、一般の国外側の内容を維持する。',
 'r57q':'先行二文と同じ君主・最高職・共同体の全組について、同じ現在点でr53bの限定を満たすならr57mの内外への広がりがあるという内容。存在しない又は非該当の君主へ実際の出来事を補わず、該当下では内外の経路証人を要求する。',
 'r57r':'本文第三文の固定基準へr57qを結ぶ全文内容。外側の評価点を変えて本文の現在点を動かさない。',
 'r57s':'同じ限定君主の全称・条件を保ち、r57nの国内側を閉じた内容にする。auchの背景内容であり、本文全体と同じ態度・現在・基準を使う。',
 'r57t':'同じ限定君主の全称・条件を保ち、r57oの国外側を閉じた内容にする。主節の帰属と追加側の焦点で使う。',
 'r57u':'同じ限定君主の全称・条件を保ち、r57pの障害下の国外側を閉じた内容にする。selbst daの不利な場合を含む焦点で使う。',
 'r57v':'本文の固定基準のr56nを人物性質として返す。Dieser Geistとerに同一の閉じた参照を与え、実際の経路と格闘でも同じr56oの内容を使う。',
 'r57w':'同じ固定基準のr56jの共通自由方針を返す。先行例から受け継ぐ宗教的自己選択・公的提示の型と、r57vの支持対象を一致させる。',
 'r57x':'全文・主節・焦点節を著者へ帰属し、先行二文から同じ自由方針への内容の継承、二箇所の同じ精神への照応、auchの追加、selbst daの不利な場合の取り立て、本文順序と各箇所の区別を結ぶ。引用から世界内容の真理を実行しない。',
}
LIMITS=[
 '固定原文u0015第三文[890,1049)の136非空白文字を対象とする。先行二文の一般的君主条件r53bを継続し、該当する同じ君主・最高職・共同体の下で同じ態度が内外へ広がると読む。実在の王・国名を新たに固定せず、全外国政府や全住民への到達には強めない。',
 'この精神は先行の宗教的自己選択と公的提示の自由の型を政府一般について支持する共有可能な態度。君主の功績・自己報告・名称評価まで支持内容へ混ぜず、個人の君主と政府組織も同一視しない。先行二文から型を受け継ぐ談話関係を明示し、両者の命題的同値や演繹的導出とはしない。',
 'auchは元の統治圏内部への広がりも背景として保ち、外部への広がりを追加する読み。両側の経路は同じ出発者と同じ態度を共有する。外部は異なる共同体の政府の管轄下かつ元の管轄外という制度的範囲で、旅行座標・国籍・全世界を同義にはしない。',
 'breitet sich ausは、態度の表れとなる人の活動を通じて、異なる人が同じ態度を取得し、現在まで保持する社会的経路。任意長の有限経路を許し、発話伝達だけに狭めず、過去に一度も持たなかったという生涯初回条件も加えない。',
 'selbst da, woは、その国外への広がりが、自己誤解する政府の外的障害に対抗する努力を要する場合にもあるという焦点。条件付きの例としてだけ空虚に扱わず、同じ君主条件の下でこの場合の証人を要求する。全外国政府が自己誤解する、無障害の外国例が別に実在する、実際の読者が驚くとは補わない。',
 '自己誤解は政府が制度上採用する自分たちの公的役割の理解と同じ内容の真偽との不一致。障害の由来は同じ政府へ結ぶが、誤解が障害を生んだ因果や悪意を加えない。複数の異なる条件を保ち、同じ条件の重複列だけを複数と数えない。',
 '格闘は同じ態度を担う人の活動・態度の表れ・力の投入・当該条件への対抗の方向性。受け手本人だけに努力を負わせず、政府打倒や克服完了を要求しない。必要性は同じ障害背景の全関連経過で到達・保持に努力を要し、達成可能な経過があるという読みで、規範的義務や努力の十分性とはしない。',
 '経路設定は候補内の取得があればそれを示す証人を供給する。介入モデルは条件以外の背景と分岐を対応させ、必要性の関連経過は同じ障害下の全実践的経過である。証人不足・結果による事後選別を妨害や必要性へ変換しない。これらの完全性・現実適合は明示した解釈入力で、有限検査による現実の因果実証や全経路探索ではない。',
 '本文現在は先行二文と同じh26kn(h26km)。態度・モデルの固定解釈基準と著者の提示文脈は分ける。未評価や未知を否定・無害へ補わず、引用帰属から実際の自由政策・発表・審査・外国政府の賛同を導かない。',
 '全文判断は明示した解釈の下で原文全語句と作用域を再読したアシスタント判断であり、有限検査による自動同義証明や独立査読ではない。第四文・第五文、第九・第十段落、アインシュタインは未完で、第四文ist/sei版差を保持する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def args(ns):return ' '.join('v '+n for n in ns)
def fields(ns):return ' '.join(n+' a' for n in ns)
def quant(ns,body,kind='f'):return quantify([(n,'a') for n in ns],body,kind)
def key(ns):return 'l[a]['+args(ns)+']'
def witness(n):return 'k '+PATH_SELECTORS[n]+'['+key(PATH_PEOPLE)+' v reference]'
def selected(n):return 'k '+MODEL_SELECTORS[n]+'['+key(FOREIGN)+' v reference]'
def qualified():return 't[c[k r53b[]]['+args(RULERS)+']]['+ANCHOR+']'
def definitions():
    at=lambda n:'c['+witness(n)+']['+ANCHOR+']'
    local=both('u[e[v origin][v target]]',*('k r54w['+args(RULERS)+' v '+n+' '+ANCHOR+']' for n in ('origin','target')),
        'k r56v['+at('first')+' '+at('rest')+' v origin v target v reference '+at('history')+' '+at('before')+' '+' '.join(at(n) for n,t in MAPS)+' '+ANCHOR+']')
    text='d r57j['+fields(PATH_PEOPLE)+' reference d] c['+local+'].\n'
    goalargs=args(FOREIGN)+' v reference '+' '.join(witness(n) for n,t in WITNESSES)
    text+='d r57k['+fields(FOREIGN)+' reference d] c[t[k r57a['+goalargs+']]['+ANCHOR+']].\n'
    text+='d r57l['+fields(FOREIGN)+' reference d] c[k r57i['+goalargs+' k h26qc['+key(FOREIGN)+' v reference] '+ANCHOR+' '+' '.join(selected(n) for n,t in MODELS)+' k h26qd['+key(FOREIGN)+' v reference]]].\n'
    domestic=quant(('target',),'k r57j['+args(PATH_PEOPLE)+' v reference]','g')
    abroad=lambda name:quant(DESTINATIONS,'k '+name+'['+args(FOREIGN)+' v reference]','g')
    text+='d r57m['+fields(RULERS)+' reference d] c['+quant(('origin',),both(domestic,abroad('r57l')),'g')+'].\n'
    for name,body in (('r57n',domestic),('r57o',abroad('r57k')),('r57p',abroad('r57l'))):
        text+='d '+name+'['+fields(RULERS)+' reference d] c['+quant(('origin',),body,'g')+'].\n'
    body=quant(RULERS,'y['+qualified()+'][k r57m['+args(RULERS)+' v reference]]')
    text+='d r57q[reference d] e[b outer['+body+']].\n'
    text+='d r57r[] e[k r57q['+REF+']].\n'
    for name,target in (('r57s','r57n'),('r57t','r57o'),('r57u','r57p')):
        body=quant(RULERS,'y['+qualified()+'][k '+target+'['+args(RULERS)+' '+REF+']]')
        text+='d '+name+'[] e[b outer['+body+']].\n'
    text+='d r57v[] h[a] e[k r56n['+REF+']].\n'
    text+='d r57w[] e[k r56j['+REF+']].\n'
    return text
def discourse():
    node=lambda n:'k '+n+'[]';code=lambda n:'r d[k '+n+'[]]';policy='r c[k r57w[]]';state='r c[k r57v[]]'
    parts=['k h236i['+node(n)+' '+AUTHOR+' '+code(t)+' '+CTX+']' for n,t in (('h26qi','r57r'),('h26qk','r57t'),('h26qo','r57u'))]
    parts+=['k h26qe['+node('h26qj')+' '+AUTHOR+' '+code(t)+' '+policy+' '+REF+' '+CTX+']' for t in ('r53k','r55s')]
    parts+=['k h26qf['+node(n)+' '+AUTHOR+' '+state+' '+node('h26qi')+' '+CTX+']' for n in ('h26qj','h26qn')]
    parts+=['k '+p+'['+node(n)+' '+AUTHOR+' '+code('r57r')+' '+code(a)+' '+code(b)+' '+REF+' '+CTX+']' for p,n,a,b in (
        ('h26qg','h26ql','r57s','r57t'),('h26qh','h26qm','r57t','r57u'))]
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in (('h26pc','h26qi'),('h26qj','h26qn'),('h26qk','h26qo'))]
    nodes=(*NODE_INFO,'h26pc')
    parts+=['u[e['+node(a)+']['+node(b)+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    return 'd r57x[] c['+both(*parts)+'].\n'
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in closure(lib.document,['r57i','r57a','r56v','r54w','r56n','r56j']):
            n=d['name'];e=lib.entries[n]
            if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
            elif n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r57x',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r57x']),statements=[new])
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='spreading_spirit_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/public-offers-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
