"""State scoped current invariance and distinguish it from an attributed account rule."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_interaction_example import ROOT,read,SCHEMA
from scripts.compose_magnet_source import FIELDS as CASE_FIELDS,CASES,case_args
from scripts.compose_conductor_cases import CAPABILITIES,PREPARATION,conclusion
from scripts.compose_relative_history_match import FIELDS as MOTION,history
from scripts.compose_current_distribution import PAIR as CURRENT,HISTORY
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-interaction-example.noema'
PARENT_BASIS='data/interaction-example-basis-v1.json'
FULL='examples/v014/einstein-observable-contrast.noema'
CORE='examples/v014/observable-contrast-core.noema'
BASIS='data/observable-contrast-basis-v1.json'
ANNOTATIONS='data/observable-contrast-identifiers-v1.json'
INDEX=208
FIELDS=CASE_FIELDS+[('process','a'),('reference','d')]
RULE=[('view','a'),('scope','a'),('firstframe','a'),('firstcontext','d'),('secondframe','a'),('secondcontext','d'),('reference','d')]
ELIGIBILITY=[('scope','a'),('process','a'),('left','a'),('right','a'),('firstframe','a'),('firstcontext','d'),('secondframe','a'),('secondcontext','d'),('reference','d')]
OBSERVABLE=[('process','a')]+HISTORY
PRIMITIVES={
 'eisad':(ELIGIBILITY,'同じ例の設定processと二物体について、この二つの系・状況が指定比較範囲の許容される比較に属する。referenceで採る記述尺度、配置・回路・外部準備と対象とする現象の範囲を固定し、観測済みの標本や結果の一致した組だけを範囲にしない。相対履歴、物体の種類、準備の具体的対応、電流の妥当性や一致は合成で別に要求する。第一・第二の呼称だけや、片方のみが静止する組に範囲を限定しない。'),
 'eisae':(OBSERVABLE,'この例の設定で、指定物体・系・状況・単位・区間・全有向断面の累積輸送量と電流履歴が、対象とする観測可能な電流現象の記録である。電荷輸送とその物理的作用を校正した測定へ接続して大きさ・符号・経過を識別できる量として読む。実際に誰かが測定済みであること、全空間の全物理量を観測したこと、用いた理論的説明の一意性は含意しない。原文のこの現象は後続の電流の大きさと経過を受ける読みとし、場の説明の同一性とは分ける。数値関数だけや測定不能の隠れたラベルを観測結果と認定しない。'),
 'eisaf':(RULE[:-1]+[('account','a'),('reference','d')],'このviewの理解・説明規則の下で、指定範囲と二つの系・状況の事例を説明する完全なaccountが許容される。規則上の許容であり、著者による承認、説明の物理的真理、説明の実際の発話を意味しない。分類を欠く説明や結果を見て都合よく選んだ説明だけへ量化範囲を縮めない。'),
 'eisag':([('view','a'),('scope','a'),('account','a'),('frame','a'),('context','d'),('category','a'),('reference','d')],'同じ理解・比較範囲の指定説明accountが、指定系・状況の事例に与える電磁的な生成・説明機構の分類category。分類は電流の数値や単なる事例名ではなく、場による電気的作用と導体中の起電力などをどの仕方で説明するかという同じ観点での扱いを指す。全てが電磁現象であるといった別の粗い観点の分類へ替えない。分類の排他性と、全許容説明で区別する制約は合成側で要求する。'),
 'eisah':([('view','a'),('document','a'),('reference','d')],'このviewが、指定論説の記述時点・論点における通常の理論理解として取り上げられる。著者本人の最終的な立場、現在の読者の理解、全員一致や数値的な支持率とは区別する。本文のnach der üblichen Auffassungの出所を固定するための慣用的な見解への帰属である。'),
 'eisai':([('view','a'),('content','i[e]'),('reference','d')],'指定viewの理解の下では、閉じたcontentに記述する主張又は説明上の制約が採られるという非事実的な見解帰属。contentをこの関係の評価時に実行せず、その内容の客観的真理、著者自身の承認、現実の事例の成立を含意しない。'),
 'eisaj':([], '固定原文einstein-1905:u0003[308,549)の、観測可能な現象の相対運動への依存と通常の理解による二場合の区別を対照する一文の箇所。'),
 'eisak':([], 'この導入で著者が通常の理解として取り上げる見解。Maxwellの理論そのもの、著者の最終見解、現代の理解と同一視せず、通常性の帰属はeisahで別に要求する。'),
}
MEANINGS={
 'eida':'同じ例と二物体の許容比較範囲eisadに、両場合の磁石eics・導体eicj、準備条件eirs、全電流履歴の妥当性eibg、同じ源の場を使う相互作用eirzと観測可能な電流記録eisaeを結ぶ。相対履歴一致・電流一致・運動静止の入れ替えはこの前提へ混入しない。',
 'eidb':'eidaの妥当な比較について、一般の相対配置履歴eia2が同じなら全断面電流履歴eibiも同じであるという条件。相対静止、両物体が動く場合も排除せず、入れ替えた運動静止の二場合だけに限定しない。逆方向の含意は加えず、異なる相対運動が同じ電流を生むことも許す。',
 'eidc':'同じ二物体と例について、全ての系・状況・単位・履歴・準備・場・基準の候補にeidbを要求する内容。妥当な比較だけに条件を適用し、選んだ一組の一致や観測済み標本を全範囲としない。相対運動だけへの依存を、この比較範囲で同じ入力なら同じ観測結果という意味に読む。',
 'eidd':'同じ理解が二場合に対して許容する説明が少なくとも一つ存在し、その全てで各場合に機構の分類があり、両場合に共通の分類が一つもないという説明上の区別規則。一つの説明だけで違えばよいとはせず、単なる事例名の不等値や観測値の違いに替えない。',
 'eide':'eidaの同じ例の妥当な二場合が、第一では左側運動・右側静止、第二では左側静止・右側運動という役割を持つならeiddの厳密な説明上の区別を要求する条件。相対履歴や電流の一致をこの前件へ要求しない。',
 'eidf':'同じ二物体・例・理解について、全候補の妥当な二場合にeideを要求する内容。物理的な事例の違いだけでなく、その理解の許容する説明全体に課す区別を保持する。',
 'eidg':'前文の同じ磁石側eisaa・導体側eisab・例eisacへeidcを適用した、観測可能な現象の相対運動への依存という閉じた内容。',
 'eidh':'同じ二物体・例と、通常の理解として指すeisakへeidfを適用した閉じた内容。引用される理解の制約であり、著者の無条件の物理的承認ではない。',
 'eidi':'この論説での通常の理解であるeisahと、その同じ理解の下でeidhの内容が採られるeisaiを結ぶ内容。引用される説明規則の真理をその場で評価しない。',
 'eidj':'観測現象の依存eidgと、通常の理解では二場合を区別するという見解帰属eidiを同じ評価点に結ぶ。観測結果の一致から説明の一致を導かず、説明の違いから観測結果の違いも導かない。',
 'eidk':'eidjを主張の力で提示するメッセージ。前文の例を考える指示とは発話の力を区別する。',
 'eidl':'著者が同じ論説でeidkを提示し、währendの二側eidg/eidiを同じ例の範囲で対照すること、前文からの順序を結ぶ。本文208へ追加する一文の帰属であり、引用内容を処理系が物理的に証明したとはしない。',
}
LIMITS=[
 'Das beobachtbare Phänomenは、この磁石・導体の例で後続が比較する電流の大きさと経過を中心とする現象として読む。あらゆる観測量、全ての配置・回路・材料条件への無条件な同値ではない。',
 'nurは妥当な比較範囲での機能的依存として読む。逆の含意、異なる相対運動なら必ず異なる電流、運動を変える因果的介入の完遂、現実の測定済みは加えない。原文の主張の経験的真理を翻訳時に証明しない。',
 '比較の相対履歴には既存eia2の同じ物質点、剛な左側参照配置、正方向、同じ単位と経過時間対応を引き継ぐ。原文の例示範囲でこのマクロな読みを採り、任意の加速・変形の全物理学へ拡張しない。',
 'streng voneinander zu trennen sindは、通常の理解の下で許容する説明が二場合を同じ機構分類へまとめないという規則として読む。全許容説明の分類の非空性と共通分類の不存在を要求するが、その理解の物理的正しさは承認しない。',
 '通常の理解の具体的な電場・起電力・エネルギーの説明は後二文でさらに記述する。今回の分類規則はその説明を省略して完了とするものではなく、対照文で述べる区別の役割を保持する。',
]

def current_args():return [v('right' if n=='body' else n) for n,_ in CURRENT]
def observed_args(case):
    shared={'body':'right','timeunit':'timeunit','quantityunit':'quantityunit','sections':'sections'}
    return [v('process')]+[v(shared.get(n,case+n)) for n,_ in HISTORY]
def allowed(account):return k('eisaf',*args(RULE[:-1]),account,v('reference'))
def category(account,case,label):return k('eisag',v('view'),v('scope'),account,v(case+'frame'),v(case+'context'),label,v('reference'))
def quantified(symbol,view=False):
    selected=[v('point' if n=='reference' else n) for n,_ in FIELDS]+([v('view')] if view else [])
    content=k(symbol,*selected)
    for n,t in reversed(FIELDS):
        if n not in ('left','right','process','reference'):content=q('f',n,t,content)
    return content

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fields)+'] '+('a' if not fields else 'c')+'.\n' for n,(fields,_) in PRIMITIVES.items())
    text+=define('eida',FIELDS,both(k('eisad',*args(ELIGIBILITY)),k('eicj',*args(CAPABILITIES)),k('eics',*args(CASES)),
        k('eirs',*args(PREPARATION)),k('eibg',*current_args()),
        *(k('eirz',v('process'),v('right'),*case_args(case),'r[p eicw]') for case in ('first','second')),
        *(k('eisae',*observed_args(case)) for case in ('first','second'))))
    text+=define('eidb',FIELDS,op('y',both(k('eida',*args(FIELDS)),k('eia2',*args(MOTION))),conclusion()))
    text+='d eidc[left a right a process a] e[b point['+quantified('eidb')+']].\n'
    populated=both(*(q('g',case+'label','a',category(v('account'),case,v(case+'label'))) for case in ('first','second')))
    disjoint=q('f','label','a',op('u',both(category(v('account'),'first',v('label')),category(v('account'),'second',v('label')))))
    text+=define('eidd',RULE,both(q('g','account','a',allowed(v('account'))),q('f','account','a',op('y',allowed(v('account')),both(populated,disjoint)))))
    roles=both(k('eiag',*history('first','left')),k('eiah',*history('first','right')),k('eiah',*history('second','left')),k('eiag',*history('second','right')))
    text+=define('eide',FIELDS+[('view','a')],op('y',both(k('eida',*args(FIELDS)),roles),k('eidd',*args(RULE))))
    text+='d eidf[left a right a process a view a] e[b point['+quantified('eide',True)+']].\n'
    text+='d eidg[] e[k eidc[k eisaa[] k eisab[] k eisac[]]].\n'
    text+='d eidh[] e[k eidf[k eisaa[] k eisab[] k eisac[] k eisak[]]].\n'
    text+='d eidi[] e[b point['+both(k('eisah',k('eisak'),k('eirf'),v('point')),k('eisai',k('eisak'),'r[k eidh[]]',v('point')))+']].\n'
    text+='d eidj[] e[b point['+both('t[k eidg[]][v point]','t[k eidi[]][v point]')+']].\n'
    text+='d eidk[] f[j s[k eidj[]]].\n'
    text+=define('eidl',[],both(k('eir3',k('eisaj'),k('rd'),k('eirf'),'r[k eidk[]]',k('ri')),
        k('zbc',k('eisaj'),k('rd'),'r[k eidg[]]','r[k eidi[]]',k('eisac'),k('ri')),
        k('ue',k('eir6'),k('eisaj'),k('ri')),op('u',op('e',k('eir6'),k('eisaj')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eidl',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='observable_dependence_and_usual_account_contrast',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/interaction-example-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Observable dependence and attributed account contrast appended')
