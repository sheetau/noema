"""Restrict the density inference to calibrated energy units in both frames."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_density_relativity import ROOT,read,BASE,VARIABLES,INDEX,LIMITS as PRIOR_LIMITS
from scripts.compose_observed_intensity import COEFFICIENT
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-density-relativity.noema';PARENT_BASIS='data/density-relativity-basis-v1.json'
FULL='examples/v014/einstein-density-unit-scope.noema';CORE='examples/v014/density-unit-scope-core.noema'
BASIS='data/density-unit-scope-basis-v1.json';ANNOTATIONS='data/density-unit-scope-identifiers-v1.json'
MEANINGS={
 'eklp':'先行64役割のeklfへ、旧系と新系の同じ長さ時間・力・二場・エネルギー単位及び換算係数を校正するeisteを加えた基礎設定。任意の未校正なenergyunit個体を適用域へ含めない。単位の対応は密度場モデルeistj・平均値・密度式とは別であり、それらを結論から前件へ移さない。',
 'eklq':'固定K・V・先行波の範囲・状況の下で、同じ60全称役割について校正を含む基礎設定eklpなら旧系の密度解釈eklgと述べる。',
 'eklr':'同じ60全称役割と同じ校正を含む前件eklpの下で新系の密度解釈eklhと述べる。校正されない単位候補への無条件の適用を除き、旧新で量化範囲を共有する。',
 'ekls':'同じ相対性原理eifjと、校正された単位での旧系密度eklqを同じ点で連言した帰結提示の前提。',
 'eklt':'第一文の同じ呼称・旧系説明・相対性原理による必須帰結・新系説明を、校正域を保持するeklq/ekls/eklrへ結ぶ修正版の提示。',
 'eklu':'校正された単位を共有する第一文の提示ekltを述べるメッセージ。',
 'eklv':'同じ第一文を同じ著者・論説へ帰属する修正版。現在の文番号385をこの内容へ置き換え、旧385主張は変更しない。',
}
LIMITS=[
 '前候補density-relativity-v1の第一文は、energyunitが前件で校正されず、全個体を単位候補として結論へ含める問題があった。旧候補・検査・読解記録を履歴として保存し、現在の第一文の判断は本版へ置き換える。全単位判断済みの旧385主張には依存変更がない。',
 '同じエネルギー単位の両系での校正eisteを前件へ明示する。これは仕事基準と指定単位の対応であり、旧新の密度モデルの採用eistj又はその平均密度式の真理を仮定するものではない。原文の共通単位規約に適合する全ての設定を扱う。',
 *PRIOR_LIMITS,
]

def definitions():
    calibration=[k('eiste',*[frame if n=='frame' else v(n) for n,t in COEFFICIENT]) for frame in (v('frame'),k('zbm'))]
    text=define('eklp',BASE,both(k('eklf',*args(BASE)),*calibration))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};actual=[fixed.get(n,v(n)) for n,t in BASE]
    for name,conclusion in [('eklq','eklg'),('eklr','eklh')]:text+=content(name,quantified('f',VARIABLES,op('y',k('eklp',*actual),k(conclusion,*actual))))
    text+=content('ekls',both(evaluate('eifj'),evaluate('eklq')))
    node=k('eistl');author=k('rd');scope=k('eistk');p=v('point')
    text+=content('eklt',both(k('eisch',k('ekll'),quote('eifj'),scope,p),k('uh',node,author,quote('eklq'),scope,p),k('zc',node,author,quote('ekls'),quote('eklr'),scope,p),k('uh',node,author,quote('eklr'),scope,p)))
    text+='d eklu[] f[j s[k eklt[]]].\n'
    text+=define('eklv',[],both(k('eir3',node,author,k('eirf'),quote('eklu'),k('ri')),k('ue',k('eistg'),node,k('ri')),op('u',op('e',k('eistg'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==386
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'][:INDEX]+[dict(kind='assert',body=dict(kind='call',symbol='eklv',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='calibrated_energy_unit_scope_for_density_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/density-relativity-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
