"""Integrate retrospective emphasis, two reasons, explanation and anaphora."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_prince_sentence import ANCHOR,CURRENT,TOPIC

PARENT='examples/v016/kant-self-departure-sentence.noema';PARENT_BASIS='data/self-departure-sentence-basis-v1.json'
DEPENDENCIES=('data/topical-guardian-interest-basis-v1.json','data/retrospective-emphasis-basis-v1.json','data/immaturity-comparison-basis-v1.json')
FULL='examples/v016/kant-religious-emphasis-sentence.noema';CORE='examples/v016/religious-emphasis-sentence-core.noema'
BASIS='data/religious-emphasis-sentence-basis-v1.json';ANNOTATIONS='data/religious-emphasis-sentence-identifiers-v1.json'
AUTHOR='k wa[]';WORK='k h26sk[]';REF='k h26sl[]';ARTS='k h26sm[]';SCIENCES='k h26sn[]';CTX='k h26sq[]'
C3='i d[e]';PROPERTY='i[h[a] e]';STATE='i b[h[a] e]'
PRIMITIVES={
 'h26sk':('[] a',[],'Ich habe ... gesetztの著者が振り返る同じ啓蒙論の論述作品。別の作品や現実の啓蒙過程を指さない。'),
 'h26sl':('[] d',[],'第九段落第一文の回顧、統治者と全臣民、論述主題、能力・自己帰責、有害さと不名誉の比較を固定する解釈基準。結果で範囲を選び直さず、本文現在h26kn(h26km)や提示文脈とは区別する。'),
 'h26sm':('[] a',[],'同じ第一文のKünsteが指す技芸の領域。美術だけに狭めず、意味はh26r5で別に確認する。'),
 'h26sn':('[] a',[],'同じ第一文のWissenschaftenが指す学問の領域。自然科学だけに狭めず、意味はh26r6で別に確認する。技芸との事項の重なりを排除しない。'),
 'h26so':('[a a a a d d] c',['author','public','ruler','community','reference','point'],
   '同じ著者と同時代の読者を含む公衆にとって、指定の統治者・政治的共同体が、われわれに関わる統治者として言及する全関連範囲に入る。本文現在と固定基準を共用し、好意的・啓蒙的・無関心な統治者だけに選別しない。著者一人の直接の支配者だけや全時代の全統治者へ替えない。君主的統治の役職と臣民の過不足ない範囲は合成側で確認する。範囲の完全性は解釈入力であり、有限試験の個体数を原文の王の人数としない。'),
 'h26sp':('[a a d] a',['ruler','community','reference'],
   '同じ統治者・政治的共同体・固定基準の全臣民を指す集団。実際に後見される者や関心対象だけを選ばず、r6boで同じ全臣民との過不足ない一致を別に検査する。'),
 'h26sq':('[] d',[],'固定原文kant-1784:u0016第一文の著者の提示文脈。前段落の提示文脈、内容の固定基準、本文現在と役割を分ける。'),
 'h26sr':('[a a '+C3+' '+C3+' '+C3+' d] c',['node','author','whole','baseline','addition','context'],
   '著者が同じ全体で第一内容を維持し、それにもう一つの内容を追加して提示する。内容の真偽、論理的含意、時間的な後発、第一の撤回、追加内容だけへの限定を含意しない。理由として追加する場合、その同じ説明先への理由関係は別に構成する。'),
 'h26ss':('[a a '+C3+' '+C3+' '+C3+' d] c',['node','author','whole','first','second','context'],
   '著者が同じ全体における二つの述定を、一方と同様に他方も成立するとする並列の提示として結ぶ。それぞれの内容を保ち、程度の数値的一致、同義性、一方から他方の導出、二者択一又は時間的順序を追加しない。引用の真理は実行しない。'),
 'h26st':('[a a a a '+PROPERTY+' '+PROPERTY+' d] c',['node','author','term_node','expansion_node','term','expansion','context'],
   '著者が第一箇所で挙げた概念を、第二箇所の同じ型の性質記述で説明し展開して提示する。概念と展開は閉じた記述で指定し、原語の綴りだけを意味にしない。説明の合致は合成側で確認し、この関係から概念の実例の現実の成立を導かない。'),
 'h26su':('[a a a '+PROPERTY+' '+STATE+' a d d] c',['mention','author','antecedent_node','general','specialized','topic','reference','context'],
   '著者が指定表現で、先行箇所の一般的な人物状態を同じ主題に具体化した閉じた状態記述として受ける。本人の能力と自己帰責という構成の継承は各定義で保持する。一般状態と主題別状態の無条件の同値、別主題、現実の全員の状態成立を含意しない。'),
}
NODE_INFO={
 'h26sv':([0,389],'第一文全体。'),
 'h26sw':([28,38],'Aufklärungの概念。'),
 'h26sx':([40,114],'啓蒙を自己に帰責される未成熟からの離脱として説明する句。'),
 'h26sy':([155,159],'weilの第一理由提示。'),
 'h26sz':([289,301],'überdem auchの追加理由提示。'),
 'h26s2':([302,319],'jene Unmündigkeitの宗教的未成熟への照応。'),
 'h26s3':([321,344],'so wie die schädlichsteの並列の第一側。'),
 'h26s4':([346,372],'also auch die entehrendsteの並列の第二側。'),
 'h26s5':([75,114],'照応元の自己に帰責される未成熟。'),
 'h26s6':([0,154],'宗教事項へ重点を置いたという回顧の主節。'),
 'h26s7':([155,287],'技芸・学問での後見への関心の不在という第一理由。'),
 'h26ta':([289,389],'宗教的未成熟の有害さと不名誉という第二理由。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0016['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
MEANINGS={
 'r6ca':'biの啓蒙過程を展開した同じ性質。ある同じ人が自己に帰責される未成熟から自立的行使能力へ移るbeを、過程・前後点へ結ぶ。Menschenはこの人間一般の概念であり、全員の同時の現実の離脱を量化しない。',
 'r6cb':'同じ著者を含む非空の人間公衆に関する全統治者・共同体の非空の範囲h26soについて、それぞれの同じ全臣民をr6bpへ渡し、技芸と学問の双方の後見への無関心を要求する。無関心な統治者だけを範囲として定義しない。',
 'r6cc':'同じ本文著者・作品・宗教主題・固定基準・現在点をr6btへ渡す回顧の閉じた内容。過去の設定活動と現在の論述上の重点を保持する。',
 'r6cd':'同じ著者・当時の公衆・技芸・学問・固定基準・本文現在のr6cbを第一理由の閉じた内容とする。外側の評価点で本文現在を動かさない。',
 'r6ce':'同じ宗教主題・公衆・固定基準の自己帰責される主題別未成熟が、有害さにおいて最大で有害な性質を持つ内容。',
 'r6cf':'同じ宗教主題・公衆・固定基準の同じ状態が、不名誉において最大でその性質を持つ内容。有害さからは導かない。',
 'r6cg':'同じ宗教主題についての有害さr6ceと不名誉r6cfの両内容を第二理由として結ぶ。両方とも同じ状態・人々・基準を保つ。',
 'r6ch':'回顧r6cc・第一理由r6cd・第二理由r6cgを同じ評価点の連言として保つ全文。理由という提示は別に構成し、因果的な証明や理由から回顧への含意に置換しない。',
 'r6ci':'第一文の同じ宗教主題と固定基準に閉じたr6bzの状態記述。jeneの照応と二比較が扱う同じ自己帰責される主題別未成熟を固定する。',
 'r6cj':'第一文全文を著者に帰属し、啓蒙の離脱句による説明、宗教的未成熟への照応、同じ主節に対する二理由、追加と両最上級の並列、前段落からの本文順序と各箇所の区別を結ぶ。引用された現実内容を実行しない。',
}
LIMITS=[
 '固定原文u0016第一文[0,389)・336非空白文字を対象とする。Ichは同じ本文著者wa、この論述作品h26skを振り返る現在完了として読み、過去の設定と現在の重点を保つ。最大の重点は同順位を許し、唯一の主題、実際の啓蒙達成、全中間時点の維持を追加しない。',
 'die des Ausgangesは原刊と固定転記の文字を保存し、AAのd. i.と共に記録した照合v1に基づいて説明の句として読む。biと同じbeの人・過程・前後点の定義をr6caへ展開する。全人間の離脱の既成事実や宗教だけの啓蒙への再定義にはしない。',
 'unsereは著者と同時代の読者を含む公衆に関わる全統治者という読み。先行の人々h26khと本文現在h26kn(h26km)を継承し、政治的範囲h26soを無関心や啓蒙的政策から選ばない。君主的統治という既存解釈を保持し、特定国名・王名・王の人数は補わない。',
 '各統治者について同じ共同体の全臣民をr6boで一致させる。Künsteは技芸一般、Wissenschaftenは学問一般であり、後見の立場を取る行為への実践的関心が両方にないと述べる。行為の現実の不実行、職務の所管の不在、全関心一般の不在とはしない。',
 'jeneは自己帰責される未成熟を、主節で重点を置いた同じ宗教事項へ具体化して受ける。本人の全関連事柄について評価された通常行使能力と同じ状態への帰責を使い、未陶冶や無知、未知・空範囲を未成熟にしない。一般状態bpとの無条件の同値は主張しない。',
 '有害さは判断・行為・生き方への不利益、不名誉は理解・判断を担う者としての尊重に反して人を貶める性質。同じ全領域の状態構成・人々・基準について、独立に肯定的性質と相対最大を要求する。同順位を許し、実害の件数・実際の嘲笑・人格の価値の消滅にはしない。',
 'weilは第一理由、überdem auchは第二理由の追加、so wie ... also auchは両最上級の並列と読む。両理由を同じ回顧へ向け、因果の実証・論理的含意・第一理由の撤回・二つの尺度の数値的一致を追加しない。',
 '主題・公衆・統治者・臣民・比較範囲の完全性と実質的評価は明示した解釈入力である。有限検査は接続・量化・否定・未知拒否を検査し、著者の歴史的又は価値的判断の真理、全現実の網羅性を証明しない。引用された内容は帰属時に実行しない。',
 '先行117主張と18全単位判断を保存する。全文判断は採用解釈に基づくアシスタントの通読判断であり、独立査読や自動同義証明ではない。u0016第二文・u0017・Einsteinは未完。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def definitions():
    text='d r6ca[process a] e[b point[g person a[g earlier d[k be[v person v process v earlier v point]]]]].\n'
    scope='k h26so[v author v public v ruler v community v reference v point]'
    text+='d r6cb[author a public a arts a sciences a reference d point d] c['+both('k r5ty[v public v reference]',
        'k h246c[v public v author v reference]','g ruler a[g community a['+scope+']]',
        'f ruler a[f community a[y['+scope+'][k r6bp[v ruler v community k h26sp[v ruler v community v reference] v arts v sciences v reference v point]]]]')+'].\n'
    text+='d r6cc[] e[b outer[k r6bt['+AUTHOR+' '+WORK+' '+TOPIC+' '+REF+' '+ANCHOR+']]].\n'
    text+='d r6cd[] e[b outer[k r6cb['+AUTHOR+' '+CURRENT+' '+ARTS+' '+SCIENCES+' '+REF+' '+ANCHOR+']]].\n'
    for n,target in (('r6ce','r6b5'),('r6cf','r6b6')):
        text+='d '+n+'[] e[b outer['+both('k h26j7['+TOPIC+' '+REF+']','k '+target+'['+TOPIC+' '+CURRENT+' '+REF+']')+']].\n'
    for n,parts in (('r6cg',('r6ce','r6cf')),('r6ch',('r6cc','r6cd','r6cg'))):
        text+='d '+n+'[] e[b outer['+both(*('t[k '+p+'[]][v outer]' for p in parts))+']].\n'
    return text+'d r6ci[] '+STATE+'[k r6b3['+TOPIC+' '+REF+']].\n'
def discourse():
    node=lambda n:'k '+n+'[]';code=lambda n:'r d[k '+n+'[]]'
    parts=['k hzon['+node('h26sv')+' '+AUTHOR+' r b[k r6ch[]] '+CTX+']',
      'k h26st['+node('h26sx')+' '+AUTHOR+' '+node('h26sw')+' '+node('h26sx')+' r[p bi] r[p r6ca] '+CTX+']',
      'k h26su['+node('h26s2')+' '+AUTHOR+' '+node('h26s5')+' r[p bp] k r6ci[] '+TOPIC+' '+REF+' '+CTX+']',
      'k h26q3['+node('h26sy')+' '+AUTHOR+' '+code('r6cc')+' '+code('r6cd')+' '+CTX+']',
      'k h26q3['+node('h26sz')+' '+AUTHOR+' '+code('r6cc')+' '+code('r6cg')+' '+CTX+']',
      'k h26sr['+node('h26sz')+' '+AUTHOR+' '+code('r6ch')+' '+code('r6cd')+' '+code('r6cg')+' '+CTX+']',
      'k h26ss['+node('h26s4')+' '+AUTHOR+' '+code('r6cg')+' '+code('r6ce')+' '+code('r6cf')+' '+CTX+']']
    pairs=(('h26r3','h26sv'),('h26sw','h26sx'),('h26s6','h26s7'),('h26s7','h26ta'),('h26s5','h26s2'),('h26s3','h26s4'))
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in pairs]
    nodes=(*NODE_INFO,'h26r3');parts+=['u[e['+node(a)+']['+node(b)+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    return 'd r6cj[] c['+both(*parts)+'].\n'
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib,roots in zip(dependencies(),(('r6bp',),('r6bt',),('r6b5','r6b6','r6b3'))):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
            elif n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6cj',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r6cj']),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='religious_emphasis_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
      new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/self-departure-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
