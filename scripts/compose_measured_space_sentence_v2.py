"""Reuse the preceding K/k naming instead of declaring their names again."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_measured_space_sentence import ROOT,read,INDEX,COORDINATES
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-measured-space-sentence.noema';PARENT_BASIS='data/measured-space-sentence-basis-v1.json'
FULL='examples/v014/einstein-measured-space-sentence-v2.noema';CORE='examples/v014/measured-space-sentence-core-v2.noema'
BASIS='data/measured-space-sentence-basis-v2.json';ANNOTATIONS='data/measured-space-sentence-identifiers-v2.json'
MEANINGS={
 'eiya':'先行する運動設定zcgでK/kを同じra/zbmの呼称として採用した対応を保持し、現在の六座標記号をそれぞれの測定規則へ結ぶ。現在箇所zc2でK/kの新たな命名宣言を追加しない。',
 'eiyb':'同じ測定済み内容eix3の思考上の想定・仮定採用と先行運動設定への追加に、eiyaの既出名称と六座標の対応を結ぶ。',
 'eiyc':'測定済みの配置を考える行為eiybを述べるメッセージ。実測済みの報告や新しい系の命名ではない。',
 'eiyd':'u0045第一文の修正済みメッセージeiycを同じ著者・論説へ帰属し、u0044第二文からの順序を保持する。',
}
LIMITS=[
 '第一文の物理条件・六座標規則・思考設定はv1から保持する。K/kは既出の名称の再使用であり、現在文での新たな命名行為というv1の過剰な条件を訂正する。',
 '先行zcgの命名条件はu0044のeiwwと同じ対応である。新たな関係を追加せず、現在のzc2で命名したという条件を使わない。旧本文・意味規約・検査・一文判断記録は保存し、新しい一文判断が旧判断に優先する。',
 'u0045第二文と全単位の判断、二作品全体は未完。',
]

def definitions():
    clauses=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,printed,rule,frame,role in COORDINATES]
    clauses += [k('eisd4',k('zcg'),k('rd'),k(sign),k(target),k('eirf'),v('point')) for sign,target in (('eisnb','ra'),('eisna','zbm'))]
    text=content('eiya',both(*clauses))
    text+=content('eiyb',both(k('eislz',k('zc2'),k('rd'),quote('eix3'),k('eisms'),v('point')),k('ug',k('zc2'),k('rd'),quote('eix3'),k('eisms'),v('point')),k('zao',k('zcg'),k('zc2'),k('eisms'),v('point')),'t[k eiya[]][v point]'))
    text+='d eiyc[] f[j s[k eiyb[]]].\n'
    text+=define('eiyd',[],both(k('eir3',k('zc2'),k('rd'),k('eirf'),quote('eiyc'),k('ri')),k('ue',k('zco'),k('zc2'),k('ri')),op('u',op('e',k('zco'),k('zc2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==271;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    assert doc['statements'][INDEX]['body']['symbol']=='eix7';doc['statements'][INDEX]['body']['symbol']='eiyd'
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='measured_space_with_reused_frame_names',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS,interpretation_revision=dict(statement_index=INDEX,previous='eix7',replacement='eiyd',reason='The current sentence reuses K/k; naming occurred at zcg, not zc2.',equivalence_to_parent_proven=False))
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/measured-space-sentence-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
