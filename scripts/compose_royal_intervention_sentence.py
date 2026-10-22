"""Integrate the twelfth sentence, its quotation and critical presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_royal_intervention_conditions import NAMES,ARGS

PARENT='examples/v016/kant-monarchical-religion-sentence.noema'
PARENT_BASIS='data/monarchical-religion-sentence-basis-v1.json'
DEPENDENCIES=('data/royal-intervention-conditions-basis-v1.json','data/royal-insight-reproof-basis-v1.json','data/royal-despotic-support-basis-v1.json')
FULL='examples/v016/kant-royal-intervention-sentence.noema';CORE='examples/v016/royal-intervention-sentence-core.noema'
BASIS='data/royal-intervention-sentence-basis-v1.json';ANNOTATIONS='data/royal-intervention-sentence-identifiers-v1.json'
FAMILY='i c[h[j[a] d] e]';WHOLE='i d[e]'
REF='k h26je[]';CTX='k h255n[]';SOURCE='k wa[]'
PRIMITIVES={
 'h26je':('[] d',[],'第六段落第十二文の君主の著作監督・威厳の損傷・二側の比較を扱う一般論述基準。直前と同じ君主的役職と政治的共同体を論じ、個々の仮定場面の内側基準や文章の提示文脈と区別する。特定の国・実在者・現在の出来事に限定しない。'),
 'h26jf':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','event','evaluation','reference','context'],
   '提示者が同じ全体・対象範囲・基準の下で、指定した出来事を指定の好意的な評価内容によって描写して提示する。段階2の閉じた内容族へ同じ対象列・基準・場面を渡し、別行為の評価へ移さない。出来事や評価の現実の真理、著者の誠実な是認、過去の他者の発言を含意しない。hzxsの評価的描写をこの内容族の型へ適用する。'),
 'h26jg':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','event','evaluation','reference','context'],
   '同じ箇所・全体・範囲・出来事・評価の描写において、提示者がその好意的評価をそのまま是認する立場から批判的に距離を置くことを表現する。段階2の同じ内容族と基準を保つ。単なる態度不明や引用だけとは区別し、評価の論理的否定、正反対の意味、悪意、実際の発言・笑いを導かない。hzxtと同種の提示態度をこの型へ適用する。'),
 'h26jh':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','focus','reference','context'],
   '著者が同じ全体・範囲で、指定の焦点内容を、通常の期待ではそこまで及ぶと考えにくい対象又は観点にも当てはまるものとして取り立てる。焦点の同じ対象列・基準を保持し、具体的に述べられていない全代替例の真理、唯一性、数値的な最上位を補わない。焦点の現実の実行は要求しない。'),
 'h26ji':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','first_condition','first_result','second_condition','second_result','reference','context'],
   '著者が同じ全体・範囲で二つの条件付き内容をともに当てはまる側として並列する。それぞれの前件と帰結を同じ対象列・基準へ結び、二側の排他性、全場合を尽くす二者択一、片側だけへの限定、前件の現実の成立を補わない。'),
 'h26jj':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','first_side','second_side','comparison','reference','context'],
   '著者が同じ二側について、第一側で既に述べた程度を踏まえ、第二側の程度がさらに大きく、その隔たりを強く示す追加的な比較として提示する。同じ範囲・基準と明示した比較内容を保持し、時間的な後発、数値倍率、第一側の撤回、二側の排他性を加えない。比較内容の真理は引用から実行しない。'),
 'h26jk':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','graded_event','specification','reference','context'],
   '著者が同じ全体・範囲で、指定した出来事の程度が、指定した同じ行為内容に至るほどであると、その具体化によって示す。同じ対象列・基準・行為を保ち、無関係な後続事件、数値閾値、時間的な必然的結果へ替えない。程度の提示と実際の行為・評価を区別する。'),
 'h26jl':('[a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','event','manner','reference','context'],
   '著者が同じ全体・範囲における指定出来事を、指定した同じ行為の具体的な仕方によって説明する。同じ対象列・基準・行為の対応と説明の向きを保持し、単なる隣接・共起、全状況での同義性、唯一の可能な方法、現実の実行を含意しない。'),
 'h26jm':('[a a a '+WHOLE+' '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','form','whole','scope','condition','reproof','literal','application','reference','context'],
   '著者が同じ全体・範囲・条件の下で、指定の批判内容を、同じ引用表現の文言によって提示する。その表現の字義的な閉じた原則内容と、本文の同じ対象への文脈的な適用を別々に結び、どちらも同じ対象列・基準に対応させる。表現の正確な文言と範囲は固定原文の記録で照合し、内容を原語の名前だけで代用しない。字義内容から適用先への自動的な論理的導出、歴史上の直接の典拠、現実の批判発言や原則の実行評価は追加しない。'),
 'h26jy':('[] a',[],'固定原文kant-1784:u0013[3935,3967)のラテン語格言の引用表現そのもの。人物名や主張の真理値とは異なる表現対象であり、正確な文言を引用記録に保存し、字義内容r5pvと本文への適用r5puを別々の合成内容として結ぶ。'),
}
NODE_INFO={
 'h26jn':([3645,4155],'第十二文全体。著作への介入と威厳の損傷、二側と程度比較。'),
 'h26jo':([3645,3842],'基本の著作監督による介入と損傷の条件付き内容。'),
 'h26jp':([3843,3968],'自身の見識による介入と批判可能性の側。'),
 'h26jq':([3969,4155],'専制支援への権能使用とより大きな損傷の側。'),
 'h26jr':([3969,3996],'als auch und noch weit mehrの追加と程度比較。'),
 'h26js':([3653,3659],'selbstによる君主自身の威厳への取り立て。'),
 'h26jt':([3713,3842],'indemによる著作監督という介入の仕方の説明。'),
 'h26ju':([3808,3841],'seiner Regierungsaufsicht würdigtという評価的描写と批判的距離。'),
 'h26jv':([3935,3967],'Caesar non est supra Grammaticosという引用提示の箇所。'),
 'h26jw':([4027,4155],'so weit erniedrigtから支援へ至る程度の具体化。'),
 'h26j2':([3843,4155],'sowohl/als auchの二つの条件付き側の並列。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0013['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
NODES=('h26h5',*NODE_INFO,'h26jy')
MEANINGS={
 'r5ro':'固定一般基準h26jeで第十二文の全条件内容r5qzを返す。同じ最高職の基本介入、自身の見識側、専制支援側、全対応対の程度比較を保持する。',
 'r5rp':'同じ基準でr5raの基本介入から威厳損傷への一般条件を返す。',
 'r5rq':'同じ基準でr5rbの自身の見識側の損傷と批判可能性の一般条件を返す。',
 'r5rr':'同じ基準でr5rcの専制支援側の損傷の一般条件を返す。',
 'r5rs':'同じ基準でr5rdの対応する二側の程度比較の一般条件を返す。',
 'r5rt':'同じ十対象の第一活動が、同じ作品による検討r5pcへ実際に参加主体を伴ってh26inとして介入する内容。内容監督という具体的な仕方r5rfの説明先であり、無関係な宗教領域への介入としない。',
 'r5ru':'同じ十対象の第一活動が、同じ最高職を保持する君主の同じ作品への統治的内容審査h26ilと検討への介入となる内容。配慮に値すると扱うh26imだけを外して、評価的描写r5rfと同じ出来事を対応させる。',
 'r5rv':'同じ十対象の第二活動に、同じ最高職の実際の権能使用r5qbと全対象の支援への不相応な手段化r5qfを結ぶ。so weitの低め方の内容であり、物理的権力低下や失職とはしない。',
 'r5rw':'同じ十対象の第二活動による、同じ複数者の宗教的専制と残余臣民に対する全支援r5qaを取り出す。程度を具体化する同じ支援内容で、別の行為や別の仕組みを借りない。',
 'r5rx':'同じ十対象列を保持し、評価場面を固定基準としてr5pvの字義的な一般格言内容を返す。文法・言語・文献解釈の範囲に保ち、現実の歴史的人物の一発言に限定しない。',
 'r5ry':'同じ十対象の君主・共同体・領域についてr5puの原則を返す。格言の同じ宗教的認識領域への文脈的適用であり、字義的な文法領域からの論理的帰結とは主張しない。',
 'r5rz':'同じ十対象の第一活動についてr5pyの正当化可能な批判への曝露だけを取り出す。引用提示と同じ条件・行為・原則に対応させ、現実の批判発言を要求しない。',
 'r5sa':'第十二文全体と各条件内容を同じ著者・段落へ帰属し、前文からの順序、二側の並列、追加と程度、程度の具体化、介入の仕方、君主自身の威厳への取り立て、評価的描写と批判的距離、格言の正確な表現・字義内容・文脈的適用を結ぶ。引用内容を実際の事実として実行しない。',
}
LIMITS=[
 'u0013第十二文[3645,4155)435非空白文字全体を対象とする。一般的な著作への介入による威厳の損傷と、自己の見識による場合・宗教的専制支援の場合・対応する二側の程度比較を既存の全条件内容から保持する。',
 'selbstは、臣民の側だけでなく君主自身の公的威厳にまで損傷が及ぶという期待に反する取り立てと読む。実際の臣民の被害を別に断言したり、君主だけが損なわれるという限定にはしない。',
 'indemは同じ検討への介入を、同じ作品を統治的な内容監督の対象にする仕方で説明する。wodurch以下は既存r5pbの同じ作品の実際の利用と理解明確化の目標に保持し、既に明確化した成功や作品の単独著作性を補わない。',
 'würdigtは作品を自分の監督という配慮に値すると扱う評価的な描写と、その好意的な見せ方から著者が批判的に距離を取ることに分ける。著者の誠実な是認、君主の悪意、語義の単なる反転、評価内容の論理的否定は加えない。',
 'sowohl/als auchは二つの条件付き側をともに取り上げる並列である。二側の排他性や全介入を尽くす二者択一にせず、noch/weitは第一側を撤回しない追加的で大きな程度比較とする。数値比率や時間順へ替えない。',
 'so weit ... zu unterstützenは、最高職の権能をその職に不相応な補助手段へ低める程度を、その同じ専制支援によって具体化する。支援と評価の活動・最高職・仕組みを共有し、無関係な後の事件や法的な役職移譲としない。',
 'Caesar non est supra Grammaticosの正確な表現を固定転記と原刊画像の大文字Grammaticosに合わせて保存する。引用表現の対象h26jyと提示箇所h26jvを分け、原則の字義内容と本文の宗教的領域への適用を合成定義で別々に結ぶ。人物名の同定や語の綴りだけで意味を代用しない。',
 '格言は統治職だけでは専門的な正否の判断の上位に立てないという限界と読む。字義内容は文法・言語用法・文献解釈、本文への適用は明示した文脈的拡張である。実際に誰かが批判済みという叙述、専門家の無謬性や政治的統治権、直接の歴史的典拠は補わない。',
 'höchstenは君主が自分の基準で自分の見解を最上とみなす読みを採る。敬称的な含みもありうるが、著者が客観的な全知・認識の正しさを保証したとはしない。geistlichenは専制の領域を修飾し、担い手全員へ正式な聖職者資格を追加しない。',
 '比較は同じ評価側面・尺度、共通の無介入基準、対応する背景の下での両側の因果的損傷と第二側の大きな追加低下である。全現実の無関係な事例の交差比較へ広げず、結果を見て対を外さない。非空の対がある場合の全対比較と、現実に両活動が起きたという主張を区別する。',
 '原文のer/seiner/seine/seinemは同じ君主とその共同体に結び、sie/ihreは同じ臣民と理解内容を指す。übrigenは支援される複数者を除く同じ臣民全体と読み、対象ごとに別の支配仕組みを許す。全員の服属成功や現在の被害は要求しない。',
 '全語句との対応と通読は明示した解釈の下でのアシスタントの判断であり、有限検査による自動的な意味同値証明又は唯一の歴史解釈ではない。第六段落全体の統合判断と二作品全体の完成は別に確認する。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    text=''
    for n,target in (('r5ro','r5qz'),('r5rp','r5ra'),('r5rq','r5rb'),('r5rr','r5rc'),('r5rs','r5rd')):
        text+='d '+n+'[] e[k '+target+'['+REF+']].\n'
    pc='k r5pc[v actor v community v person v project v work v field v point v point]'
    act=both('k dg[v firstact v point]','k df[v actor v firstact v point]','k h26in[v firstact v project v point v point]')
    bare=both(pc,act,'k h234f[v office v community v point]','k r2ui[v actor v office v community v point]',
        'k h26il[v firstact v office v work v point v point]')
    adapters={'r5rt':both(pc,act),'r5ru':bare,
        'r5rv':both('k r5qb[v actor v office v community v secondact v point v point]','k r5qf[v office v actor v community v group v field v secondact v point v point]'),
        'r5rw':'k r5qa[v actor v community v group v field v secondact v point v point]',
        'r5rx':'t[k r5pv[v point]][v point]',
        'r5ry':'k r5pu[v actor v community v field v point v point]',
        'r5rz':'k r5py[v actor v community v field v firstact v point v point]'}
    for n,body in adapters.items():text+='d '+n+'[bindings j[a] reference d] e[b point['+bind(NAMES,body)+']].\n'
    whole='r d[k r5ro[]]';q=lambda n:'r c[p '+n+']';scope=q('r5re');head=SOURCE+' '+whole+' '+scope+' '
    claims=['k h236i[k '+node+'[] '+SOURCE+' r d[k '+target+'[]] '+CTX+']' for node,target in (
        ('h26jn','r5ro'),('h26jo','r5rp'),('h26jp','r5rq'),('h26jq','r5rr'),('h26jr','r5rs'))]
    claims += [
        'k h26jh[k h26js[] '+head+q('r5rg')+' '+REF+' '+CTX+']',
        'k h26jl[k h26jt[] '+head+q('r5rt')+' '+q('r5rf')+' '+REF+' '+CTX+']',
        'k h26jf[k h26ju[] '+head+q('r5ru')+' '+q('r5rf')+' '+REF+' '+CTX+']',
        'k h26jg[k h26ju[] '+head+q('r5ru')+' '+q('r5rf')+' '+REF+' '+CTX+']',
        'k h26ji[k h26j2[] '+head+' '.join(q(n) for n in ('r5rh','r5ri','r5rj','r5rk'))+' '+REF+' '+CTX+']',
        'k h26jj[k h26jr[] '+head+' '.join(q(n) for n in ('r5rh','r5rj','r5rm'))+' '+REF+' '+CTX+']',
        'k h26jk[k h26jw[] '+head+q('r5rv')+' '+q('r5rw')+' '+REF+' '+CTX+']',
        'k h26jm[k h26jv[] '+SOURCE+' k h26jy[] '+whole+' '+scope+' '+' '.join(q(n) for n in ('r5rh','r5rz','r5rx','r5ry'))+' '+REF+' '+CTX+']']
    edges=(('h26h5','h26jn'),('h26jo','h26jp'),('h26jp','h26jq'),('h26jt','h26ju'),('h26ju','h26jv'),('h26jv','h26jr'),('h26jr','h26jw'))
    claims+=['k ue[k '+a+'[] k '+b+'[] '+CTX+']' for a,b in edges]
    distinct=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(NODES) for b in NODES[i+1:]]
    claims += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5sa[] c['+both(*claims)+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r5sa',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='royal_intervention_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/monarchical-religion-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
