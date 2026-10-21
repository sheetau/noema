"""Integrate the general law criterion, self-imposition question and its presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_law_enactment import NAMES,FIELDS,ARGS

PARENT='examples/v016/kant-posterity-rights.noema'
PARENT_BASIS='data/posterity-rights-basis-v1.json'
DEPENDENCIES=('data/law-enactment-basis-v1.json','data/rational-self-imposition-basis-v1.json')
FULL='examples/v016/kant-legislative-touchstone.noema'
CORE='examples/v016/legislative-touchstone-core.noema'
BASIS='data/legislative-touchstone-basis-v1.json'
ANNOTATIONS='data/legislative-touchstone-identifiers-v1.json'
REF='k h26b7[]';CTX='k h255n[]'
FOUR_NAMES=('actor',*NAMES)
FOUR='l[a][v actor '+ARGS+']'
PROPERTY='i b[h[j[a]] e]';QUESTION='i b[h[j[a]] f]'
PRIMITIVES={
 'h26ci':('[] a',[],'同じ政治的共同体の人民に公的な法を定める主体としての立場。個人または集団の主体を扱い、現行制度の現職や特定の君主へ限定しない。誰が何を採択し得るか、その資格と実行は別に構成する。人民自身の立場h26chとの型の類似だけで資格を同一化しない。'),
 'h26cj':('[] a',[],'公的な法を人民に定めることの正当な資格を評価する規範の出所。h26cgと同じ理性的な公的規律という観点で、採択主体一般について扱う。実際の権力者による承認や現行法の有効性だけとは区別する。どの採択を許容するかは同じ内容と対象列を持つh245c/h237zで与え、自己賦課の可能性との対応は本文の基準命題で別に述べる。'),
 'h26ck':('[a a a i d[e] '+PROPERTY+' '+PROPERTY+' '+QUESTION+' d] c',['node','author','question_node','whole','scope','assessed_property','question','context'],'著者が同じ全体内容の中で、指定の範囲の同じ順序の対象列について、その性質の判定基準を、指定した質問箇所に提示する同じ問いの肯否を確かめることに置くと述べる。問いの全内容と性質の対応は全体内で別に構成する。単なる話題の一致や一般的な疑問の表明と区別し、特定の対象への肯定回答、質問の実行、客観的な判定の正しさを含意しない。'),
 'h26cl':('[a a a '+PROPERTY+' '+QUESTION+' d] c',['node','author','question_node','scope','question','context'],'著者が指定した範囲・質問箇所の同じ問いを、その肯定がはたして成り立ち得るかと思案・吟味を促す調子で提示する。確定した回答や単なる肯定断言と区別する。数値確率、必ず否定されるという含意、著者の伝記的な迷い、読者が実際に熟考したことは追加せず、問いの対象や条件は変えない。'),
 'h26cm':('[a a i d[e] i[h[a] e] d] c',['node','author','criterion','testing_instrument_kind','context'],'著者が記述された判定基準を、別に記述した物的な検査道具の働きに見立てて提示する。対象の適否を見分ける役目を対応させ、物的道具が実在して用いられたこと、基準と道具の物理的同一性、検査や基準の無謬性を断言しない。両記述の内容自体は別に構成する。'),
 'h26cn':('[a d] c',['instrument','point'],'この物は石材の表面に金・銀等の試料を擦って残した跡から、その金属の品質を見分けるために用いる道具の種類に属する。具体的な鉱物種・純度数値・特定の検査実施や成功を要求しない。比喩の描写側に使っても、その道具の現実の存在を補わない。'),
 'h26co':('[] a',[],'kant-1784:u0013[1265,1436)のDer Probiersteinからauferlegen könnte?までの第六文全体。'),
 'h26cp':('[] a',[],'同じ第六文で、Der Probiersteinからliegt in der Frageまで、全立法内容の判定基準を問いに置く箇所。'),
 'h26cq':('[] a',[],'同じ第六文のob ein Volkからauferlegen könnte?までの間接疑問。'),
 'h26cr':('[] a',[],'同じ第六文のwohlによる思案的な問いの提示箇所。'),
}
MEANINGS={
 'r5ev':'採択主体・人民・共同体・法の正確な四対象列と基準を、同じ候補内のr5elの公的採択へ束縛する。主体を人民へ固定せず、自己賦課の三対象r5enと区別する。全条項を評価するため段階1で引用する。',
 'r5ew':'同じ主体・人民・共同体・法と固定基準h26b7のr5evへ、一般の公的立法の規範h26cjと立場h26ciから、同じ候補でr37cの衝突のない積極的許可がある。採択の実行は引用から要求しない。',
 'r5ex':'同じr5epの仮定経過において、ある主体が同じ人民へ同じ法を採択するr5elと、その同じ主体のr5ewの資格がともに成立する候補がある。受動形beschlossen werden kannの採択主体を存在量化し、実在の君主・現職・現実の採択へ限定しない。',
 'r5ey':'同じ人民・共同体・法の正確な三対象列にr5exの立法として採択し得る内容を対応させる。問いr5euの同じ三対象と比較する対象性質。',
 'r5ez':'同じ三対象列が固定基準h26b7でr5eiの完全な人民と非空の公的法案の枠組みを満たす範囲。許容された法や成功する候補だけへ範囲を制限しない。',
 'r5e2':'全ての人民・共同体・法について、r5eiの枠組みなら、その法を人民に公的に採択し得るr5exと、同じ人民が自らに課し得るr5esが同値であるという基準命題。肯否を判定する完全な試金石という採用読解。任意の特定主体の資格や実際の全法律の正当性は述べない。',
 'r5e3':'同じ物が金属試料の跡により品質を検査する石の道具h26cnに属するという描写側の性質。基準を述べる本文から実際の石や金属の存在を導かない。',
 'r5e4':'第六文の基準命題r5e2を同じ著者・文脈へ帰属し、その基準を同じ範囲r5ez・判定対象r5ey・自己賦課の問いr5euへ結ぶ。試金石の道具への見立て、wohlの思案的提示、前文からの順序を保持する。引用した世界内容や問いへの回答を実行しない。',
}
LIMITS=[
 'u0013[1265,1436)の144非空白文字。ein Volkは任意の政治的共同体の全成員という一般化であり、二度目も同じ人民、ein solches Gesetzも同じ全条項を持つ法案へ束縛する。直前の特定の契約だけへ対象を限定しない。',
 'beschlossen werden kannは公的な法として正当に採択し得ること、könnteは同じ人民による自己賦課が規範的に許容される仮定を置き得ることと読む。後者の構成はrational-self-impositionの明示読解を保持する。現在の制度的権能、現実の投票、物理的強制の可能性だけでは代用しない。',
 'Probiersteinとliegt in der Frageを、全対象の肯否を判定する基準という読みで形式化し、許容と自己賦課可能性の同値を要求する。必要条件だけの旧rkeへ弱めない。これは採用した明示読解であり、語だけから論理的に唯一の形式が導かれるとの主張ではない。後続の不許可例は必要方向を示し、暫定的な秩序の可能性の検討は肯定側を含む。1793年の比較資料を十分方向の唯一の根拠にはしない。',
 '基準は法の内容の許容性についてであり、どの人物でも同じ法を採択してよいという全員への権限付与ではない。主体一般の許容と人民自身の許容を別に構成し、同値を定義上の恒真へ潰さない。範囲が空なら普遍命題は真だが、法の実在や問への肯定回答は導かない。',
 'Probiersteinの品質を調べる道具への慣用的な見立ては、別の道具性質と提示関係で残す。石・金属・検査の現実の存在は主張しない。liegtは判定根拠の所在であり、物理的な位置や運動を追加しない。',
 'wohlは同じ可能性がはたして成り立つかと吟味を促す疑問の調子として読む。推量・疑問を伴う歴史的用法を参考にし、必ず肯定・否定される問い、数値確率、著者の心理状態の伝記的事実にはしない。原刊の疑問符を保持し、AA版の句点と区別する。',
 '問いは範囲内の任意の同じ三対象へ適用する閉じた質問族として帰属する。Noemaの引用内の問いの構成は、読者への現実の返答要求や全候補への肯定回答を意味しない。基準が妥当であるとの著者の主張を記述し、客観的真理を証明するものではない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
NODES=('h26bx','h26co','h26cp','h26cq','h26cr')
def definitions():
    text='d r5ev[bindings j[a] reference d] e[b candidate['+bind(FOUR_NAMES,'k r5el[v actor '+ARGS+' v reference v candidate]')+']].\n'
    text+='d r5ew[actor a '+FIELDS+' candidate d] c[k r37c[k h26cj[] v actor k h26ci[] r b[p r5ev] '+FOUR+' '+REF+' v candidate]].\n'
    text+='d r5ex['+FIELDS+'] c[g candidate d[g actor a['+both('k r5ep['+ARGS+' v candidate]','k r5ew[v actor '+ARGS+' v candidate]',
        'k r5el[v actor '+ARGS+' '+REF+' v candidate]')+']]].\n'
    for root,body in (('r5ey','k r5ex['+ARGS+']'),('r5ez','k r5ei['+ARGS+' '+REF+']')):
        text+='d '+root+'[bindings j[a]] e[b point['+bind(NAMES,body)+']].\n'
    criterion='y[k r5ei['+ARGS+' '+REF+']][z[k r5ex['+ARGS+']][k r5es['+ARGS+']]]'
    for n in reversed(NAMES):criterion='f '+n+' a['+criterion+']'
    text+='d r5e2[] e[b point['+criterion+']].\n'
    text+='d r5e3[instrument a] e[b point[k h26cn[v instrument v point]]].\n'
    author='k wa[]';whole='r d[k r5e2[]]';scope='r b[p r5ez]';question='r b[p r5eu]'
    clauses=['k h236i[k h26co[] '+author+' '+whole+' '+CTX+']',
        'k h26ck[k h26cp[] '+author+' k h26cq[] '+whole+' '+scope+' r b[p r5ey] '+question+' '+CTX+']',
        'k h26cl[k h26cr[] '+author+' k h26cq[] '+scope+' '+question+' '+CTX+']',
        'k h26cm[k h26cp[] '+author+' '+whole+' r[p r5e3] '+CTX+']']
    clauses+=['k ue[k '+a+'[] k '+b+'[] '+CTX+']' for a,b in (('h26bx','h26co'),('h26cp','h26cq'))]
    clauses+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(NODES) for b in NODES[i+1:]]
    text+='d r5e4[] c['+both(*clauses)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5e4',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='legislative_touchstone_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/posterity-rights-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
