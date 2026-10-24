"""Compose ordered question reduction and method-relative solvability, without optical shortcuts."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define,args

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-pressure-leading-approximation.noema';PARENT_BASIS='data/pressure-leading-approximation-basis-v1.json'
FULL='examples/v014/einstein-problem-series-reduction.noema';CORE='examples/v014/problem-series-reduction-core.noema'
BASIS='data/problem-series-reduction-basis-v1.json';ANNOTATIONS='data/problem-series-reduction-identifiers-v1.json'
SEQUENCE='j[a]';QUESTIONS='h[a] g[a]';MAPPER='h[j[a]] a';CLASS='h[a] c'
PLANS='h[a a j[a] '+MAPPER+' d] c'
TUPLE=[('targets',SEQUENCE),('answers',SEQUENCE),('questions',QUESTIONS)]
REDUCTION=[('source','a'),('targets',SEQUENCE),('questions',QUESTIONS),('mapper',MAPPER)]
CLASSIFIED=REDUCTION+[('targetclass',CLASS)]
PLAN=[('method','a')]+CLASSIFIED+[('plans',PLANS),('context','d')]
PROBLEM=[(n,t) for n,t in PLAN if n not in ('targets','mapper')]
ALL=[(n,t) for n,t in PROBLEM if n!='source']+[('sourceclass',CLASS)]
MEANINGS={
 'ekvg':'指定された有限個体列と同じ長さの0始まりの有理整数位置列を、列のfoldと連結で構成する。位置は実際の列長から生成し、固定した二項だけや全有理数の標本を使わない。',
 'ekvh':'非空のtargets列の全項が同じtargetclassに属する。任意の有限長、順序、反復を保持し、一つの成功項だけで全列を分類しない。',
 'ekvi':'非空のtargetsと同じ長さのanswersの各同一位置について、同じquestions(target)へ対応するanswerがNoemaのanswer_matchesで合致する。全位置をekvgとfoldで巡り、別位置の答えや長さの不一致を拒否する。',
 'ekvj':'同じanswers列に同じmapperを適用して得た一個体の答えが、同じsourceの同じNoema質問に合致する。個体は構造を持つ解答記録の参照であり、実数や関数の値を暗黙に個体へ変換しない。',
 'ekvk':'非空の同じtargets列について、全ての有限answers列がekviなら同じmapperの再構成答えがekvjを満たすという還元の正しさ。元の答えが正しいことを前提にせず、対象問題の解の存在もこの条件だけでは保証しない。',
 'ekvl':'同じ有限問題列の全位置を満たす一つの同じ解答列が存在する。別々の部分的な成功を一つの完全解答へ取り替えず、空の問題列を成功としない。',
 'ekvm':'同じsource・targets・questions・mapperでekvkとekvlを併せる。還元の正しさと、還元先の完全な解答列の存在を区別しつつ共有する。',
 'ekvn':'同じsourceのNoema質問に合致する個体解答記録が存在する。具体的に計算又は実験を実行した、既に知っている、唯一の答えがあるという意味ではない。',
 'ekvo':'同じtargetclassへの全項分類ekvhと、同じ質問群と再構成写像によるekvkを結ぶ。還元先の種類を問題ごとに取り替えず、成功する答えを分類条件へ含めない。',
 'ekvp':'同じmethodがsourceを同じtargetsとmapperへ移す、contextで認められた手続き案plansの対応をekvoへ結ぶ。対応だけから正しさや解の存在を推論せず、無関係な写像での成功を同じ方法へ帰属させない。',
 'ekvq':'同じmethod・source・questions・targetclass・plans・contextに対して、一つのtargets列とmapperがありekvpを満たす。問題列と再構成写像は同じ証人で共有する。',
 'ekvr':'非空の全sourceclassの各問題について、同じmethod・質問族・還元先の種類・手続き案・状況でekvqが成立する。成功済みの部分範囲だけを全問題へ替えず、問題ごとに異なる有限列と写像を許す。',
 'ekvs':'同じ問題について、同じtargetsとmapperの証人でekvp及びekvlを要求する。この方法の認められた手続き案により解答を構成できるという候補条件であり、現在の実行済みを条件にしない。',
 'ekvt':'非空の全sourceclassの各問題について、同じmethodと状況でekvsを要求する。全範囲の還元可能性ekvrと、全範囲での還元先の解答存在を混同しない。',
 'ekvu':'同じ還元設定でekvmが成立すれば元の質問の解答が存在するekvnという論理的な帰結内容。原文の光学的な全問題の解決をこの一般形だけで認定しない。',
}
LIMITS=[
 'u0226の三文に必要な、一般の問題列・質問と解答・還元・方法に関する依存群である。既存406主張と全判断を保存し、この追加だけで新しい原文単位又は範囲を完了としない。',
 '問題は個体として参照し、questionsが各問題へ実際のNoema質問g[a]を与える。答えは構造を持つ個体記録として扱う型であり、任意の実数・関数を個体へ暗黙に変換したり、自然言語の文字列を解答内容の代用にしたりしない。光学への接続では記録の量・場・単位・設定と実際の質問条件を明示する必要がある。',
 '有限列は長さを固定しない。並び順、反復、全位置を保持し、答えは同じ位置の質問へ結ぶ。ここでは単項列も許す一般形であり、原文Reiheの複数性の採否は光学への接続で決める。数学的な無限列へ有限foldを代用しない。',
 '還元の正しさは全ての適格な完全解答列を同じ写像で元の正解へ戻せることである。還元先に解がなければ条件付きの正しさが成立し得るが、解決可能性ekvs/ekvtには別に完全解答列の存在を要求する。空の問題列による自明化は拒否する。',
 'plansは同じ方法・元問題・問題列・再構成写像・評価状況で認められた手続き案の全対応を渡す入力である。実行済みの履歴又は単なる偶然の関数一致ではない。具体的な方法との対応・実効的な構成の根拠・適用条件を後続で結び、任意の集合論的写像を光学的方法と認定しない。',
 '全問題範囲と還元先の種類は別の述語で与える。どちらも問いの内容・物理的対象と後続で結び、解ける問題や鏡の成功例だけを選ぶことでalle/jedesを満たしたことにしない。',
 '正しさを確認する全有限列の量化と、列・関数の証人の存在を有限候補のリストへ置き換えない。有限評価では具体的な列と実際の質問条件、量化の各位置を分けて診断し、未知入力の拒否を保持する。',
 '同じ動く物体の影響を受ける光、両場の同一出来事における変換、同じ物体に相対静止する系、方法の本質的役割、先行手続きへの参照と三文の著者提示は未接続。一般の問題還元を一つの原始関係へ格納せず、今回の合成をその接続に使用する。',
]

def length(x):return 'd['+x+']'
def position(xs,index,value):return 'a['+xs+']['+index+']['+value+']'
def fold(xs,initial,step):return 'q['+xs+']['+initial+']['+step+']'
def matches(problem,answer):return 'h['+app(v('questions'),problem)+']['+answer+']'

def definitions():
    zero='n p a b';true=op('e',zero,zero)
    indices=fold(v('items'),'l[b][]','i[prefix j[b] item a][m[v prefix][l[b]['+length(v('prefix'))+']]]')
    text=define('ekvg',[('items',SEQUENCE)],indices,'j[b]')
    nonempty=k('aa',zero,length(v('targets')))
    every=fold(v('targets'),true,'i[prior c item a]['+both(v('prior'),app(v('targetclass'),v('item')))+']')
    text+=define('ekvh',[('targets',SEQUENCE),('targetclass',CLASS)],both(nonempty,every))
    pair=q('g','problem','a',q('g','answer','a',both(position(v('targets'),v('index'),v('problem')),position(v('answers'),v('index'),v('answer')),matches(v('problem'),v('answer')))))
    every=fold(k('ekvg',v('targets')),true,'i[prior c index b]['+both(v('prior'),pair)+']')
    text+=define('ekvi',TUPLE,both(nonempty,op('e',length(v('targets')),length(v('answers'))),every))
    text+=define('ekvj',REDUCTION+[('answers',SEQUENCE)],matches(v('source'),app(v('mapper'),v('answers'))))
    body=op('y',k('ekvi',*args(TUPLE)),k('ekvj',*args(REDUCTION),v('answers')))
    text+=define('ekvk',REDUCTION,both(nonempty,q('f','answers',SEQUENCE,body)))
    text+=define('ekvl',[('targets',SEQUENCE),('questions',QUESTIONS)],q('g','answers',SEQUENCE,k('ekvi',*args(TUPLE))))
    text+=define('ekvm',REDUCTION,both(k('ekvk',*args(REDUCTION)),k('ekvl',v('targets'),v('questions'))))
    text+=define('ekvn',[('source','a'),('questions',QUESTIONS)],q('g','answer','a',matches(v('source'),v('answer'))))
    text+=define('ekvo',CLASSIFIED,both(k('ekvh',v('targets'),v('targetclass')),k('ekvk',*args(REDUCTION))))
    plan=app(v('plans'),v('method'),v('source'),v('targets'),v('mapper'),v('context'))
    text+=define('ekvp',PLAN,both(plan,k('ekvo',*args(CLASSIFIED))))
    for root,body in [('ekvq',k('ekvp',*args(PLAN))),('ekvs',both(k('ekvp',*args(PLAN)),k('ekvl',v('targets'),v('questions'))))]:
        text+=define(root,PROBLEM,q('g','targets',SEQUENCE,q('g','mapper',MAPPER,body)))
    selected=app(v('sourceclass'),v('source'))
    for root,inner in [('ekvr','ekvq'),('ekvt','ekvs')]:
        text+=define(root,ALL,both(q('g','source','a',selected),q('f','source','a',op('y',selected,k(inner,*args(PROBLEM))))))
    text+=define('ekvu',REDUCTION,op('y',k('ekvm',*args(REDUCTION)),k('ekvn',v('source'),v('questions'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==406
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='ordered_question_series_reduction_and_method_solvability_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/pressure-leading-approximation-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
