"""Integrate civil oversight, personal religious discretion and preventive remit."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='examples/v016/kant-monarchical-sentence.noema'
PARENT_BASIS='data/monarchical-sentence-basis-v1.json'
DEPENDENCIES=('data/civic-oversight-basis-v1.json','data/personal-religious-remit-basis-v1.json','data/salvation-work-protection-basis-v1.json')
FULL='examples/v016/kant-monarchical-religion-sentence.noema'
CORE='examples/v016/monarchical-religion-sentence-core.noema'
BASIS='data/monarchical-religion-sentence-basis-v1.json'
ANNOTATIONS='data/monarchical-religion-sentence-identifiers-v1.json'
FAMILY='i c[h[j[a] d] e]'
REF='k h26hz[]';CTX='k h255n[]';SOURCE='k wa[]'
NAMES=('actor','community','order')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
TWO='l[a][v actor v community]'
THREE='l[a]['+ARGS+']'
PRIMITIVES={
 'h26hy':('[a a a d d] c',list(NAMES)+['reference','case'],
   '同じ君主候補・政治的共同体・市民的秩序と固定論述基準について、ここで検討する相互に矛盾しない仮定場面の全範囲。監督の成功、許容、宗教的な所管外、妨害防止の履行や義務を先に選別条件にしない。役職と非空の秩序枠は別に構成し、内側の対象分類・能力・内容の固定基準には同じ場面そのものを渡す。'),
 'h26hz':('[] d',[],
   '第六段落第十一文の君主の宗教的関与と公的職責を扱う一般的な論述基準。直前と同じ君主的役職r2ujと政治的共同体を扱い、特定国・実在者・現行制度だけへ固定しない。各仮定場面の役職・臣民・宗教内容・能力基準や、文章の提示文脈とは区別する。'),
 'h26h2':('[a a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['focus_node','condition_node','author','whole','scope','condition','consequence','reference','context'],
   '著者が同じ全体・範囲の下で、指定した前件さえ充足すれば指定した帰結が成り立つという十分条件への焦点を提示する。前件の箇所を保持し、同じ対象列と固定基準を三内容族へ渡す。前件が現実に真であること、必要十分条件、主体が他の事柄へ一切注意してはならないという全面排除を追加しない。'),
 'h26h3':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','reserved','remaining','reference','context'],
   '著者が同じ全体・範囲の下で、第一の関与事項を留保した上で、それ以外の指定事項に第二の扱いを向けるという残余範囲を提示する。同じ対象列・基準を保ち、公的秩序への監督と本人の宗教的自己選択を混同しない。第一の撤回、第二への無限定な全行為の自由、引用内容の現実の実行は加えない。'),
 'h26h4':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','permission','minimal_response','reference','context'],
   '著者が同じ全体・範囲の下で、指定の許容対象を、それ以上の指定領域への介入を加えずに済む応答として取り立てる。ここでそれ以上を加えない内容は閉じた応答内容族に明示し、同じ対象列・基準へ結ぶ。単に未知の介入を無視する意味でも、全領域の全代替方針への禁止や無条件の履行義務でもない。'),
 'h26ig':('[a a i d[e] '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','focus','reference','context'],
   '著者が同じ全体・対象範囲・固定基準の下で、指定の補足内容を特に注意すべき点として取り立てる。段階2の閉じた範囲と焦点の内容族へ同じ対象列と基準を渡す。h26baと同種の取り立てを引用を含む内容族へ適用し、焦点の現実の真理・唯一性・数値的な最大順位を加えず、範囲を焦点の成功例だけへ縮めない。'),
}
NODE_INFO={
 'h26h5':([3226,3644],'第十一文全体。監督を条件とした本人への委任と、宗教的な所管外・妨害防止の職責。'),
 'h26h6':([3226,3464],'Wennからfinden;までの条件付きの委任の許容。'),
 'h26h7':([3226,3341],'Wennからbestehe;までの前件。真又は見かけの改善と市民的秩序の両立への監督。'),
 'h26ia':([3465,3488],'das geht ihn nichts anの、同じ君主の宗教的な所管外。'),
 'h26ib':([3489,3644],'wohl aber以降の、他者の全力の営みへの暴力的妨害を防ぐ職責。'),
 'h26ic':([3234,3237],'最初のnur。監督という前件さえ充足すればよいという条件への焦点。'),
 'h26id':([3371,3379],'übrigens。公的秩序の留保を除いた宗教的自己選択の残余範囲。'),
 'h26ie':([3380,3383],'二つ目のnur。さらに宗教的指図・介入を加えず本人に委ねればよいという応答への焦点。'),
 'h26if':([3489,3498],'wohl aber。同じ君主の所管外に対する、妨害防止の積極的職責の肯定・対照。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0013['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
NODES=('h26gw',*NODE_INFO)
MEANINGS={
 'r5ok':'同じ一般論述基準の全仮定場面h26hyのうち、同じ人が同じ共同体の君主r2ujであり、同じ非空の市民的秩序の全条件枠r5m5がある。監督・許可・所管外・予防の義務や成功を範囲へ先取りしない。',
 'r5ol':'同じ仮定場面の同じ君主が保持する同じ最高統治職に対し、著者waの評価を出所として、同じ全臣民への非指図・非介入r5nzへの衝突のない積極的許容r37cがある。内側基準と評価点を同じ場面に固定し、許容から実際の不干渉を導かない。',
 'r5om':'同じ君主・共同体・秩序の同じ仮定場面で実効的監督r5nhがあるなら、同じ場面でr5olの本人への委任の許容がある。前件の監督を現実の事実として別に断言せず、全提案が実施可能であることを要求しない。',
 'r5on':'同じ仮定場面を内側の固定基準と評価点にし、同じ君主・共同体の全臣民の救済判断についてr5n2の公的な所管外を返す。',
 'r5oo':'同じ仮定場面の同じ君主・共同体へ、著者waの評価を出所としてr5ojの実効的予防の公的所管と正極性要求を結ぶ。義務を実際の予防履行へ替えない。',
 'r5op':'同じ一つの君主・共同体・秩序・仮定場面に、監督から委任許容への条件r5om、宗教的所管外r5on、予防の職責r5ooを結ぶ。後二者を監督成功の条件内へ隠さない。',
 'r5oq':'固定論述基準h26hzで全君主・共同体・秩序・仮定場面のr5ok範囲にr5opを要求する、第十一文全体の一般内容。各場面の内部で同じ参照先を共有する。',
 'r5or':'同じ全範囲にr5omの条件付き委任許容を要求する前半の内容。監督だけ又は許容だけを無条件に帰属しない。',
 'r5os':'同じ全範囲にr5onの宗教的所管外を要求する節の内容。前半の監督前件が偽でもこの所管外は独立に保持する。',
 'r5ot':'同じ全範囲にr5ooの積極的な妨害防止の職責を要求する後半の内容。前半の監督前件が偽でもこの職責は独立に保持する。',
 'r5ou':'君主・共同体・秩序の正確な三対象列と一般論述基準・仮定場面をr5okの全範囲へ渡す。三つの焦点と職責の対照で共通に使う。',
 'r5ov':'同じ三対象列と仮定場面で、同じ君主による同じ市民的秩序への実効的監督r5nhを返す。内側の固定基準も同じ場面に置く。',
 'r5ow':'同じ三対象列の君主・共同体と仮定場面をr5olの委任許容へ渡す。秩序は範囲で保持し、別の共同体の許可を借りない。',
 'r5ox':'同じ三対象列の君主・共同体と仮定場面をr5onの宗教的所管外へ渡す。',
 'r5oy':'同じ三対象列の君主・共同体と仮定場面をr5ooの妨害防止の職責へ渡す。',
 'r5o2':'同じ三対象列から同じ君主・共同体へのr5nzの非指図・非介入内容を返す。nurで焦点化する応答自体であり、その許容r5owや実際の履行とは別に保持する。',
 'r5o3':'同じ人がいずれかの政治的共同体の君主的役職を持つという共通観点。宗教的所管外と公的な予防の職責を、同じ君主の関与範囲の二側として対照する。',
 'r5o4':'第十一文全体・条件節・所管外・予防職責を同じ著者と段落へ帰属し、前文からの順序、最初のnurの十分条件焦点、übrigensの残余範囲、二つ目のnurの最小限の応答、wohl aberの肯定的な職責対照を結ぶ。引用された政策・許可・監督・予防を現実の事実として実行しない。',
}
LIMITS=[
 'u0013第十一文[3226,3644)354非空白文字全体を対象とする。君主は直前と同じr2ujの制度上の役職、臣民はその同じ君主の同じ共同体への制度的服属。真又は見かけの改善、救済の本人判断、営みと妨害・予防は保存した依存群の明示読解を保持する。',
 '一般論述の基準h26hzと個々の仮定場面を分ける。全仮定場面の内部では、その同じ場面を対象分類・能力・内容の固定基準と規範評価点へ共通に渡す。許容内容や予防内容の引用内で評価点が動いても、既に固定した対象範囲を成功や後の信念で選び直さない。',
 'Wenn er nur darauf siehtは、実施される真又は信じられた改善が同じ市民的秩序を保つよう実効的に監督するなら、という十分条件と読む。最初のnurはこの条件さえ充足すればよいという焦点で、君主が他の公的事項を一切監督してはならないという排他性や逆向きの必要条件にはしない。',
 'kannは著者の提示する統治の評価における規範的許容と読み、本人への委任r5nzに最高統治職で衝突のない積極的許可r37cを結ぶ。身体的能力、現実の委任、全臣民が現に営みを実行したことや救済の真理を追加しない。',
 'übrigensは市民的秩序を守る監督を留保した残余の宗教的自己選択の範囲。二つ目のnurは、さらに宗教上の指図・代行・強制的介入を加えず本人に任せればよい、という最小限の応答の焦点と読む。全ての統治政策のうち一つだけが許容されるという排他的量化や、無条件の履行義務は追加しない。非指図・非介入そのものはr5nzの内容に明示する。',
 'セミコロン後のdas geht ihn nichts anとwohl aber以下は独立した一般的な職責の説明として読む。宗教的必要性を本人に代わって公的に決定する所管はなく、他者の権限なき強制による妨害を防ぐ公的所管と要求はある。監督に成功した君主だけにこの二側を限定しない。',
 'wohl aberは所管外と積極的所管・職責の対照で、後者を肯定的に取り立てる。語用上の対照を両命題の論理的矛盾、前半の撤回、数値的確信度や予防が現に成功していることへ替えない。',
 'er/ihnは同じ君主、seine/sieは同じ共同体の臣民、einer/andernはその範囲の異なる二人、desselbenは被害側本人の同じ救済、所有表現はその本人の能力を受ける。固定転記はseinen、AA本文はseinemだが、転記を改変せず同じ被害側の能力に係る表現として読む。',
 '後半の保護候補は既に必要だと信じた営みだけへ狭めず、決定と促進の二目標への全候補を使う。全力は本人の固定能力基準での最大の投入という読解。妨害は身体的力だけでなく権限なき優越的強制を含み、正当な公的規律を自動的に防止対象にはしない。',
 '前文との話題継続と同じ段落への著者帰属を保持し、全文・条件付き前半・所管外・予防職責を別々の内容として帰属する。監督の前件だけを無条件の主張へ変換しない。',
 '全語句との対応と通読は明示解釈下のアシスタントの判断であり、有限検査による自動同値証明や唯一の歴史解釈ではない。第六段落の残部と二作品全体は未完。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    case='v case';inner=case
    frame=both('k h26hy['+ARGS+' v reference '+case+']','k r2uj[v actor v community '+case+']','k r5m5[v order v community '+inner+']')
    text='d r5ok['+FIELDS+' reference d case d] c['+frame+'].\n'
    permit='k r37c['+SOURCE+' v actor v office r b[p r5nz] '+TWO+' '+inner+' '+case+']'
    office=both('k h234f[v office v community '+case+']','k r2ui[v actor v office v community '+case+']',permit)
    text+='d r5ol[actor a community a case d] c[g office a['+office+']].\n'
    oversight='t[k r5nh['+THREE+' '+inner+']]['+case+']'
    text+='d r5om['+FIELDS+' reference d case d] c[y['+oversight+'][k r5ol[v actor v community '+case+']]].\n'
    text+='d r5on[actor a community a case d] c[t[k r5n2['+TWO+' '+inner+']]['+case+']].\n'
    text+='d r5oo[actor a community a case d] c[k r5oj['+SOURCE+' v actor v community '+inner+' '+case+']].\n'
    text+='d r5op['+FIELDS+' reference d case d] c['+both('k r5om['+ARGS+' v reference '+case+']','k r5on[v actor v community '+case+']','k r5oo[v actor v community '+case+']')+'].\n'
    for name,target,arguments in (('r5oq','r5op',ARGS+' '+REF+' '+case),('r5or','r5om',ARGS+' '+REF+' '+case),
        ('r5os','r5on','v actor v community '+case),('r5ot','r5oo','v actor v community '+case)):
        body='f case d[y[k r5ok['+ARGS+' '+REF+' '+case+']][k '+target+'['+arguments+']]]'
        for n in reversed(NAMES):body='f '+n+' a['+body+']'
        text+='d '+name+'[] e[b point['+body+']].\n'
    adapters={'r5ou':'k r5ok['+ARGS+' v reference v point]',
        'r5ov':'t[k r5nh['+THREE+' v point]][v point]',
        'r5ow':'k r5ol[v actor v community v point]','r5ox':'k r5on[v actor v community v point]',
        'r5oy':'k r5oo[v actor v community v point]','r5o2':'t[k r5nz['+TWO+' v point]][v point]'}
    for n,body in adapters.items():text+='d '+n+'[bindings j[a] reference d] e[b point['+bind(NAMES,body)+']].\n'
    text+='d r5o3[person a] e[b point[g community a[k r2uj[v person v community v point]]]].\n'
    author=SOURCE;whole='r d[k r5oq[]]';q=lambda n:'r c[p '+n+']'
    claims=['k h236i[k '+node+'[] '+author+' r d[k '+target+'[]] '+CTX+']' for node,target in (
        ('h26h5','r5oq'),('h26h6','r5or'),('h26ia','r5os'),('h26ib','r5ot'))]
    claims += ['k h26h2[k h26ic[] k h26h7[] '+author+' '+whole+' '+q('r5ou')+' '+q('r5ov')+' '+q('r5ow')+' '+REF+' '+CTX+']',
        'k h26h3[k h26id[] '+author+' '+whole+' '+q('r5ou')+' '+q('r5ov')+' '+q('r5o2')+' '+REF+' '+CTX+']',
        'k h26h4[k h26ie[] '+author+' '+whole+' '+q('r5ou')+' '+q('r5ow')+' '+q('r5o2')+' '+REF+' '+CTX+']',
        'k h236k[k h26if[] '+author+' k h26ia[] r d[k r5os[]] k h26ib[] r d[k r5ot[]] r[p r5o3] '+CTX+']',
        'k h26ig[k h26if[] '+author+' '+whole+' '+q('r5ou')+' '+q('r5oy')+' '+REF+' '+CTX+']']
    edges=(('h26gw','h26h5'),('h26h7','h26ia'),('h26ia','h26ib'),('h26ic','h26id'),('h26id','h26ie'),('h26ie','h26if'))
    claims+=['k ue[k '+a+'[] k '+b+'[] '+CTX+']' for a,b in edges]
    distinct=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(NODES) for b in NODES[i+1:]]
    claims += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5o4[] c['+both(*claims)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not(set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5o4',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='monarchical_religion_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/monarchical-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
