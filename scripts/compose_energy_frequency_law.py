"""Join the same enclosed energy and observed frequency under one motion law."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_energy_ratio import ROOT,read,TOTAL,FIXED,VARIABLES
from scripts.compose_doppler_specialization import EXTENDED
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-light-energy-ratio.noema';PARENT_BASIS='data/light-energy-ratio-basis-v1.json'
FULL='examples/v014/einstein-energy-frequency-law.noema';CORE='examples/v014/energy-frequency-law-core.noema'
BASIS='data/energy-frequency-law-basis-v1.json';ANNOTATIONS='data/energy-frequency-law-identifiers-v1.json';INDEX=393
COMMON=[(n,R) for n in ('light','speed','ax','energy','newenergy','frequency','newfrequency')]
PRIMITIVES={'eisua':'u0214の、同じ光の部分のエネルギーと周波数が観測者の運動状態に伴って同じ法則で変わることを注目すべきものと述べる箇所。'}
MEANINGS={
 'ekp3':'同じ70設定の一般総エネルギー比ekpnと、同じ観測者の受信周期数の一般Doppler則ekeuを、同じV・speed・旧方向axで正の二総量と二周期数が同じD=β(1−ax*speed/V)倍になるseckへ結ぶ。位相率rateを周期数frequencyへ取り違えず、数値の等しさ又は単位を越える量同一性にしない。',
 'ekp4':'同じK・V・波範囲・部分zvaa・状況を固定し、残る65役割の全割当で、ekpmの物理設定ならekp3の共通変換則であると述べる内容。speedを観測者の運動・受信経路・系の変換・両量の全経路へ共有する。一つの速度標本又は零角だけの一致へ縮めない。',
 'ekp5':'同じ共通変換則ekp4の引用記述に、同じ評価状況で注意を向ける価値zldと注目すべき基準zleをs2zで適用する。法則の真理、意外さ、読者の実際の注意又は固定した数値閾値とは区別する。',
 'ekp6':'著者が同じ箇所と第八節で共通変換則ekp4とその注目価値の評価ekp5を述べることを結ぶ。同じ部分の一般エネルギー比への参照を保ち、計算の実施済みや明示されない新しい証明要求を追加しない。',
 'ekp7':'同じ部分のエネルギーと周期数に対する共通変換則及び注目価値の評価を述べるメッセージ。',
 'ekqa':'u0214全文を同じ著者・論説へ帰属し、前の零角でのエネルギー比の表示の後へ置く。',
}
LIMITS=[
 '原刊914頁のu0214全133非空白本文文字を対象とする。Energie und Frequenz、eines Lichtkomplexes、nach demselben Gesetze、mit dem Bewegungszustande des Beobachters、bemerkenswertを一文の関係として保持する。',
 '同じ法則とは、同じ運動状態を入力とする同じ倍率D=β(1−av/V)で、E′=D*Eとν′=D*νがともに変換されることである。エネルギーと周波数の数値が等しい、量の種類や単位が同じ、異なる光にも同一の比例定数E/νがある、又は光量子則E=hνであるとの主張は追加しない。',
 '同じ部分zvaaと波・過程の対応はekpm→ekn7→ekn6の領域割当と全点平均・空間積分へ接続する。周波数は同じ源・波の周期と同じ観測者の受信経路からの既存eket/ekd3/ekd4/ekc7を使い、位相率rateそのものに替えない。',
 'Bewegungszustandはこの議論の校正された二慣性系の標準配置における0<v<Vと同じ旧方向角に関する観測者の相対運動である。同じspeedがekesのK側の運動eivuと新系受信経路、Lorentz変換へ渡る。加速の時間発展、光速観測者又は同一状況で相反する速度が同時に実在することを要求しない。',
 '許容する全割当への同じ関数形として述べ、有限の一組や特殊なφ=0だけの一致にしない。前件ekpmは両量の積分・周期等の物理的構成を保持し、共通倍率を満たす出力だけを先に選ばない。純粋な数値対照は零・符号付き亜光速も使うが、著者の適用域を拡張しない。',
 '総エネルギーは前文と同じ位相平均密度の空間積分である。周期数と同じ物理単位へ変換したり、全エネルギーを局所瞬間密度や振幅へ替えたりしない。旧総量と周期数が正の比の文脈を保持する。',
 'bemerkenswertは同じ法則の記述へ注意を向ける文脈上の価値が基準を満たすという著者の評価として読む。数値尺度と閾値の実値、驚きの心理、全読者の注目を補わない。法則の主張と評価を別々に帰属し、引用の評価だけで法則の真理を認定しない。',
 '過去のseia–seicの四記録による部分草案は保存するが、今回はその記録や未接続の量種類を実測済みとして再利用しない。既存seckの数値構成を現在の積分・周期・観測者へ結び直す。有限対照・有理補題・原文判断は独立査読又は物理法則や意味同義性の自動証明ではない。',
 '後続u0215以降の完全鏡、反射光の方向・周波数・強度・圧力及び第八節見出し全体は未完。',
]

def definitions():
    text='r eisua[] a.\n'
    text+=define('ekp3',TOTAL,both(k('ekpn',*args(TOTAL)),k('ekeu',*args(EXTENDED)),k('seck',*args(COMMON))))
    actual=[FIXED.get(n,v(n)) for n,t in TOTAL]
    text+=content('ekp4',quantified('f',VARIABLES,op('y',k('ekpm',*actual),k('ekp3',*actual))))
    p=v('point');node=k('eisua');author=k('rd');scope=k('eistk')
    text+=content('ekp5',k('s2z',quote('ekp4'),p,'p zld','p zle'))
    text+=content('ekp6',both(k('uh',node,author,quote('ekp4'),scope,p),k('uh',node,author,quote('ekp5'),scope,p),k('eisra',node,author,k('eirf'),k('eist2'),quote('ekps'),quote('ekp4'),scope,p)))
    text+='d ekp7[] f[j s[k ekp6[]]].\n'
    text+=define('ekqa',[],both(k('eir3',node,author,k('eirf'),quote('ekp7'),k('ri')),k('ue',k('eist5'),node,k('ri')),op('u',op('e',k('eist5'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekqa',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_light_energy_frequency_motion_law_and_attention_appraisal',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/light-energy-ratio-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
