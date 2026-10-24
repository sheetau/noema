"""Compose common explanatory classifications for the introductory current cases."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define,args
from scripts.compose_observable_contrast import FIELDS,RULE,allowed,category
from scripts.compose_relative_history_match import FIELDS as MOTION,history
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-auxiliary-role.noema';PARENT_BASIS='data/auxiliary-role-basis-v1.json'
FULL='examples/v014/einstein-asymmetry-resolution.noema';CORE='examples/v014/asymmetry-resolution-core.noema'
BASIS='data/asymmetry-resolution-basis-v1.json';ANNOTATIONS='data/asymmetry-resolution-identifiers-v1.json';INDEX=360
KEY_NAMES=('left','right','process','scope','firstframe','firstcontext','secondframe','secondcontext','reference')
KEYS=[(n,dict(FIELDS)[n]) for n in KEY_NAMES]
WITNESSES=[(n,t) for n,t in FIELDS if n not in KEY_NAMES]
GEN_NAMES={n for n,_ in MOTION}|{'quantityunit','sections','firstcumulative','firstcurrent','secondcumulative','secondcurrent','process','reference'}
GENERATION=[(n,t) for n,t in FIELDS if n in GEN_NAMES]
CONTENT=[('left','a'),('right','a'),('process','a'),('view','a'),('reference','d')]
COMPARISONS=[(n,t) for n,t in KEYS if n not in ('left','right','process','reference')]
PRIMITIVES={
 'eisq5':(GENERATION,'同じprocess・二物体の相対的な配置の変化が、rightの指定された電荷輸送・電流履歴の生成に物理的に寄与するという帰属。二つの記述は同じ物質点・長さ時間単位・全履歴・区間対応に従い、輸送量と電流は同じ導体・電荷単位・有向断面へ結ぶ。単なる同時存在、順序、相関、電流値の一致からこの生成を認定しない。相対履歴の一致・物体の種類・場との結合・電流の妥当性は別に合成する。他の作用の併存や零交差を許し、全時刻での非零、相対運動だけの必要十分な因果、実験実施や微視的機構の証明を含意しない。どの説明機構に分類するかはこの関係で決めない。'),
 'eisq6':([], 'この論説で展開した同じ理論を著者が採用して電磁的な現象を説明する見方への参照。序文で取り上げた通常の理解eisakと区別する。具体的な理論eisqwへの対応はeisayで指定し、この参照だけで説明の対称性や物理的真理を認定しない。'),
 'eisq7':([], '固定原文einstein-1905:u0177の第一文Es ist ferner klarからverschwindet.までの提示箇所。'),
 'eisra':([('node','a'),('author','a'),('document','a'),('antecedent','a'),('prior','i[e]'),('current','i[e]'),('scope','a'),('context','d')], '同じ著者がdocumentのnodeでcurrentを述べるとき、同じscopeについてantecedentで既に取り上げたpriorの論点を受け直しているという後方参照。先行箇所と両内容を固定し、似た語を持つ別の論点への交換を許さない。先行内容の真理を現在の著者が無条件に再承認することや、解消・否定・証明をこの参照だけで含意しない。それらはcurrentで別に記述する。'),
 'eisrb':([('prior_node','a'),('node','a'),('author','a'),('prior','i[e]'),('added','i[e]'),('scope','a'),('context','d')], '同じ著者が同じscopeで先行箇所のpriorを維持し、その上にnodeのaddedを追加して提示する。追加方向と同じ議論の継続を保持する。論理的な導出、因果、内容の実行、強さの順位、先行の撤回、他の追加項目の網羅は含意しない。'),
}
MEANINGS={
 'ejz5':'同じ見方・比較範囲・二場合について、許容する完全な説明が少なくとも一つあり、その全てで両場合に共通の生成・説明機構の分類が存在する。分類の観点は既存eisagを保持し、単なる事例名や同じ数値結果へ替えない。分類集合の完全一致や説明記録の一意性は要求しない。',
 'ejz6':'同じ磁石・導体の物理的に妥当な二場合eida、同じ相対履歴eia2、磁石運動/導体静止とその逆の役割、および同じ電流履歴への相対運動の生成寄与eisq5を結ぶ。電流値の一致や説明分類の共通性を前件へ入れない。',
 'ejz7':'同じ二物体・過程・比較範囲・二系・二状況・参照点を保ち、ejz6を満たす物理量・履歴・場・単位・能力規約があるという比較範囲への射影。異なる物理的な証人の断片を継ぎ合わせない。',
 'ekaa':'ejz7に属する比較なら、指定した同じ見方でejz5の共通機構による説明が許容説明全体に成立する。範囲を外れた配置へ無条件に同じ電流や機構を主張しない。',
 'ekab':'同じ二物体・過程・見方・参照点で、全ての範囲・二系・二状況にekaaを要求する。許容される比較がある場合に説明が空で済むことを認めず、観測済みの一比較だけで全体を代用しない。',
 'ekac':'同じ論説の展開済み理論eisqwに対応する現在の見方eisq6で、序文の磁石eisaa・導体eisab・過程eisacの全比較にekabを述べる第一文の内容。通常の理解eisakの非対称性を消去・上書きせず、現在の理論での解消を表す。',
 'ekad':'同じ第一文の内容を著者が主張し明白だと提示する。序文の一般的な非対称性eiezと同じ例での区別eidhを受け直す参照、および先の補助概念の結論ejzwへさらに加える提示を結ぶ。',
 'ekae':'非対称性解消の内容と後方参照・明白さ・追加の提示ekadを述べるメッセージ。',
 'ekaf':'第一文を同じ著者・論説へ帰属し、u0176の最後の提示に続けて本文へ追加する。',
}
LIMITS=[
 '序文の通常の理解による二場合の必然的な説明上の区別を、展開済みの理論で共通の機構分類による説明ができるようになることとして読む。同じ分類観点を保ち、電流の数値が一致することだけや、電場と磁場の成分が全系で同一であることへ縮めない。',
 '共通分類は全ての許容説明に要求するが、各説明が持つ全分類集合の一致、説明の一意性、語の一致を追加しない。説明が空のために全称が真になる場合を各比較で除外する。',
 '対象は序文の同じ磁石・導体の比較範囲であり、物質点・回路や準備・尺度・相対履歴の既存規約を引き継ぐ。相対運動が電流生成に寄与する物理的帰属を独立に接続し、電流の一致や既存の二つの説明が真であることを比較の前件にしない。',
 '通常の理解eisakでのeidhの区別と、現在の理論eisqwを読むeisq6での共通説明を区別する。原著者の主張を記述し、場の法則から実際にこの結論を証明したとはしない。',
 'in der Einleitungは固定された同じ序文の一般論eir7と例の対照eisajへの後方参照として保持する。fernerは先の補助概念の結論への追加、klarは同じ内容を著者が明白と提示する役割として読む。',
 'ここで扱うのはu0177第一文。第二文の単極機とSitzの問いは未接続であり、全単位の完成件数を増やさない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    shared=q('g','label','a',both(category(v('account'),'first',v('label')),category(v('account'),'second',v('label'))))
    text+=define('ejz5',RULE,both(q('g','account','a',allowed(v('account'))),q('f','account','a',op('y',allowed(v('account')),shared))))
    roles=both(k('eiag',*history('first','left')),k('eiah',*history('first','right')),k('eiah',*history('second','left')),k('eiag',*history('second','right')))
    text+=define('ejz6',FIELDS,both(k('eida',*args(FIELDS)),k('eia2',*args(MOTION)),roles,k('eisq5',*args(GENERATION))))
    text+=define('ejz7',KEYS,bind(WITNESSES,k('ejz6',*args(FIELDS))))
    text+=define('ekaa',KEYS+[('view','a')],op('y',k('ejz7',*args(KEYS)),k('ejz5',*args(RULE))))
    all_cases=k('ekaa',*args(KEYS),v('view'))
    for n,t in reversed(COMPARISONS):all_cases=q('f',n,t,all_cases)
    text+=define('ekab',CONTENT,all_cases)
    p=v('point')
    text+=content('ekac',both(k('eisqy',k('eisqw'),k('eirf'),quote('eigj'),k('zno'),p),k('eisay',k('eisqw'),k('eisq6'),k('eirf'),p),k('ekab',k('eisaa'),k('eisab'),k('eisac'),k('eisq6'),p)))
    refs=[k('eisra',k('eisq7'),k('rd'),k('eirf'),k(node),quote(prior),quote('ekac'),k('eisac'),p) for node,prior in [('eir7','eiez'),('eisaj','eidh')]]
    text+=content('ekad',both(k('uh',k('eisq7'),k('rd'),quote('ekac'),k('zno'),p),k('zdg',k('eisq7'),k('rd'),quote('ekac'),k('zno'),p),*refs,k('eisrb',k('zpw'),k('eisq7'),k('rd'),quote('ejzw'),quote('ekac'),k('zno'),p)))
    text+='d ekae[] f[j s[k ekad[]]].\n'
    text+=define('ekaf',[],both(k('eir3',k('eisq7'),k('rd'),k('eirf'),quote('ekae'),k('ri')),k('ue',k('zpw'),k('eisq7'),k('ri')),op('u',op('e',k('zpw'),k('eisq7')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekaf',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='common_explanatory_mechanism_for_introductory_currents',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/auxiliary-role-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
