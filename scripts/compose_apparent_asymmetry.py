"""Compose the general opening claim with a nonfactive appearance qualification."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_conductor_case import ROOT,read
from scripts.compose_observable_contrast import RULE
from scripts.compose_material_body_motion import FIELDS as MOTION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-moving-conductor-case.noema';PARENT_BASIS='data/moving-conductor-case-basis-v1.json'
FULL='examples/v014/einstein-apparent-asymmetry.noema';CORE='examples/v014/apparent-asymmetry-core.noema'
BASIS='data/apparent-asymmetry-basis-v1.json';ANNOTATIONS='data/apparent-asymmetry-identifiers-v1.json';INDEX=211
COMPARISON=RULE[1:-1]
CODE='i[h['+' '.join(t for _,t in COMPARISON)+'] e]'
MOTION_CODE='i[h['+' '.join(t for _,t in MOTION)+'] c]'
APPEARANCE=COMPARISON+[('reference','d')]
FIELDS=RULE+[('theory','a'),('document','a')]
APPLICATION=FIELDS+[('motion',MOTION_CODE)]
CANDIDATES=COMPARISON+[('content',CODE),('reference','d'),('candidate','d')]
PRIMITIVES={
 'eisax':([], 'この論説がMaxwellの電気力学として指す歴史的な理論への参照。電荷と電流を源とする電気側・磁気側の場の時間空間的な関係、および場と物質の作用を法則で扱う理論体系である。電気側と磁気側の量・作用は既存eibs/eicoの基礎規約と同じ区別で読む。固有名による理論の識別であり、全法則を処理系が実証済みであることや、ここで通常の理解として取り上げる見解そのものと同一であることは含意しない。'),
 'eisay':([('theory','a'),('view','a'),('document','a'),('reference','d')],'指定論説の記述時点・論点においてviewがtheoryをどう理解し、どの説明をその適用として認めるかという解釈上の関係。理論の歴史的同一性と、その理論を解釈し適用する仕方を分ける。通常性はeisahで別に要求し、現代の理解や著者の最終的見解へ自動的に替えない。'),
 'eisaz':(APPLICATION,'指定論説・理解viewの下でtheoryを動く物体へ適用する、このscopeに属する二つの比較事例。各事例は指定系・状況の同じ物理的準備・対象対応・尺度を保ち、基準系に対してどの物体が動く側として扱われるかを比べる。運動は渡された閉じたmotion型の全物質点・全区間履歴に従い、事例名だけや未知の履歴を運動と認めない。磁石・導体に限らない一般の適用である。viewとscopeと二場合についてeisafが与える許容説明の範囲は、この理論の解釈・適用から認める説明全体であり、無関係な二記録や都合のよい説明の抜粋ではない。説明が異なること、観測差、観測差がないように見えることは、この適用関係へ先取りしない。'),
 'eisa2':(APPEARANCE,'同じscope・対象対応・準備・尺度の二事例で、どちらが動く側として扱われるかという区別が、観測可能な物理的現象自体の区別として現れる。場の説明機構の名前や理論の分類とは別に、同じ単位・手順で識別できる物理的効果の差として扱う。参照点referenceはこの差を評価する見方・状況であり、原文の現実的な判断点と見かけの候補点を区別する。電流だけに限定した語義ではなく、その比較の現象の範囲をscopeで固定する。観測差が未確認であることから不存在と認定しない。'),
 'eisa3':(CANDIDATES,'同じ比較のcontentがどう見えるかを、referenceで利用できる観察・説明上の情報に沿って評価する候補candidateの全範囲。閉じたcontent型へ同じscope・二系・二状況を渡して評価し、候補を替える際に比較対象を都合よく交換しない。現実の真理、全論理的可能性、確信済みの信念、内容が真になる候補だけを選んだ集合とは区別する。候補の非空性と同じ内容が全候補で成立することは合成で要求する。見方を担う特定の人や数値確率を原文へ補わない。'),
 'eisa4':([('document','a'),('content','i[e]'),('reference','d')],'指定論説の論点と記述時点で、この閉じたcontentが関係する知識共同体に既に知られた事柄として扱われるという周知性の帰属。全人類の同意、ある一人だけの信念、現代の常識、証明済みという検査結果へ置き換えない。語としての知識には真と認める扱いがあるが、その内容を著者が述べることと処理系による客観的真理の認定は別である。contentそのものを主張する部分は合成で保持する。'),
 'eisa5':([('node','a'),('author','a'),('target','i[e]'),('qualification','i[e]'),('reference','d')],'著者がこの箇所でtargetを述べる際に、qualificationを挿入的な補足として提示し、対象がどの理解・条件の下で述べられるかを限定する。補足を削除した主張や、独立した別の論点へ替えない。内容の引用をこの談話帰属の評価時に実行せず、読み手が既に承認済みであることを要求しない。'),
}
MEANINGS={
 'eieu':'同じ一般比較の二事例について、現象自体にeisa2の区別がないという否定内容。実際の成立と、見かけの候補での成立を区別できる内容として構成する。',
 'eiev':'同じ比較と閉じたeieu型に対するeisa3の候補が少なくとも一つあり、その全候補で同じ否定内容が成立する。現実のreferenceでも否定が真であるとは要求せず、見かけが必ず誤りだとも要求しない。',
 'eiew':'同じ理論・通常の理解による動く物体への適用eisazが、eiddの許容説明すべてでの分類の区別を持ち、その同じ比較の現象自体には区別がないように見えるeievを結ぶ。説明の区別と観測差を混同しない。',
 'eiex':'指定理論・理解・論説についてeiewを満たす比較範囲・二系・二状況が存在するという内容。asymmetriesを適用上生じる区別の存在として読む。全適用が非対称、例が唯一、又は少なくとも二つの独立実験が必要とは加えない。',
 'eiey':'同じ論説の通常の理解eisahと、その理解がMaxwellの電気力学eisaxを解釈するeisayを結ぶ挿入部の内容。gegenwärtigは論説記述時点であり現在の読者の時点ではない。',
 'eiez':'eieyで限定した同じ理論・通常の理解についてeiexの適用上の非対称性と見かけの留保を述べる閉じた内容。後続の磁石・導体だけへ一般論の対象を縮めない。',
 'eie2':'eiezの内容を述べ、かつそれがこの論説の論点で既に知られた事柄として扱われるeisa4を結ぶ。周知性のラベルだけで内容を省かず、見かけの留保を取り除いた命題を周知としない。',
 'eie3':'eie2を主張の力で提示するメッセージ。単なる問いや著者の推測の報告へ替えない。',
 'eie4':'既存eir7が指していた冒頭箇所にeie3の著者・論説への帰属を追加し、同じeieyを挿入補足として保持する。後続の例示eir6との順序を保ち、先行箇所の内容を新しい別箇所へ付け替えない。',
}
LIMITS=[
 '一般の動く物体への理論適用の非対称性として読む。後続の一例の全物理設定を、この一般文の量化範囲全体へ代入しない。',
 '非対称性は二事例で許容する説明機構を区別する扱いと読む。観測差との不一致を、同じ事例・尺度を保つ否定内容と見かけの候補で表す。任意のあらゆる数学的非対称性の辞書的定義ではない。',
 'scheinenは同じ否定内容が非空の見かけの全候補で成立することとして読む。現実の不変性の証明、単なる未確認、確信度の数値化、特定人物の心理状態を追加しない。',
 'ist bekanntはこの論点での周知性を述べる提示として読み、その内容自体も保持する。原著者の主張の経験的真理を翻訳時に証明したとはしない。',
 'この一文の確認後にも、五文の対象・作用範囲・談話の接続を通して確認してから段落全体の判断を行う。',
]

def candidates(candidate):return k('eisa3',*args(COMPARISON),'r[p eieu]',v('reference'),candidate)
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+='d eieu['+' '.join(n+' '+t for n,t in COMPARISON)+'] e[b point['+op('u',k('eisa2',*args(COMPARISON),v('point')))+']].\n'
    text+=define('eiev',APPEARANCE,both(q('g','candidate','d',candidates(v('candidate'))),q('f','candidate','d',op('y',candidates(v('candidate')),'t['+k('eieu',*args(COMPARISON))+'][v candidate]'))))
    text+=define('eiew',FIELDS,both(k('eisaz',*args(FIELDS),'r[p eiag]'),k('eidd',*args(RULE)),k('eiev',*args(APPEARANCE))))
    content=k('eiew',*[v('point' if n=='reference' else n) for n,_ in FIELDS])
    for n,t in reversed(COMPARISON):content=q('g',n,t,content)
    text+='d eiex[theory a view a document a] e[b point['+content+']].\n'
    text+='d eiey[] e[b point['+both(k('eisah',k('eisak'),k('eirf'),v('point')),k('eisay',k('eisax'),k('eisak'),k('eirf'),v('point')))+']].\n'
    text+='d eiez[] e[b point['+both('t[k eiey[]][v point]','t[k eiex[k eisax[] k eisak[] k eirf[]]][v point]')+']].\n'
    text+='d eie2[] e[b point['+both('t[k eiez[]][v point]',k('eisa4',k('eirf'),'r[k eiez[]]',v('point')))+']].\n'
    text+='d eie3[] f[j s[k eie2[]]].\n'
    text+=define('eie4',[],both(k('eir3',k('eir7'),k('rd'),k('eirf'),'r[k eie3[]]',k('ri')),k('eisa5',k('eir7'),k('rd'),'r[k eiez[]]','r[k eiey[]]',k('ri')),k('ue',k('eir7'),k('eir6'),k('ri')),op('u',op('e',k('eir7'),k('eir6')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eie4',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='general_application_asymmetry_with_appearance_and_knownness',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/moving-conductor-case-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Opening asymmetry claim appended')
