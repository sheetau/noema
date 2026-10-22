"""Integrate the seventh paragraph's conditional question and contrasting answer."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_progress_indications import FIELDS

PARENT='examples/v016/kant-royal-intervention-sentence.noema';PARENT_BASIS='data/royal-intervention-sentence-basis-v1.json'
DEPENDENCY='data/progress-indications-basis-v1.json'
DEPENDENCIES=(DEPENDENCY,'data/religious-collective-assessment-basis-v1.json')
FULL='examples/v016/kant-present-epoch-sentence.noema';CORE='examples/v016/present-epoch-sentence-core.noema'
BASIS='data/present-epoch-sentence-basis-v1.json';ANNOTATIONS='data/present-epoch-sentence-identifiers-v1.json'
CTX='k h26k7[]';AUTHOR='k wa[]';ACTUAL='k h26km[]';POINT='k h26kn['+ACTUAL+']';REF='k h26kj[]'
QTYPE='i d[f]';CTYPE='i d[e]'
PRIMITIVES={
 'h26kh':('[] a',[],'第七段落のwir/ihnen/die Menschenが時代評価で対象にする、実際の現在の人間集団。著者を含む全ての現在の人をh246cとmpに固定し、少数の専門家や成功者の標本へ縮めない。生存との一致・完全列挙はr5scとr5teで確認する。'),
 'h26ki':('[] a',[],'第七段落でいま人々が生きている時代。歴史上の年の数値や全世界で同一の発展段階を追加しない。期間・現在点の所属はh26aa/h26abとr5scで構成する。'),
 'h26kj':('[] d',[],'第七段落の同じ人口、宗教的事項、行使能力と集団到達基準、進行比較の規則を固定する解釈基準。著者の提示文脈や比較例の現在時点とは区別する。'),
 'h26kk':('[] a',[],'第七段落の時代評価を後続のin Religionsdingenによって具体化する宗教的な理解・判断の領域。信念・教え・実践と吟味に関するh26j7と全関連事項h26kaで内容を与え、語名だけ、本人の信仰、単一教派の教義への同意では代用しない。'),
 'h26kl':('[d] d',['comparison_case'],'同じ第七段落の比較例に対応する候補履歴の状況。現実の例h26kmでは本文の実際の候補を指し、他の例は同じ人々・主題・基準についての代替的な状況に対応する。結果に応じた別人口への交換を行わない。'),
 'h26km':('[] d',[],'第七段落の比較設定のうち、著者が実際の現在について述べる側の例。現在時点そのものはh26knで指定し、比較例と時刻を同一視しない。'),
 'h26kn':('[d] d',['comparison_case'],'同じ比較例の現在に当たる評価点。実際の例ではjetztの同じ現在を、問い・未到達・機会開放・障害漸減・徴候で共有する。外側の評価点や別の例へ指示を移さない。'),
 'h26ko':('[d] d',['comparison_case'],'同じ比較例で、現在までの機会開放と障害変化を比較する先行点。現在との前後・所属を構成側で確認する。原文に数値的な期間を追加せず、変化の結果から都合よい開始点を選ばない。'),
 'h26kp':('[d a a] a',['comparison_case','person','work'],'同じ比較例の同じ本人・取り組みについて、先行点から現在に新しい機会が成立する変化過程の参照。本人・過程・両端・生起はr5tzで確認し、異なる人に同じ過程を強要しない。'),
 'h26kq':('[] j[a]',[],'第七段落の障害比較で、固定範囲h26krの全候補を同じ粒度で列挙する有限列。非空・重複なし・完全性はrl2で確認する。現に妨げる候補だけへ列を縮めない。'),
 'h26kr':('[a] c',['condition'],'同じ固定基準で一般的な離脱への障害になりうる条件を比較する全候補範囲。妨害するか否かはr5udで別に評価し、期間・比較例ごとに範囲や条件の粒度を変えない。'),
 'h26ks':('[] b',[],'同じ有限段階の障害件数の比較で採る、一段階の減少の正の上限。原文に具体値を帰属しない。実際の例と比較例で同じ規則を保持し、正の値はr5ugとr5ukで確認する。'),
 'h26kt':('[a] j[a]',['condition'],'同じ条件の有無を評価する二値構造モデルの全変数列。条件に対応する要因h26kvを含め、両介入で同じ変数・方程式の背景を保つ。'),
 'h26ku':('[a d] h[a h[a] c] c',['condition','initial'],'同じ条件・評価の初期点における構造方程式。要因の有無だけを介入で変更し、離脱の結果を見て式を交換しない。候補ごと・時点ごとの背景差は明示する。'),
 'h26kv':('[a] a',['condition'],'同じ条件の有無に対応するモデル変数。h26kgの条件の有無との一致はr5ubで確認し、効果が現れたかを要因の真偽へ置換しない。'),
 'h26kw':('[a d h[a] c] d',['condition','initial','assignment'],'同じ条件・初期点・モデル割当てに対応する候補履歴。比較する両側で同じ人々の離脱を同じ期間規則h26kyの下に評価する。'),
 'h26kx':('[a d h[a] c h[a] c] c',['condition','initial','on_assignment','off_assignment'],'同じ背景・介入前の状態と非決定的選択枝を保ち、条件の有無だけを変更した結果の対応。両側の全解を覆うことはr2wjで確認する。生存・基準や別要因を交換せず、悪化する組を事後に除かない。'),
 'h26ky':('[d] a',['initial'],'同じ初期点から先の離脱を評価する比較期間の枠。全比較例で同じ選択規則を使い、離脱の有無に応じて終点を伸縮しない。履歴と未来の存在はr5t6で確認する。'),
 'h26kz':('[a a a '+QTYPE+' a '+QTYPE+' '+CTYPE+' d] c',['node','author','question_node','question','answer_node','answer','answer_content','context'],
   '著者が指定の問いが提出される場合を仮定し、その同じ問いに対する回答として、同じ回答箇所・発話記述・内容記述を提示する。発話行為に関する条件付きの提示であり、現実に質問又は口頭の回答が生起したこと、問いの肯定命題が真なら回答も真という物質含意、回答の真理・十分性を追加しない。回答内部の極性や対照は同じ記述の下に保持する。'),
 'h26k2':('[a a a '+QTYPE+' d] c',['node','author','prior_discourse','question','context'],
   '著者が指定した先行論述を踏まえ、論述を次の評価へ進める段階で同じ問いを取り上げるという接続を示す。先行論述から回答が論理的に必然になること、物理的因果、以前に同じ質問が実際にあったこと、過去と現在の時刻差は追加しない。'),
 'h26k3':('[] a',[],'第七段落冒頭までの同じ作品の論述部分。固定原文kant-1784:u0009からu0013までの啓蒙の説明・妨げ・自由・統治の議論を指す談話上の参照。直前の君主についての一命題だけを先行議論全体の代わりにしない。'),
 'h26k4':('[a a '+QTYPE+' '+CTYPE+' d] c',['node','author','answer','focus','context'],
   '著者が同じ回答の中で、指定の焦点内容を肯定側として明確に取り立てる。対照される別内容の否定を維持し、焦点を推測的な可能性へ弱めたり、数値確率・程度の最大値・無謬性を加えたりしない。焦点の真理を提示関係だけから実行しない。'),
 'h26k5':('[a a '+QTYPE+' '+CTYPE+' '+CTYPE+' '+QTYPE+' d] c',['node','author','question','positive','negative','answer','context'],
   '著者が同じ肯定内容を問う問いに対し、その内容を否定する極性の回答を、指定された同じ否定内容として提示する。否定疑問の二重反転、別の命題への否定、対象の存在や評価不足だけを否定回答に代用することを避ける。肯定・否定内容の構成は渡す記述で明示し、現実の発話や真理を追加しない。'),
 'h26k7':('[] d',[],'第七段落kant-1784:u0014の著者による論述の提示文脈。第六段落の文脈、内容の固定基準h26kj、実際の現在h26kn(h26km)と区別する。'),
}
NODE_INFO={
 'h26la':([0,147],'第一文全体の条件付き問答。'),
 'h26lb':([0,27],'Wenn denn nun gefragt wird:という問いの仮定的導入。'),
 'h26lc':([28,76],'現在が既に啓蒙された時代かを問う問い。'),
 'h26ld':([77,147],'so ist die Antwort以下の回答の導入と対照内容。'),
 'h26le':([5,13],'denn nunの先行論述を踏まえた次の問いへの移行。'),
 'h26lf':([97,101],'Neinの同じ問いへの否定。'),
 'h26lg':([103,147],'aber wohl以下の進行中の時代という肯定側。'),
 'h26lh':([108,112],'wohlの肯定側の取り立て。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0014['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
SETTINGS={
 'speaker':AUTHOR,'group':'k h26kh[]','epoch':'k h26ki[]','reference':REF,'topic':'k h26kk[]',
 'candidates':'p h26kl','points':'p h26kn','firsts':'p h26ko','processes':'p h26kp',
 'obstacles':'k h26kq[]','scope':'p h26kr','bound':'k h26ks[]','variables':'p h26kt','equations':'p h26ku',
 'factors':'p h26kv','worlds':'p h26kw','matches':'p h26kx','frames':'p h26ky'}
CODES=' '.join('r['+SETTINGS[n]+']' for n,_ in FIELDS)
FRAME=AUTHOR+' k h26kh[] k h26ki[] '+REF+' k h26kl['+ACTUAL+'] '+POINT
CURRENT=FRAME+' k h26kk[] k h223h['+POINT+']'
MEANINGS={
 'r5ux':'第七段落の同じ話者・人口・時代・宗教主題・固定基準と全比較規則をr5umの閉じた進行族へ供給する。場や徴候の語名を真偽関数の代用にしない。',
 'r5uy':'同じ設定の実際の現在でr5uvの既に啓蒙された時代かという問いを返す。',
 'r5uz':'r5uyと同じ設定のr5uwの未到達だが進行中という回答を返す。',
 'r5u2':'同じ実際の現在におけるr5tjの集団到達内容。問いの肯定命題とNeinの否定対象に同じ内容を使う。',
 'r5u3':'r5u2と同じ現在・人口・質付き宗教能力・基準についてr5tlの評価済みの未到達を返す。対象の不在や評価不足を未到達としない。',
 'r5u4':'同じr5ux進行族の実際の例をr5uoで選ぶ。現在の機会開放と離脱への障害漸減を連言した進行内容であり、能力の到達済みとは区別する。',
 'r5u5':'同じ現在のr5tk未到達かつ進行内容を閉じる。r5uzの回答の命題内容と一致し、wohlの側だけへ未到達を移さない。',
 'r5u6':'第七段落の同じ人口の人としての性質。未到達と進行中の対照を同じ人々について行う共通観点へ使い、異なる集団の二事実を対照へ借りない。',
 'r5u7':'第七段落第一文の問いを仮に受けた場合の回答提示を、同じ著者・段落文脈へ帰属する。denn nunの先行論述からの移行、同じ問いへのNein、同じ人口の未到達と進行の対照、wohlの肯定側の取り立て、本文順序を保持する。引用内容や実際の質問生起を実行しない。',
}
LIMITS=[
 'u0014第一文[0,147)の124非空白文字を対象とする。問いの条件・現在人口・同じ時代・到達済みの評価・未到達かつ進行中という回答・談話上の移行と対照をまとめる。第二文以降の全提示を完成扱いにしない。',
 'Wenn gefragt wird ... so ist die Antwortは、質問が提出される場合にこの回答をするという論述上の条件付き提示と読む。誰かの実際の質問又は口頭対話を補わず、問いの肯定命題を前件にした真理関数的な含意へ替えない。',
 'denn nunはそれまでの論述を踏まえて現在の時代評価へ進む談話的な移行と読む。先行議論全体を参照し、直前の一命題から時代評価を演繹したとはしない。nunをjetztとは別の歴史的時刻の変化へ替えない。',
 'wirは著者を含む同じ現在人口、Leben/jetzt/in einem Zeitalterは生存する人々と同じ現在点を含む時代の枠へ結ぶ。国名・年の数値・全世界の均一な社会状態は追加しない。',
 'aufgeklärtの集団的到達は後続のin Religionsdingenにより主題を具体化し、質付きの本人の理解力行使能力と固定された普及基準を使う。否定には同じ全評価を要求する。基準の具体値・全員一致は著者へ補わない。',
 'Zeitalter der Aufklärungは、同じ人々への自由な取り組みの新規開放と、自己に帰責される未成熟からの離脱への障害の段階的減少という後続の内容で具体化する。dahinの質付き能力目標と障害の離脱対象を区別し、到達済みの現在能力だけで進行を代用しない。有限モデルの範囲・基準・比較規則について先行読解の限界を引き継ぐ。',
 'Neinは同じ問いへの否定。aberは未到達と進行中の対照であり、両者の論理的矛盾や前言撤回ではない。wohlはこの文脈では肯定側を取り立てると読み、たぶんという数値的・推測的留保を追加しない。',
 '各参照・モデル入力は閉じたNoema記述へ明示的に供給する。文全体の意味を返す原始関係は導入せず、問答・対照等の提示関係と世界についての合成内容を区別する。有限検査は原文同値を自動証明せず、全語句の照合と通読は明示した解釈の下での判断である。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    text='d r5ux[] i c[h[d] e][k r5um['+CODES+']].\n'
    for n,target in (('r5uy','r5uv'),('r5uz','r5uw')):text+='d '+n+'[] f[k '+target+'['+CODES+' r['+ACTUAL+']]].\n'
    for n,target in (('r5u2','r5tj'),('r5u3','r5tl')):text+='d '+n+'[] e[b outer[k '+target+'['+CURRENT+']]].\n'
    text+='d r5u4[] e[k r5uo[k r5ux[] '+ACTUAL+']].\n'
    text+='d r5u5[] e[b outer[k r5tk['+CURRENT+' k r5u4[]]]].\n'
    text+='d r5u6[person a] e[b outer['+both('k aa[v person]','k h246c[k h26kh[] v person '+REF+']')+']].\n'
    question='r d[k r5uy[]]';answer='r d[k r5uz[]]';positive='r d[k r5u2[]]';negative='r d[k r5u3[]]';progress='r d[k r5u4[]]'
    parts=[
      'k h26kz[k h26lb[] '+AUTHOR+' k h26lc[] '+question+' k h26ld[] '+answer+' r d[k r5u5[]] '+CTX+']',
      'k h26k2[k h26le[] '+AUTHOR+' k h26k3[] '+question+' '+CTX+']',
      'k h26k5[k h26lf[] '+AUTHOR+' '+question+' '+positive+' '+negative+' '+answer+' '+CTX+']',
      'k h236k[k h26ld[] '+AUTHOR+' k h26lf[] '+negative+' k h26lg[] '+progress+' r[p r5u6] '+CTX+']',
      'k h26k4[k h26lh[] '+AUTHOR+' '+answer+' '+progress+' '+CTX+']']
    edges=(('h26jn','h26la'),('h26lb','h26lc'),('h26lc','h26ld'),('h26lf','h26lg'))
    parts+=['k ue[k '+a+'[] k '+b+'[] '+CTX+']' for a,b in edges]
    nodes=(*NODE_INFO,'h26jn','h26k3')
    distinct=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    parts += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5u7[] c['+both(*parts)+'].\n';return text

def build():
    old=parent();libs=dependencies();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not(set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5u7',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='present_epoch_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set().union(*(set(lib.source_sha256) for lib in libs)))},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/royal-intervention-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
