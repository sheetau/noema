"""Compose the author's caveat on local simultaneity and necessary abstraction."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_train_clock_example import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_kinematics_headings import SIM
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-train-clock-example.noema';PARENT_BASIS='data/train-clock-example-basis-v1.json'
FULL='examples/v014/einstein-local-simultaneity-note.noema';CORE='examples/v014/local-simultaneity-note-core.noema'
BASIS='data/local-simultaneity-note-basis-v1.json';ANNOTATIONS='data/local-simultaneity-note-identifiers-v1.json';INDEX=228
LOCAL='i[h[a a a d] c]';REMEDY='i[h[a a a d] c]'
PRIMITIVES={
 'eisfp':([('firstplace','a'),('secondplace','a'),('frame','a'),('context','d')],'二つの場所が同じframeと記述尺度で、局所的に同じ場所として扱う程度に近接しているという規約。実際には別々の広がりや離隔を持ち得るが、この局所同時性の概念設定で無視する空間的差の範囲内にある。原文にない固定距離・計器精度・光伝播補正を数値で補わず、任意の遠隔場所を含めない。厳密に同一の場所は合成側でも別に許す。'),
 'eisfq':([('issue','a'),('concept',SIM),('scope',LOCAL),('document','a'),('context','d')],'issueが、同じdocumentでconceptの関係をscopeの対象へ適用する概念に内在する不精密さである。物理的な出来事や場所は有限の広がり・識別条件を持つため、そのままでは理想的に同じ場所・時点という適用境界を無条件に一意化できないという、概念と物理的使用の対応上の問題を指す。単なる時計の故障、計算ミス、未知の数値、同時性概念全体の無意味さへ替えない。問題の所在と関係・対象範囲を保持し、その解消は別に述べる。'),
 'eisfr':([('abstraction','a'),('issue','a'),('document','a'),('context','d')],'abstractionが同じissueを扱うため、物理的な出来事や場所の有限の広がり・細部を捨象し、局所的な一致を理想的な点・時点の関係として使う概念的な操作である。どの差を捨象して何を保持するかを同じ対象範囲で定め、問題を否認したり高精度の計器を購入したりすることとは区別する。物理的な不精密さを消滅させる実験ではなく、当該概念の使用を可能にする理想化として橋渡しする。'),
 'eisfs':([('issue','a'),('remedy',REMEDY),('document','a'),('context','d')],'同じissueを処理してその概念を用いるには、remedyの閉じた型で指定する操作を通じて橋渡ししなければならないという必要条件である。単なる一つの選択肢、十分条件、既に実施した操作の存在、物理的な問題の完全消滅へ替えない。必要とされる操作の意味と同じissueへの向きを保持する。'),
 'eisft':([('author','a'),('issue','a'),('node','a'),('document','a'),('context','d')],'authorが同じdocumentのnodeで進める現在の説明ではissueを詳しく論じないという論述上の方針を示す。hierはこの箇所の議論の範囲であり、問題が存在しないこと、論じられないこと、どの文献でも永久に扱わないことではない。今ここでの不議論の方針であり、必要性の否定や他人への禁止でもない。'),
 'eisfu':([('node','a'),('issue','a'),('remedy',REMEDY),('document','a'),('context','d')],'同じnodeで、issueについてもremedy型の操作が必要になることを、物理的な概念設定に伴う他の理想化と同様の追加事項として位置付ける。gleichfallsに当たる添加の関係であり、先行する特定の問題の名称・件数・処理済みの事実を新たに補わない。操作の対象を別問題へ交換せず、既に橋渡しが完了したという意味にしない。'),
 'eisfv':([], '著者脚注u0279で指す、ほぼ同じ場所の二出来事に同時性概念を用いる際の同じ不精密さという論点。所在と内容はeisfqによって指定し、単なる問題名だけで脚注内容を代用しない。'),
}
MEANINGS={
 'eijd':'同じ系の異なる二出来事が、それぞれ割り当てられた場所にあり、その場所が同一又は同じ局所尺度で近接しているという適用範囲。出来事が実際に同時であることはこの局所範囲だけでは要求しない。',
 'eije':'同じ局所範囲eijdで既存同時性eihmを用いる概念にある同じ不精密さについて、抽象化eisfrによる橋渡しが必要であり、これも他の理想化と同様であること、ここでは詳しく論じない方針を結ぶ脚注内容。',
 'eijf':'脚注の不精密さ、抽象化の必要、添加、不議論の方針eijeを主張するメッセージ。抽象化を既に実行した事実や問題の否認へ替えない。',
 'eijg':'同じ著者・論説の同じ脚注箇所eisfnへeijfを帰属し、列車・時計の例の末尾の脚注1)と結ぶ。原文インベントリ末尾の配置を物理的な本文順序としない。',
}
LIMITS=[
 '原刊の(annähernd)を、厳密に同じ場所と同じ局所尺度で近接する場所を含む読みとして保持する。原文にない距離・時計精度の閾値や遠隔時計の同期規約を脚注の内容として補わない。',
 '不精密さは局所同時性という理想的な概念と物理的な出来事の記述との対応上の問題である。単なる計器誤差や概念の全面否定へ替えず、抽象化は必要な差の捨象を明示する理想化として読む。',
 'überbrückt werden mußは抽象化による橋渡しの必要性とし、実施済み・充分性・不精密さの物理的消滅を含意しない。gleichfallsを他の理想化と同様の追加として保持し、比較対象の固有名や処理済み件数は補わない。',
 'soll hier nicht erörtert werdenはこの箇所では詳しく論じないという著者の論述方針。永久的な禁止・議論不能・問題の不存在とはしない。',
 '固定u0279全212文字・185非空白文字を原刊893頁下部に対応させる。インベントリ末尾にある注のpage_at_end=921を原刊掲載頁として使わず、固定ファイルを変更せず原刊照合で実際の掲載頁を保持する。',
 '有限検査は局所範囲・同じ論点と操作型・必要性と非実施・不議論・脚注参照を確認する。物理的な理想化の妥当性、任意の実機精度、意味一致の自動証明を主張しない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    locations=q('g','left','a',q('g','right','a',both(k('cb',v('first'),v('left'),v('frame')),k('cb',v('second'),v('right'),v('frame')),op('x',op('e',v('left'),v('right')),k('eisfp',v('left'),v('right'),v('frame'),v('context'))))))
    text+=define('eijd',[('first','a'),('second','a'),('frame','a'),('context','d')],both(op('u',op('e',v('first'),v('second'))),k('zbd',v('first')),k('zbd',v('second')),k('va',v('frame')),locations))
    text+=content('eije',both(k('eisfq',k('eisfv'),'r[p eihm]','r[p eijd]',k('eirf'),v('point')),k('eisfs',k('eisfv'),'r[p eisfr]',k('eirf'),v('point')),k('eisfu',k('eisfn'),k('eisfv'),'r[p eisfr]',k('eirf'),v('point')),k('eisft',k('rd'),k('eisfv'),k('eisfn'),k('eirf'),v('point'))))
    text+='d eijf[] f[j s[k eije[]]].\n'
    text+=define('eijg',[],both(k('eir3',k('eisfn'),k('rd'),k('eirf'),quote('eijf'),k('ri')),k('eisfo',k('eisfm'),k('eisfn'),k('eirf'),'n p b b',k('ri')),op('u',op('e',k('eisfm'),k('eisfn')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eijg',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='local_simultaneity_imprecision_abstraction_and_discussion_limit_note',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/train-clock-example-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
