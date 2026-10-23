"""Connect current affine coefficients, the unfixed function and origin assumption."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_time_origin_affinity import ROOT,read,MATRIX,VECTOR,COEFFICIENTS
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-time-origin-affinity.noema';PARENT_BASIS='data/time-origin-affinity-basis-v1.json'
FULL='examples/v014/einstein-affine-time-claim.noema';CORE='examples/v014/affine-time-claim-core.noema'
BASIS='data/affine-time-claim-basis-v1.json';ANNOTATIONS='data/affine-time-claim-identifiers-v1.json';INDEX=286
FIELDS=[('matrix',MATRIX),('offset',VECTOR)]+COEFFICIENTS
MEANINGS={
 'ei4o':'同じ現在のτと同じアフィン行列・定数ベクトル・五係数について、補助座標への延長ei4nと偏微分係数smrを結ぶ。同じ出発時刻とV,vを用い、時間係数は同じ未定関数φ(v)である。',
 'ei4p':'先行する同じτの縦方向方程式と横二方向の零偏微分、同じ五係数のアフィン表示と偏微分値ei4o、別に採る時刻・空間原点規約ei4lを合わせた、時間式への著者の推論の前提内容。',
 'ei4q':'k原点でτ=0ならt=0という全対象の非空の時刻原点規約と、既出表示に合わせる空間零点、同じ現在のτの零値ei4lを述べる仮定内容。',
 'ei4r':'同じ著者が同じ第三節で、同じ係数に接続した前提ei4pから未定φ(v)を含むτの式smnが得られると述べる内容。',
 'ei4s':'線形性と先行微分方程式からτの式を得るという著者の提示ei4rを述べるメッセージ。',
 'ei4t':'u0062の式への帰結とu0063の式を同じ著者・論説へ帰属し、横二方向の零偏微分に続ける。',
 'ei4u':'同じ著者が同じ第三節で、同じφの候補を同じ速度域・考察段階に結ぶ未決定性smpを述べる内容。候補が複数残るという明示的な読みである。',
 'ei4v':'速度関数がこの段階では未決定であるという著者の提示ei4uを述べるメッセージ。',
 'ei4w':'u0064前半の暫定的未知性を同じ著者・論説へ帰属し、その係数を含む時間式に続ける。',
 'ei4x':'同じ第三節で同じ著者が原点内容ei4qを仮定ugとして採り、その同じ仮定を記述の簡潔さのためzexと位置付ける内容。',
 'ei4y':'時刻原点の仮定と簡潔さという理由ei4xを述べるメッセージ。',
 'ei4z':'u0064後半の原点仮定と簡潔さを同じ著者・論説へ帰属し、未定係数の説明に続ける。',
}
LIMITS=[
 'u0062–u0064を式の導入・表示式・係数と仮定の説明として接続する。原刊899頁の本文順序は帰結、未知係数、原点仮定であり、論理上の前提を定義した順序とは区別する。',
 'linearは先行の現在測定対応のアフィン性を引き継ぎ、同じ五係数を補助座標上の全実数へ延長する読みである。時間係数D+vAをφ(v)に結び、偏微分だけで定数Eを零にしない。',
 '同じτの四偏微分が同じアフィン係数であることをsmrで明示する。先行する全空間の縦横条件は同じ出発時刻で参照し、アフィン係数は全入力で一定とする。一般の微分の一意性と実数体の法則の自動証明ではない。',
 '原点条件ei4lの非空の時刻規約と別の空間ラベル選択を継承する。k原点でτ=0ならt=0を保ち、全時刻のt=τや全空間成分が零という時刻条件への追加にはしない。',
 'vorläufig unbekanntは現在の考察段階で異なる速度関数候補が残るという読みとする。現在のφも同じ許容速度域で候補族に結ぶ。唯一の解を知らないという知識一般や、全候補が後続の条件を満たすことまでは述べない。',
 '係数aは同じφの同じvでの値。1、符号、後段の係数へ固定しない。未測定の全実数入力が実際の出来事として存在することも要求しない。',
 '帰結zc、未決定内容uh、原点仮定ug、簡潔さzexは引用した内容の著者帰属であり、検査器がその物理的真理を証明したことにしない。新規原始語はない。',
]

def definitions():
    time=k('sjh',k('qe',k('zdq')),k('zb6'));coeff=[v(n) for n,_ in COEFFICIENTS]
    args=[v(n) for n,_ in FIELDS]
    text=define('ei4o',FIELDS,both(k('ei4n',k('zd4'),*args),k('smr',k('zd4'),k('tc'),k('zb7'),time,k('zeq'),*coeff)))
    witness=k('ei4o',*args)
    for n,s in reversed(FIELDS):witness=q('g',n,s,witness)
    text+=content('ei4p',both(k('skn',k('zd4'),k('tc'),k('zb7'),time),k('slm',k('zd4'),time),witness,k('ei4l',k('zb6'))))
    text+=content('ei4q',k('ei4l',k('zb6')))
    text+=content('ei4r',k('zc',k('zeu'),k('rd'),quote('ei4p'),quote('smn'),k('eisms'),v('point')))
    text+=content('ei4u',k('uh',k('zew'),k('rd'),quote('smp'),k('eisms'),v('point')))
    text+=content('ei4x',both(k('ug',k('zev'),k('rd'),quote('ei4q'),k('eisms'),v('point')),k('zex',k('zev'),k('rd'),k('eisms'),v('point'))))
    for body,message,author,node,previous in (('ei4r','ei4s','ei4t','zeu','zeo'),('ei4u','ei4v','ei4w','zew','zeu'),('ei4x','ei4y','ei4z','zev','zew')):
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(author,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ei4t','ei4w','ei4z')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_affine_tau_formula_unfixed_scale_and_origin_assumption',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(INDEX,INDEX+3))).document
    ann=json.loads(read('data/time-origin-affinity-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
