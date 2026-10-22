"""Integrate the first sentence of Kant's final paragraph, including its depiction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import PROFILE
from scripts.compose_prince_sentence import ANCHOR

PARENT='examples/v016/kant-legislative-freedom-sentence.noema';PARENT_BASIS='data/legislative-freedom-sentence-basis-v1.json'
DEPENDENCIES=('data/political-quoted-speech-basis-v1.json','data/republic-speech-prohibition-basis-v1.json',
 'data/military-peace-guarantee-basis-v1.json','data/enlightened-person-conditions-basis-v1.json')
ROOTS=(('r6f4','r6f3'),('r6gc','r6f6'),('r6fq','r6fo'),('r6e5','r6e2'))
LEGACY=(('examples/v016/cast-shadow.noema','data/cast-shadow-basis-v1.json','rvt'),
 ('examples/v016/described-apprehension.noema','data/described-apprehension-basis-v1.json','rvm'))
FULL='examples/v016/kant-qualified-speech-sentence.noema';CORE='examples/v016/qualified-speech-sentence-core.noema'
BASIS='data/qualified-speech-sentence-basis-v1.json';ANNOTATIONS='data/qualified-speech-sentence-identifiers-v1.json'
C5='i f[e]';ACTION='i c[h[a a] e]';MESSAGE='i b[h[a] f]'
REF='k h26wp[]';CTX='k h26wq[]';TOPIC='k h26wo[]';STANDARD='k h26wr[]';ROLE='k h26ws[]';AUTHOR='k wa[]';SCOPE='k h26wt[]'
PRIMITIVES={
 'h26wi':('[d a a d] c',['reference','source','patch','point'],'固定基準における、同じ光源の発光部分と評価点。幾何的な位置だけを発光としない。影の字義的描写に使い、現実の光源の存在を著者主張として補わない。'),
 'h26wj':('[d a a a d] c',['reference','patch','place','path','point'],'同じ固定基準と点で、発光部分から場所へ至る直接の光路。反射・屈折の経路はこの幾何光学上の直接経路と分ける。'),
 'h26wk':('[d a a d] c',['reference','path','blocker','point'],'同じ固定基準と点で、指定した遮蔽物だけを取り除き、他の条件を保てばその光路に他の遮蔽がないという比較条件。別原因の暗さを同じ遮蔽物に帰属しない。'),
 'h26wl':('[d a a d] c',['reference','blocker','path','point'],'同じ固定基準と点で、同じ遮蔽物が指定した直接光路に介在する。別の経路への介在とは分ける。'),
 'h26wm':('[d a a d] c',['reference','blocker','path','point'],'同じ固定基準と点で、その遮蔽物が指定した経路の直接光を透過させない。介在していても透明な場合は含まない。'),
 'h26wn':('[d a a d] c',['reference','region','place','point'],'同じ固定基準と点で、指定した場所が同じ影の領域を構成する場所である。非空性と全成員での遮光条件は合成側で確認する。'),
 'h26wo':('[] a',[],'第十段落第一文の自立的な判断能力を評価する、宗教上の判断から法・統治・公的討論までを含む実践的な判断領域。h26vdで規約化した領域であり、先行の宗教専用主題h26kkと同一視しない。'),
 'h26wp':('[] d',[],'第十段落第一文の人物条件・軍隊・平穏・政治的能力・共和国・危険認識・禁止・二つの引用内容に共用する固定解釈基準。好ましい結果に合わせて宛先や候補を変更しない。'),
 'h26wq':('[] d',[],'固定原文kant-1784:u0017第一文を著者が提示する論述文脈。内容を評価する本文現在と、固定した解釈基準を区別する。'),
 'h26wr':('[] a',[],'同じ第一文のnicht wagen darfで採る政治的・実践的判断基準。公的な平穏と統治を維持する責任に照らして、主体がその方針を試みてよいかを評価する。現行法令や特定の意思決定者の好みとは同一視せず、危険の存在だけから禁止を演繹しない。'),
 'h26ws':('[] a',[],'同じ第一文の共和国自身が公的方針を表明する統治主体としての役割。代表者個人の私生活や国民全員の役割とは分け、同名の現実の官職があることは要求しない。'),
 'h26wt':('[] a',[],'第十段落第一文で、同じ本人・共同体・評価点の人物条件を記述する仮定上の提示範囲。条件を満たす実在者又は発言の実行をこの範囲名から補わない。'),
 'h26wu':('[a a a '+PROFILE+' '+PROFILE+' '+PROFILE+' d] c',['node','author','scope','boundary','depiction','target','context'],
  '同じ著者・箇所・範囲で、同じ人物条件と同じ人物引数・評価点の下に、描写側の閉じた性質を対象側の閉じた性質の比喩として提示する。描写の字義的な真理又は対象の実在を主張せず、比喩と二内容の論理的同値を区別する。'),
 'h26wv':('[a a a '+PROFILE+' '+PROFILE+' '+PROFILE+' d] c',['node','author','scope','boundary','first','second','context'],
  '同じ著者・箇所・範囲・人物条件で、同じ本人と同じ評価点に第一と第二の性質がともに必要なものとして、観点の対照を伴って提示される。時間的な前後や因果的導出、一方の撤回とは分ける。'),
 'h26ww':('[a a '+C5+' '+PROFILE+' '+PROFILE+' a d d d] c',['node','author','whole','qualification','ability','community','reference','point','context'],
  '著者が同じ全体の中で、この共同体・固定基準・点の発言能力を持つ人の範囲を、指定した人物条件へ限定するものとして提示する。必要条件の向きは全体内容で構成し、条件を持つ全員が発言できるという逆向きや該当者の実在は導かない。'),
 'h26wx':('[a a '+C5+' '+C5+' '+C5+' d] c',['node','author','whole','previous','addition','context'],
  '著者が先行内容を保ちながら、現在の内容を追加の考慮事項として同じ論述に加える。先行内容からの論理的必然や、追加内容だけへの訂正とは分ける。'),
 'h26wy':('[a a '+C5+' a '+ACTION+' d] c',['node','author','whole','target_node','target','context'],
  '著者が同じ全体のこの照応箇所で、指定された引用箇所の同じ閉じた公式発言目標を指す。主体と発話行為の二引数はそれぞれの能力又は試みの範囲で束縛し、別の発言内容へ替えず、実際に発話したことを導かない。'),
 'h26wz':('[a a '+C5+' '+C5+' '+C5+' d] c',['node','author','whole','first','second','context'],
  '著者が同じ全体の第一内容と第二内容を、政治的主体のあり方による相違を示す比較として対置する。二内容の構成は別に保ち、論理矛盾、逆向きの十分条件、比較対象の実在を付け加えない。'),
 'h26w2':('[a a '+C5+' '+ACTION+' '+MESSAGE+' '+MESSAGE+' d] c',['node','author','whole','target','permission','obedience','context'],
  '著者が同じ全体の能力と禁止の対象となる公式発言を、同じ出所・基準の許可内容と服従命令の直接引用として展開する。第一内容に対する第二の唯一の留保は公式発言の内部で構成する。著者がここで読者に直接命じたことや、実際の許可・服従は補わない。'),
}
NODE_INFO={
 'h26w4':([0,303],'第一文全体。'),'h26w5':([0,4],'Aberの対照。'),'h26w6':([5,9],'auchの追加。'),
 'h26w7':([10,23],'nur derjenigeの人物範囲への限定。'),'h26xa':([24,183],'同じ人への関係節による条件。'),
 'h26xb':([30,36],'selbstの本人への強調。'),'h26xc':([30,47],'本人の判断能力。'),
 'h26xd':([49,81],'sich nicht vor Schatten fürchtetの否定を含む影の比喩。'),
 'h26xe':([83,96],'zugleich aberの同時的な条件追加と対照。'),'h26xf':([97,182],'同じ軍隊の利用と公的平穏の保証。'),
 'h26xg':([186,200],'kann das sagenの政治的能力。'),'h26xh':([191,194],'dasの後続引用への照応。'),
 'h26xi':([202,236],'共和国の試みへの禁止との比較。'),'h26xj':([202,205],'wasの同じ発言目標への照応。'),
 'h26xk':([238,303],'二内容と留保を展開する直接引用。'),'h26xl':([290,303],'nur gehorchtの唯一の留保。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0017['+str(r[0])+','+str(r[1])+')の'+m) for n,(r,m) in NODE_INFO.items()})
MEANINGS={
 'r6gd':'同じ固定基準について、ある同じ光源と遮蔽物に相対的に、非空の領域の全場所で直接光の一部又は全部が遮られるという既存rvtの影の性質。真っ暗さ、最大領域、連結性や現実の影の存在は要求しない。',
 'r6ge':'同じ本人と点で、r6gdの閉じた影の性質を対象とする既存rvmの不快な不利益予期がないという字義的な描写。基準名の一致を確かめる。対象としての影の実在や全対象への無恐怖は要求しない。',
 'r6gf':'同じ本人と固定基準のr6etを人物性質として取り出す。影の比喩の対象側である、根拠のない恐れの不在を保持し、字義的な影を怖がらないこととの同義は断定しない。',
 'r6gg':'同じ本人・共同体・基準のr6foの軍隊利用と公的平穏保証を、人物性質として取り出す。人物条件の他の要素とは同じ評価点で共用する。',
 'r6gh':'同じ本人・共同体・基準・点のr6f3の政治的発言能力を人物性質にする。呼称の一致を確認し、人物条件を定義内へ混ぜたり、単なる発声能力へ替えたりしない。',
 'r6gi':'本文現在と同じ基準で、全共同体についてr6f4の人間側の必要条件を述べる。能力のある人なら同じ本人に完全な人物条件を要求し、条件の十分性や実在は補わない。',
 'r6gj':'本文現在と同じ引用基準で、r6gcの全共和国への同じ試みの禁止を、明示した政治的判断基準と統治主体としての役割に結ぶ。',
 'r6gk':'同じ本文現在・固定基準の人間側の必要条件r6giと共和国側の禁止r6gjを合わせる第一文の内容。いずれか一方だけで全文にせず、比較の実在や引用の現実の実行は追加しない。',
 'r6gl':'固定基準の閉じた呼称をr6geへ適用した段階7の字義的描写。人物範囲と比喩対象の記述とともに渡し、構成時に影又は恐れを実行しない。',
 'r6gm':'一つの共同体を同じ全体内の束縛に保ち、完全な人物条件r6fqの下に、本人への強調r6e5、影の比喩、同じ点の精神的条件と軍隊の対照的な併存、能力への必要条件の提示を結ぶ。',
 'r6gn':'第一文全文を著者へ帰属し、先行文との対照と追加、全共同体での同じ人物条件の提示、共和国との比較、das/wasの同じ引用への照応、直接引用の展開と本文順序を統合する。引用した内容の現実の真理や実行は要求しない。',
}
LIMITS=[
 '固定原文u0017第一文[0,303)・257非空白文字を対象とする。nur derjenigeは政治的能力から人物条件への必要条件であり、条件を満たす人物の実在や能力への十分性は採らない。ein Freistaatも明示した制度モデルの一般的な種類への全称と読む。',
 'selbstは本人の判断能力への強調。宗教から法・統治までの実践判断領域を採り、宗教専用の旧範囲には戻さない。同じ本人・共同体・点の恐れ、軍隊と平穏保証を保持する。',
 'Schattenは、非空の領域で同じ光源からの直接光が遮られるという幾何光学的な字義を、根拠のない恐れの不在の比喩として読む。関連するAdelungの用例は補助であり、唯一の歴史的解釈を証明しない。否定を描写側と対象側の双方に保つが、両者の真理条件の同値や実際の影の存在は述べない。',
 'zugleich aberは精神的な条件と軍隊の条件が同じ本人・点にともに必要であるという対照的な追加。Bürgeは軍隊の公的平穏を保証する機能として既存の明示した因果比較へ結び、人格ある法的保証人や金銭補償は補わない。',
 'kann das sagenは同じ公式方針・許可・公的平穏を両立できる政治的能力。nicht wagen darfは同じ方針を危険認識の下で試みることへの政治的な負の要求。単なる許可の不在、物理的不可能、実行済みの試みだけへの規範に変えない。',
 'das/wasと後続の直接引用は、同じ基準のr2ug/r2uhを含む公式発言目標に接続する。引用内nurはこの呼びかけに付す唯一の留保。許可の成立に現実の服従を前提とせず、他の全法規の廃止や著者から読者への直接命令も補わない。',
 'Aberは前文の君主の立法上の自由と安全性に対して人物条件と共和政との差を持ち出す対照、auchはその追加と読む。前文の撤回、論理的な矛盾、前文からの演繹ではない。',
 '全記述域の直接有限評価を拒否する既存制約を保持する。試験は本文の束縛と提示を検査し、下位本体の既存報告を固定参照する。原文通読の意味判断と、歴史的主張の真理又は独立査読を区別する。段落の後続三文とEinsteinは未完。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
@lru_cache(None)
def legacy():
    out=[]
    for path,basis,root in LEGACY:
        ds=closure(parse((ROOT/path).read_text(encoding='utf-8')),(root,));ms=json.loads((ROOT/basis).read_text(encoding='utf-8'))['definitions']
        out.append((ds,{d['name']:ms[d['name']] for d in ds},basis))
    return out
def node(n):return 'k '+n+'[]'
def code(n):return 'r f[k '+n+'[]]'
def named(n):return 'k h223g['+n+']'
def profile(n,*values):return 'o a[r h[p '+n+']]['+' '.join(values)+']'
def definitions():
    providers=' '.join(('i[region a place a point d][k h26wn[v reference v region v place v point]]',
      'i[source a patch a point d][k h26wi[v reference v source v patch v point]]',
      'i[patch a place a path a point d][k h26wj[v reference v patch v place v path v point]]',
      'i[path a blocker a point d][k h26wk[v reference v path v blocker v point]]',
      'i[blocker a path a point d][k h26wl[v reference v blocker v path v point]]',
      'i[blocker a path a point d][k h26wm[v reference v blocker v path v point]]'))
    text='d r6gd[reference d] h[a] e[i[region a][b point[g source a[g blocker a[k rvt[v source v blocker v region v point '+providers+']]]]]].\n'
    match='e[s[k h223h[v reference]]][v reference]'
    shadow='o a[r[p r6gd]][k h223h[v reference]]'
    affect='p h26u4 p h26u5 p h26u6 p h26u7 i[person a prospect d][k h26va[v person v reference v prospect]]'
    text+='d r6ge[reference d] h[a] e[i[person a][b point['+both(match,'u[k rvm[v person '+shadow+' v point '+affect+']]')+']]].\n'
    text+='d r6gf[reference d] h[a] e[i[person a][k r6et[v person v reference]]].\n'
    text+='d r6gg[community a reference d] h[a] e[i[person a][k r6fo[v person v community v reference]]].\n'
    text+='d r6gh[community a reference d] h[a] e[i[person a][b point['+both(match,'k r6f3[v person v community k h223h[v reference] v point]')+']]].\n'
    text+='d r6gi[] e[b outer[f community a[t[k r6f4['+TOPIC+' v community '+REF+']]['+ANCHOR+']]]].\n'
    text+='d r6gj[] e[b outer[t[k r6gc['+STANDARD+' '+ROLE+' '+REF+']]['+ANCHOR+']]].\n'
    text+='d r6gk[] e[b outer['+both('t[k r6gi[]][v outer]','t[k r6gj[]][v outer]')+']].\n'
    text+='d r6gl[reference i[d]] '+PROFILE+'[o a[r h[p r6ge]][v reference]].\n'
    return text
def discourse():
    nref='k h223h['+REF+']';ncomm=named('v community');ntopic=named(TOPIC);whole=code('r6gk')
    boundary='k r6fq['+ntopic+' '+ncomm+' '+nref+']';pair='k r6e2['+ntopic+' '+nref+']'
    parts=['e[s['+ncomm+']][v community]',
      'k r6e5['+node('h26xb')+' '+node('h26xc')+' '+AUTHOR+' '+SCOPE+' '+TOPIC+' '+REF+' '+boundary+' '+CTX+']',
      'k h26wu['+node('h26xd')+' '+AUTHOR+' '+SCOPE+' '+boundary+' k r6gl['+nref+'] '+profile('r6gf',nref)+' '+CTX+']',
      'k h26wv['+node('h26xe')+' '+AUTHOR+' '+SCOPE+' '+boundary+' '+pair+' '+profile('r6gg',ncomm,nref)+' '+CTX+']',
      'k h26ww['+node('h26w7')+' '+AUTHOR+' '+whole+' '+boundary+' '+profile('r6gh',ncomm,nref)+' v community '+REF+' '+ANCHOR+' '+CTX+']']
    text='d r6gm[community a] c['+both(*parts)+'].\n'
    target='k r6f6['+nref+']'
    parts=['k h26ub['+node('h26w4')+' '+AUTHOR+' '+whole+' '+CTX+']',
      'k h26uc['+node('h26w5')+' '+AUTHOR+' '+whole+' '+code('r6ei')+' '+whole+' '+CTX+']',
      'k h26wx['+node('h26w6')+' '+AUTHOR+' '+whole+' '+code('r6ei')+' '+whole+' '+CTX+']',
      'f community a[k r6gm[v community]]',
      'k h26wz['+node('h26xi')+' '+AUTHOR+' '+whole+' '+code('r6gi')+' '+code('r6gj')+' '+CTX+']']
    parts+=['k h26wy['+node(n)+' '+AUTHOR+' '+whole+' '+node('h26xk')+' '+target+' '+CTX+']' for n in ('h26xh','h26xj')]
    first='o a[r b[p r2ug]]['+nref+']';second='o a[r b[p r2uh]]['+nref+']'
    parts+=['k h26w2['+node('h26xk')+' '+AUTHOR+' '+whole+' '+target+' '+first+' '+second+' '+CTX+']']
    pairs=(('h26um','h26w4'),('h26w5','h26w6'),('h26w6','h26w7'),('h26xa','h26xg'),('h26xc','h26xd'),('h26xd','h26xe'),('h26xe','h26xf'),('h26xf','h26xg'),('h26xg','h26xi'),('h26xi','h26xk'),('h26xk','h26xl'))
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in pairs]
    return text+'d r6gn[] c['+both(*parts)+'].\n'
def build():
    old=parent();libs=dependencies();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={};means={};origin={}
    for lib,roots in zip(libs,ROOTS):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n];prior=old.entries.get(n,imported.get(n))
            if prior:assert d==prior['declaration'] and e['meaning_ja']==prior['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    for ds,ms,basis in legacy():
        for d in ds:
            n=d['name'];prior=old.entries.get(n,imported.get(n))
            if prior:assert d==prior['declaration'] and ms[n]==prior['meaning_ja'],n
            else:doc['declarations'].append(d);means[n]=ms[n];origin[n]=basis
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6gn',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r6gn']),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(lib.source_sha256 for lib in libs))|{p for row in LEGACY for p in row[:2]}
    basis=dict(status='qualified_speech_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,primitives=prims,
      new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|origin,import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/legislative-freedom-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
