"""Compose location questions, their presupposition and theoretical rejection."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-unipolar-machine.noema';PARENT_BASIS='data/unipolar-machine-basis-v1.json'
FULL='examples/v014/einstein-seat-questions.noema';CORE='examples/v014/seat-questions-core.noema'
BASIS='data/seat-questions-basis-v1.json';ANNOTATIONS='data/seat-questions-identifiers-v1.json';INDEX=362
TOPIC=[('concept','a'),('setting','a'),('context','d')]
PRIMITIVES={
 'eisrk':(TOPIC,'同じconceptについて論じる所在の問いの適用設定がsettingである。settingは仮想的な配置を含む問題設定であり、実在装置や実験実施を要求しない。問題に含まれる全設定を数え、理論が前提を拒絶したものだけに限定しない。個別の問い・答え・前提・評価は別に構成する。'),
 'eisrl':(TOPIC[:2]+[('site','a')]+TOPIC[2:],'同じconceptとsettingの所在探究で、siteをその作用の発生場所として挙げる候補条件。siteは対象内の部分又は場所として同じ配置に結び付く。これは探究の提案する答えの条件であり、自立した物理的発生源の実在・理論による承認・既知性を断言しない。座標値だけや語の綴りを場所の帰属の代用にしない。'),
 'eisrm':([('source','a'),('concept','a'),('setting','a'),('context','d')],'同じsettingでsourceがconceptの作用を物理的に生む自立した担い手である。ここで自立とは、当該作用の源としての身分が記述系を選んで既存作用を分解する定義だけに依存せず、理論上独立に帰属することである。概念が補助的に定義できるだけの場合や、作用する局所値があるだけの場合とは区別する。特定の電磁概念又はその不存在を規約に埋め込まない。'),
 'eisrn':([('source','a'),('site','a'),('setting','a'),('context','d')],'同じsettingでsourceという作用の担い手がsiteに所在するという物理的帰属。候補の提案・知識・文字列の一致とは区別する。特定の座標系での数値表示を必須にせず、物理的場所の同一性を保つ。'),
 'eisro':([('question','g[a]'),('premise','e'),('context','d')],'このcontextの探究としてquestionを実質的な問いと扱う際に、premiseという内容を意味上必要な前提として置く。単なる会話上の推測や答えの既知性とは区別する。前提の真理、問いの発話、回答の実行は含意しない。'),
 'eisrp':([('theory','a'),('premise','e'),('context','d')],'同じcontextでtheoryがpremiseの内容を理論上の記述対象又は独立した物理的帰属として積極的に退ける。未調査・不明・単なる不言及・答えが未取得であることとは区別する。理論による拒絶という関係であり、内容を評価して偽であることだけからこの関係を推論しない。'),
 'eisrq':([('view','a'),('question','g[a]'),('premise','e'),('context','d')],'viewが同じquestionをpremiseに基づく実質的な探究として扱う。同じ問いと前提への従前の扱いを記録できる一般関係であり、実際の発問、既知の回答、前提の真理を含意しない。'),
 'eisrr':([('topic','i[h[a a d] c]'),('concept','a'),('classrule','i[h[a d] c]'),('document','a'),('node','a'),('context','d')],'documentのnodeの括弧書きが、conceptについてtopicが指定する問題の適用先として、classruleで構成する対象類を取り上げる。両規則は同じcontextで解釈し、対象類に属する装置に関する設定を話題へ結ぶ。全問題をこの対象類だけへ限定する関係でも、対象の実在や著者の発明を主張する関係でもない。引用した規則の自動実行はしない。'),
 'eisrs':([], '固定原文einstein-1905:u0177第二文の所在の問いへの評価と追加提示を行う箇所。'),
}
MEANINGS={
 'ekal':'同じ概念と問題設定に対して、提案された発生場所を答えとする個体型の問いを構成する。前提の承認、答えの存在・一意性・既知性を断言せず、著者の発問という発話でもない。',
 'ekam':'同じ概念と問題設定で、自立した作用の担い手が存在し、その担い手の物理的所在があるという内容。場所と担い手は同じ存在証人で結び、概念自体や局所力の存在だけとは区別する。',
 'ekan':'同じ問いekalと前提ekamを保ち、問いがその前提を必要とすること、従前の見方がそれに基づいて問いを扱うこと、新理論がその前提を退けることを結ぶ。これを理論の交替によって問いが対象を失うという読みとする。',
 'ekao':'対象となる設定の範囲が非空で、そこに属する全ての設定について同じ概念・従前の見方・新理論でekanが成立する。単極機だけへ狭めず、成功した拒絶例だけを選ばない。',
 'ekap':'展開した理論における同じ電動力概念を先行の物理的役割へ結び、従前の見方からの所在の問いの失効と、単極機を適用先として取り上げる括弧の役割を同じ概念証人に結ぶ第二文の内容。',
 'ekaq':'第二文内容を同じ著者の主張へ帰属し、第一文の非対称性解消を保持して加えるAuchを結ぶ。',
 'ekar':'第二文の主張と追加提示ekaqを述べるメッセージ。',
 'ekas':'第二文を著者・論説へ帰属し、第一文に続く別の箇所として本文へ接続する。',
}
LIMITS=[
 'Sitzの引用符を、記述系に依存する分解から独立した起電作用の本来的な発生場所を求める問いの読みへ反映する。前段の補助概念と系依存性を踏まえた明示的な解釈であり、通常の局所的な力の場所を問う全ての質問を無意味とする主張ではない。',
 'gegenstandslosを、この読みの問いに必要な自立した源の前提を展開した理論が退けるため、従来の探究としての対象を失うことと読む。候補集合が空、未回答、不明、力そのものが存在しないことへ置き換えない。問いは内容として構成し、著者が回答を求める発問にしない。',
 'werdenは従前の見方から展開した理論への記述上の移行として読む。時刻に伴う装置や力の物理的消失、従前の前提の真理、前段からの自動的な論理導出を付け加えない。',
 '電動力概念は同じeisqs・ejygへ結ぶ。回路の仕事/電荷を局所三成分に置換せず、起電作用と一般の機械的力を混同しない。括弧内の単極機は既存ekajの装置類を問題の適用先として取り上げる。全ての問いの排他的な範囲指定とは読まない。',
 'Auchは第一文の非対称性解消を保持して第二文を加える。新理論による前提の拒絶は著者の理論的判断として明示し、有限検査の真偽や補助概念だけという性質から自動的に推論しない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    c,s,ctx=map(v,('concept','setting','context'))
    text+=define('ekal',TOPIC,'j v[i[site a]['+k('eisrl',c,s,v('site'),ctx)+']]','g[a]')
    premise=q('g','source','a',both(k('eisrm',v('source'),c,s,v('point')),q('g','site','a',k('eisrn',v('source'),v('site'),s,v('point')))))
    text+=define('ekam',TOPIC[:2],'b point['+premise+']','e')
    question=k('ekal',c,s,ctx);p=k('ekam',c,s)
    fields=[('theory','a'),('view','a')]+TOPIC
    text+=define('ekan',fields,both(k('eisro',question,p,ctx),k('eisrq',v('view'),question,p,ctx),k('eisrp',v('theory'),p,ctx)))
    scope=k('eisrk',c,s,ctx)
    text+=define('ekao',[f for f in fields if f[0]!='setting'],both(q('g','setting','a',scope),q('f','setting','a',op('y',scope,k('ekan',*args(fields))))))
    point=v('point');theory=k('eisqw')
    claim=both(k('eisqy',theory,k('eirf'),quote('eigj'),k('zno'),point),q('g','concept','a',both(k('ejzt',theory,c,point),k('ekao',theory,k('eisak'),c,point),k('eisrr','r[p eisrk]',c,'r[p ekaj]',k('eirf'),k('eisri'),point))))
    text+=content('ekap',claim)
    text+=content('ekaq',both(k('uh',k('eisrs'),k('rd'),quote('ekap'),k('zno'),point),k('eisrb',k('eisq7'),k('eisrs'),k('rd'),quote('ekac'),quote('ekap'),k('zno'),point)))
    text+='d ekar[] f[j s[k ekaq[]]].\n'
    text+=define('ekas',[],both(k('eir3',k('eisrs'),k('rd'),k('eirf'),quote('ekar'),k('ri')),k('ue',k('eisq7'),k('eisrs'),k('ri')),op('u',op('e',k('eisq7'),k('eisrs')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekas',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='seat_questions_presupposition_and_theoretical_rejection',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/unipolar-machine-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
