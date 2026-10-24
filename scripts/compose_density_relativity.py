"""Attribute the old density premise and its relativity-based moving-frame use."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_radiative_density import ROOT,read,SETTING,DENSITY_MODEL,CYCLE,EXTENDED,AMPLITUDE,HARMONIC,FALSE
from scripts.compose_wave_transform_application import transformed
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-radiative-density.noema';PARENT_BASIS='data/radiative-density-basis-v1.json'
FULL='examples/v014/einstein-density-relativity.noema';CORE='examples/v014/density-relativity-core.noema'
BASIS='data/density-relativity-basis-v1.json';ANNOTATIONS='data/density-relativity-identifiers-v1.json';INDEX=385
BASE=[(n,t) for n,t in SETTING if n not in ('density','newdensity')]
VARIABLES=[(n,t) for n,t in BASE if n not in ('frame','light','scope','context')]
PRIMITIVES={
 'eistk':([], '同じ論説の第八節。u0202の見出しからu0226まで、光のエネルギー変換と完全鏡への放射圧を扱う区分。先行する波の仮定と記号の考察eisrxを参照するが、その区分や第八節の見出し箇所とは別である。'),
 'eistl':([], '固定原文einstein-1905:u0203[0,163)の第一文。旧系での単位体積当たりの光エネルギーを前提に、相対性原理により新系でも対応する量として扱うべきことを述べる箇所。u0203の残る文や次の球面表示とは別の範囲。'),
}
MEANINGS={
 'ekle':'同じpiと同じ非負振幅からamplitude²/(8*pi)を返す密度候補。適用時にpiの積分指定と振幅の物理的帰属を保持する。総エネルギーをこの値だけで指定しない。',
 'eklf':'同じ64役割に既存eket・許容速度・旧新の同じ電気側振幅・横波・原文の単位係数を結ぶ基礎設定。密度モデルの物理的採用、密度平均値及び結論の旧新密度式を前件へ含めない。',
 'eklg':'同じ64役割の旧系に、原文単位・仕事校正と結び付くekkzの密度モデル、同じ位相率・零原点・旧周期・旧周期数による平均ekk4を結ぶ。その平均値を同じ旧振幅のekleに指定する旧系の密度解釈。波の基礎設定scopeは継承し、密度モデルの考察scopeは第八節eistkへ結ぶ。',
 'eklh':'同じ64役割の新系zbmに、同じ速度で変換した六係数・位相・領域の密度モデルと、同じ観測経路の位相原点及び新周期・新周期数の平均を結ぶ。その平均値は同じ新振幅のekle。旧系の位相・周期又は密度を流用しない。',
 'ekli':'K・V・先行波の仮定範囲eisrx・状況を固定し、残る60役割の全てで基礎設定eklfなら旧系の密度解釈eklgと述べる内容。有限の一つの波だけ又は式の数値一致だけへ狭めない。',
 'eklj':'ekliと同じ60役割・同じ前件eklfに対して新系の密度解釈eklhを述べる内容。旧新で量化範囲を変更せず、結論の新密度モデルを前件へ混ぜない。',
 'eklk':'既存の同じ相対性原理eifjと旧系密度の内容ekliを同じ点で結ぶ、第一文の帰結提示の前提内容。引用の成立を帰属時に実行しない。',
 'ekll':'同じ相対性原理の既存呼称eiscgを返す別表記用参照。Relativitätsprinzipという複合語の印字を識別表記で保持し、別の原理を追加しない。',
 'eklm':'同じ相対性原理の呼称と内容を結び、旧系密度ekliを仮定範囲内で提示し、原理と旧系密度eklkから新系解釈ekljが従わなければならないという帰結提示zcと、その新系解釈への主張uhを合わせる。Da ... so ... nach ... haben wir ... zu betrachtenを、論述上の根拠及び帰結として保持する。',
 'ekln':'u0203第一文の旧系密度・相対性原理による新系適用の説明eklmを述べるメッセージ。',
 'eklo':'第一文の説明を同じ著者・論説へ帰属し、先行第七節末尾eistgからの本文順序を接続する。未完の第八節見出しの主題はこの順序だけで代用しない。',
}
LIMITS=[
 'u0203[0,163)の第一文全体を原刊913頁へ照合する。M0349=A²/(8pi)、M0350=A′²/(8pi)であり、同じ文前半のpro Volumeneinheitを新系のLichtenergieにも引き継ぐ。平均密度と総エネルギーを区別する。',
 '前回の周期平均という読みを保持する。瞬間密度は共通sin²Φに依存し、一周期の平均を同じ周期積分で構成する。原文に印字されていない平均の規約は解釈として明示し、現実の有限領域の瞬間総量と自動的に同一視しない。',
 '基礎設定は同じ源・波・過程・観測者・校正された二系・単位・近似・位相・周期・旧新振幅を共有する。旧新の密度モデルは基礎設定から分離して主張の帰結側へ置く。新系の密度説明を仮定した条件から同じ説明を結論する構成にはしない。',
 '同じ先行波の考察eisrxと新たな第八節eistkを区別する。既存のA及びA′のekiaによる同じ非負振幅を使い、密度モデルの採用範囲をeistkへ結ぶ。物理的な系・波・単位を新しく選ぶことを意味しない。',
 'Relativitätsprinzipは同じ呼称eiscgと内容eifjへの参照。名称だけや法則が共通という一部分だけへ内容を切り詰めず、原語の別表記は旧識別記録を変えずに追加する。',
 'Da ... so ... nach ... haben wir ... zu betrachtenは、著者が旧系の説明を前提として示し、同じ相対性原理に基づき新系の説明が従わなければならないと述べる提示として読む。論理的必然性を著者の帰結提示zcへ保持し、読者への行為命令、実測済み又は独立に検証された導出とはしない。',
 '零振幅と零平均密度を許す。後続のエネルギー比のために必要な非零分母、同じ光の集合、体積又は光速で動く球を第一文へ先取りしない。過去の一般振幅主張や光行差の不整合は変更しない。',
 'これは第一文の通読判断である。u0203の残る同体積の反実仮想・体積不一致と、u0204の球面を挟むu0205の保存・同じ集合・問い、u0202の節主題及び二作品全体は未完。',
]

def definitions():
    text=''.join('r '+name+'[] a.\n' for name in PRIMITIVES)
    zero=k('bb','n p a b');mul=lambda a,b:k('shv',a,b);V=v('light');speed=v('speed');coef=v('coefficient');pi=v('pi')
    text+=define('ekle',[('pi',R),('amplitude',R)],mul(mul(v('amplitude'),v('amplitude')),k('sjd',mul(k('bb','n p i b'),pi))),R)
    amps=[v(n) for n in ('ex','ey','ez','hx','hy','hz')];newamps,shifted,_,phase=transformed(speed)
    ampactual=[FALSE if n=='magneticside' else v(n) for n,t in AMPLITUDE]
    text+=define('eklf',BASE,both(k('eket',*args(EXTENDED)),k('ekev',V,speed),k('ekia',*ampactual),k('ekk2',coef,V,pi),k('seaj',*[v(n) for n in ('ax','ay','az')],*amps),k('seaj',*shifted[1:],*newamps)))
    oldphase=k('ekbf',V,v('rate'),v('ax'),v('ay'),v('az'));oldregion=k('ekau',v('space'),v('lower'),v('upper'));newregion=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    rows=[('eklg',v('frame'),oldphase,amps,oldregion,v('rate'),zero,v('oldperiod'),v('frequency'),v('amplitude')),
          ('eklh',k('zbm'),phase,newamps,newregion,shifted[0],v('newoffset'),v('newperiod'),v('newfrequency'),v('newamplitude'))]
    for name,frame,p,coefficients,region,rate,offset,period,frequency,amp in rows:
        replacements=dict(frame=frame,phase=p,region=region,scope=k('eistk'),**dict(zip(('ex','ey','ez','hx','hy','hz'),coefficients)))
        model=k('ekkz',*[replacements.get(n,v(n)) for n,t in DENSITY_MODEL])
        average=k('ekk4',coef,V,*coefficients,*args(HARMONIC),rate,offset,period,frequency,k('ekle',pi,amp))
        text+=define(name,BASE,both(model,average))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};actual=[fixed.get(n,v(n)) for n,t in BASE]
    for name,conclusion in [('ekli','eklg'),('eklj','eklh')]:text+=content(name,quantified('f',VARIABLES,op('y',k('eklf',*actual),k(conclusion,*actual))))
    text+=content('eklk',both(evaluate('eifj'),evaluate('ekli')))
    text+=define('ekll',[],k('eiscg'),'a')
    node=k('eistl');author=k('rd');scope=k('eistk');p=v('point')
    text+=content('eklm',both(k('eisch',k('ekll'),quote('eifj'),scope,p),k('uh',node,author,quote('ekli'),scope,p),k('zc',node,author,quote('eklk'),quote('eklj'),scope,p),k('uh',node,author,quote('eklj'),scope,p)))
    text+='d ekln[] f[j s[k eklm[]]].\n'
    text+=define('eklo',[],both(k('eir3',node,author,k('eirf'),quote('ekln'),k('ri')),k('ue',k('eistg'),node,k('ri')),op('u',op('e',k('eistg'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eklo',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='density_relativity_first_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/radiative-density-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='ekll',role='designation',forms=[dict(text='Relativitätsprinzip',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
