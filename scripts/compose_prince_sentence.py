"""Integrate the qualified prince sentence, its nested contrasts and attribution."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_release_merit import DETAILS,DARGS,NAMES,DATES,GROUND,BENEFIT,RESPONSE,STANDARD

PARENT='examples/v016/kant-named-epoch-sentence.noema';PARENT_BASIS='data/named-epoch-sentence-basis-v1.json'
DEPENDENCIES=('data/prince-merit-scope-basis-v1.json','data/haughty-designation-basis-v1.json','data/prince-conclusion-basis-v1.json','data/religious-freedom-policy-basis-v1.json')
FULL='examples/v016/kant-prince-sentence.noema';CORE='examples/v016/prince-sentence-core.noema'
BASIS='data/prince-sentence-basis-v1.json';ANNOTATIONS='data/prince-sentence-identifiers-v1.json'
C7='i h[e]';T7='i h[h[a a a] e]';T2='i c[h[a a a] e]';SIDE='i[h[a a d] h[a] e]';ASSESSMENT='i b[h[a d] c]'
AUTHOR='k wa[]';CTX='k h26og[]';REF='k h26oh[]';LABEL='k h26oi[]';SOURCE='k h26ok[]'
CURRENT='k h26kh[]';EPOCH='k h26ki[]';TOPIC='k h26kk[]';CANDIDATE='k h26kl[k h26km[]]';ANCHOR='k h26kn[k h26km[]]'
POST='k h26om[]';POSTEPOCH='k h26on[]';COHORT='currentgroup a postgroup a currentepoch a postepoch a'
COARGS='v currentgroup v postgroup v currentepoch v postepoch';COFIX=CURRENT+' '+POST+' '+EPOCH+' '+POSTEPOCH
SCOPE='k h26o2[]'
PRIMITIVES={
 'h26n7':('[a a '+C7+' d] c',['node','author','content','context'],'著者がこの箇所で段階7の閉じた内容を主張する。h236i等の内容帰属を高い引用へ保ち、内容の真理又は実行、前提の現実の成立をこの提示関係から導かない。'),
 'h26oa':('[a a a '+T7+' '+T7+' d] c',['node','author','scope','boundary','premise','context'],'著者が同じ仮定範囲で、第一対象・公的立場・共同体の同じ三引数を二つの段階7の性質に共用し、範囲条件の下で前提性質を採用して論じる。h26nnの束縛を三引数へ保ち、条件の実在・真理・内容の実行を導かない。'),
 'h26ob':('[a a a '+T7+' '+T7+' d] c',['node','author','scope','boundary','conclusion','context'],'著者が同じ仮定範囲で、第一対象・公的立場・共同体の同じ三引数を共用し、範囲条件の下で結論性質を提示する。h26noの帰結提示を三引数へ保つ。無条件の真理、別人・別役職への適用、論理的必然又は心理的因果を含意しない。'),
 'h26oc':('[a a a a '+T7+' '+T7+' a d] c',['node','author','scope','clause','boundary','focus','item','context'],'同じ著者・範囲・節で同じ三引数の条件と焦点性質を共用し、指定の対象にまで焦点が及ぶことを通常の期待を越える取り立てとして提示する。h26npと同じ働きで、当人だけという排他性、全代替対象の拒否、数値確率や現実の真理を補わない。'),
 'h26od':('[a a a a '+T7+' '+T7+' d] c',['node','author','scope','clause','boundary','property','context'],'同じ著者・範囲・節と三引数の条件の下で、性質の述定対象が第一引数の当人自身であることを対照的に強調する。h26nqと同じ働きで、周囲への働きかけだけでなく本人を対象とする。本人だけの排他性や意外性、他人の実際の性質は追加しない。'),
 'h26oe':('[a a '+C7+' '+T2+' '+T2+' d] c',['node','author','whole','negative','positive','context'],'著者が同じ全体内容のこの箇所で、同じ人・公的立場・共同体の三引数に対する否定側の方針を維持し、肯定側の方針をそれに代わる採用内容として対照的に提示する。二内容が全体のどの義務・判断・報告・評価に埋め込まれるかは全体記述に保持する。単なる併置、先行否定の撤回、実際の方針実現や現在の発話を導かない。'),
 'h26of':('[a a '+C7+' '+SIDE+' d] c',['node','author','whole','aspect','context'],'著者が同じ全体内容のこの箇所で、指定された側面の性質演算により制限された肯定内容を、少なくともこの側面については成り立つものとして提示する。演算の三設定引数と対象者は全体内の同じ束縛を用いる。他の側面でも成立するとも、他の側面では成立しないとも述べず、全体の引用内容を実行しない。'),
 'h26og':('[] d',[],'固定原文kant-1784:u0015第一文を著者が提示する第八段落の論述文脈。先行段落の提示文脈、内容の固定基準、物語内の現在点とは別にする。'),
 'h26oh':('[] d',[],'同じ第一文の一般的な君主、宗教的自己選択、良心事項、名称の用法、人口・時間比較・規範評価を固定する解釈基準。評価結果によって変更せず、本文の現在点や提示文脈とは区別する。'),
 'h26oi':('[] a',[],'同じ第一文のNamen der Toleranzにおける呼称という対象。原語の形は識別注記へ保存し、意味は同じr5wu/r5wvの裁量による宗教的自由の説明へ結ぶ。呼称を君主自身や現実の自由政策と同一視しない。'),
 'h26oj':('[a] a',['community'],'同じ第一文の用法共同体で、君主へ当該名称を適用しうる関連人物の全範囲を固定した集団。実際に用いた人だけ、拒否に従う人だけへ縮めない。所属は同じ基準のh246cで与える。'),
 'h26ok':('[] a',[],'同じ第一文の公的立場における義務・許容・対人尊重の要求を解釈する規範出所。特定法令や倫理学説を原文に補わず、本人・政府組織・名称使用者と自動的に同一化しない。具体的内容と正負の要求は既存の記述付き関係へ渡す。'),
 'h26ol':('[a] a',['community'],'同じ第一文の仮定的な自己報告で、その共同体の君主が自分の義務判断を述べる相手として想定する全受け手範囲。本文に具体的な聴衆名を追加せず、非空性・全員への同じ内容の伝達は発言の記述内で確認する。実際の報告や聴衆の同意は要求しない。'),
 'h26om':('[] a',[],'同じ第一文のNachweltの人間集団。現在時代の全点より後の全期間のどこかで生存する人々に固定し、完全性はr5ysで確認する。感謝する者だけ又は血縁の子孫だけを選ばない。'),
 'h26on':('[] a',[],'同じ第一文の後代の時代範囲。前段落と同じ現在時代より後の履歴全体をr5yqで固定し、一世代だけや都合のよい区間に縮めない。'),
 'h26oo':('[a a d] c',['office','community','point'],'同じ第一文の名称評価において、指定した公的立場・共同体での自己への名称採用を調べる、固定した関連仮定場面の全範囲。実際の使用例又は既に高慢と評価した例だけでなく、反例になりうる場面も含める。非空・採用用例の存在・全用例への評価はr5xgで確認する。'),
 'h26op':('[a a] a',['office','community'],'同じ第一文の名称評価で、指定の公的立場・共同体において名称を自分へ採用しうる関連人物の全候補集団。現に拒否する君主や実際に高慢な人物だけには縮めず、所属・非空性・全用例の評価は同じ基準で結ぶ。'),
}
NODE_FRAGMENTS={
 'h26oq':('Ein Fürst,','zu bedienen.'), 'h26or':('der es seiner','zu lassen,'),
 'h26os':('der also','von sich ablehnt:'), 'h26ot':('selbst den','von sich ablehnt:'),
 'h26ou':('ist selbst','aufgeklärt,'), 'h26ov':('ist selbst','aufgeklärt,'),
 'h26ow':('und verdient','zu bedienen.'), 'h26ox':('sondern','zu lassen,'),
 'h26oy':('wenigstens','der Regierung,'), 'h26oz':('den hochmüthigen','der Toleranz'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0015第一文の'+a+' … '+b+'の提示箇所。'+('当人の強調を示す子箇所。' if n=='h26ov' else '')) for n,(a,b) in NODE_FRAGMENTS.items()})
PRIMITIVES['h26o2']=('[] a',[],'同じ第一文の一般的な君主について、人物・役職・共同体を共有して条件と結論を述べる仮定範囲。現実の一人の王や特定国の存在ではない。')
MEANINGS={
 'r52y':'同じ集団・時代に生存する応答者が、同じ恩恵への感謝と同じ功績への強い称揚を示す応答性質。聴衆はその発言で同じ功績の内容を伝えられる人の非空範囲とし、現在と全後代へ一つの固定聴衆を強制しない。',
 'r52z':'r52yの全設定を閉じる段階1の応答記述。応答ごとにその発言の受け手を扱い、功績と恩恵の記述は同じ値を保持する。',
 'r522':'同じ参照を確認したr52zの応答に、真の功績と非空の全基準によるr52kを適用する。現実の発話・感謝を実行しない。',
 'r523':'現在世界と全後代の双方について、同じ人物・功績・恩恵・基準現在にr522の適合を要求する。両時代の実際の聴衆を一つに固定しない。',
 'r524':'r52uと同じ具体的解放・比較評価・生存受益者を、応答時の受け手を開いたr523へ接続する。',
 'r525':'r52vと同じ比較評価と両範囲の全適合基準を、同じ具体的なr524へ供給する。',
 'r526':'同じ現在点の本人の能力と、本人ごとの解放・政府・前後人口・受益者・前後点を結論内で選ぶr525を連言する。',
 'r527':'同じ限定君主の全員にr526を適用する一般条件。前後件の役職・共同体・基準を共有し、聴衆の固定による余計な制約を加えない。',
 'r53a':'本文の一般的な君主の範囲を、人・役職・共同体の三引数に保つ。実在や特定国への限定は追加しない。',
 'r53b':'本文の名称・使用者・規範出所・宗教的対象集団・聴衆・基準を固定し、同じ人・役職・共同体の完全な君主条件r5xjを返す。',
 'r53c':'同じ三引数と本文設定で、義務判断を述べることを自分に不相応でないとする本人の品位判断を返す。',
 'r53d':'同じ三引数と本文設定で、同じ呼称の自分への適用を拒否する性質を返す。',
 'r53e':'同じ三引数と本文の現在・世界・後代について、その君主自身の具体的な最初の解放を根拠とする称揚適合を返す。',
 'r53f':'同じ三引数の当人に、本文の宗教主題と固定基準の個人の啓蒙状態r5xvを返す。役職の性質を本人の能力と同一視しない。',
 'r53g':'同じ三引数の本人が同じ人々の宗教的選択について何も指図しないという、自己報告内の否定側の方針を返す。',
 'r53h':'同じ三引数の本人が同じ人々へ宗教上の全面的な自己選択の自由を残すという、自己報告内の肯定側の方針を返す。',
 'r53i':'本文の同じ現在における君主職・共同体の全組合せについて、全参照を確認し、限定された本人の能力と具体的功績への称揚適合を一般条件として述べる。原文の現在を外側の評価点で移さない。',
 'r53j':'本文の君主職・共同体について、同じ名称を自己採用する固定された全関連用例が、相手への必要な尊重を損なう非対称を含むという名称評価を返す。拒否する本人の前件や高慢な人格へ置き換えない。',
 'r53k':'同じ第一文の君主に関する一般条件と、独立した高慢な名称の評価を連言する。名称評価が偽であることを前件不成立へ隠さない。',
 'r53l':'第一文全体と名称評価を著者へ帰属し、同じ三引数の仮定範囲の下で前提・alsoの帰結・名称さえの焦点・本人の啓蒙・称揚を結ぶ。埋め込まれたsondernの対照、wenigstensの政府側の肯定下限、本文順序を保持し、引用内容を現実の事実として実行しない。',
}
LIMITS=[
 '固定原文u0015第一文[0,573)を対象とする。Ein Fürstは同じ現在における君主職と共同体についての一般条件と読み、特定のフリードリヒの実在主張へ変更しない。役職・共同体・当人を三引数で共有する。',
 '自己報告を品位に反しないとする外側の本人の判断と、名称の自分への適用拒否を前件に置く。内側の義務判断、実際の義務・自由政策、実際の報告又は誠実さを前件へ追加しない。',
 '宗教的自己選択の対象は本文の現在の全人間に固定する。前段落と同じ現在集団・時代・宗教領域・履歴・現在点を参照するが、第八段落の提示文脈と解釈基準は新たに分ける。名称使用者・仮定用例・自己報告の受け手は意味規約を持つ全範囲の供給元に固定する。',
 '高慢は呼称の自己採用に含まれる他者への尊重を損なう非対称の評価であり、拒否者本人を高慢とするのではない。各君主職・共同体の関連用例について著者が述べる独立した評価として、一般条件の前件の外側に保持する。',
 'sondernは非指図を維持し、全面的な自由を採用側として対照提示する読みとする。単なる沈黙だけで全面的自由にならず、その内容は義務判断の自己報告に対する品位評価の内側へ保持する。',
 '政府側の解放は、時点別の全人口の政府による拘束から同じ個々人の自由への変化とする。wenigstensはこの側面の肯定を下限として提示し、他側面の自由も不自由も追加しない。全員の能力取得とは分ける。',
 '功績・比較評価・世界と後代の範囲・全適合基準は既存の閉じた構成へ接続する。後代の感謝は別人への過去の恩恵を認める場合を含み、未来全員の実際の心情や発話を主張しない。称揚の受け手は各発言の非空の人間範囲とし、現在と後代へ一つの固定聴衆を課さない。',
 '引用段階は応答と功績1、比較評価1、恩恵0、本人条件と能力および本文帰属7を保持する。各語義・引用・量化の既存検査は保存する。原刊のコロンと頁またぎ、後続のist/sei差を維持し、第二文以後は今回の範囲に含めない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def fields(community='v community',office='v office'):
    return LABEL+' k h26oj['+community+'] '+SOURCE+' '+office+' '+CURRENT+' '+community+' '+TOPIC+' k h26ol['+community+'] '+REF
def policy():return 'v actor '+CURRENT+' v community '+TOPIC+' '+REF
def qualified(target):return 't[c[k '+target+'['+fields()+']][v actor]][v point]'
def witness(target,point='v point'):
    selected='t[c[k '+target+'['+DARGS+' '+COARGS+' v beneficiary]][v actor]]['+point+']'
    for n,s in reversed((('activity','a'),('government','a'),('beforegroup','a'),('aftergroup','a'),('beneficiary','a'),('first','d'),('acted','d'),('last','d'))):selected='g '+n+' '+s+'['+selected+']'
    return selected
def response_definitions():
    scope='group a epoch a benefaction a beneficiary a reference d candidate d anchor d benefit '+BENEFIT+' ground '+GROUND
    names=('group','epoch','benefaction','beneficiary','reference','candidate','anchor')
    code='o a[r[p ro7]][v ground]'
    audience='i[recipient a]['+both('k aa[v recipient]','k h234g[v response v recipient v actor '+code+' v point]')+']'
    body=both('k h246c[v group v holder v reference]','k h256o[v holder v candidate v point]','k h26ab[v epoch v reference v candidate v point]',
        'x[e[v anchor][v point]][k ic[v anchor v point v candidate]]',
        't[c[k r5yo[v benefaction v beneficiary v benefit v reference v candidate]][v holder v actor]][v point]',
        't[c[k r52g['+audience+' v ground v reference]][v holder v response v actor]][v point]')
    text='d r52y['+scope+'] h[a a a] e[i[holder a response a actor a][b point['+body+']]].\n'
    named=' '.join(n+(' i[d]' if n in ('reference','candidate','anchor') else ' i[a]') for n in names)
    text+='d r52z['+named+' benefit i['+BENEFIT+'] ground i b['+GROUND+']] '+RESPONSE+'[o a[r b[p r52y]]['+' '.join('v '+n for n in names)+' v benefit v ground]].\n'
    ns=['k '+('h223h' if n in ('reference','candidate','anchor') else 'h223g')+'[v '+n+']' for n in names]
    valid=both(*('e[s['+c+']][v '+n+']' for n,c in zip(names,ns)))
    response='k r52z['+' '.join(ns)+' o r[v benefit] o r[v ground]]'
    text+='d r522['+scope+' standards j['+STANDARD+']] h[a] e[i[actor a][b point['+both(valid,'t[k r52k[v actor '+response+' v ground v standards]][v point]')+']]].\n'
    merit=COHORT+' benefaction a beneficiary a candidate d anchor d benefit '+BENEFIT+' ground '+GROUND+' firststandards j['+STANDARD+'] laststandards j['+STANDARD+']'
    side=lambda s:'t[c[k r522[v '+s+'group v '+s+'epoch v benefaction v beneficiary v reference v candidate v anchor v benefit v ground v '+('first' if s=='current' else 'last')+'standards]][v actor]][v point]'
    text+='d r523[reference d '+merit+'] h[a] e[i[actor a][b point['+both('e[v point][v anchor]',
        'k r5ys[v currentgroup v postgroup v currentepoch v postepoch v reference v candidate v anchor]',side('current'),side('post'))+']]].\n'
    return text
def bound_definitions():
    ns=['k '+('h223h' if n in DATES else 'h223g')+'[v '+n+']' for n in NAMES]
    ground='k r52t['+' '.join(ns)+' v assessment]'
    benefit='k r5zp[k h223g[v government] k h223g[v community] k h223h[v reference]]'
    release='v actor v activity v government v beforegroup v aftergroup v community v reference v candidate v first v acted v last v office v anchor s[v assessment] v beneficiary'
    text='d r524['+DETAILS+' assessment '+ASSESSMENT+' '+COHORT+' beneficiary a firststandards j['+STANDARD+'] laststandards j['+STANDARD+']] h[a] e[i[actor a][b point['+both(
        *('e[s['+c+']][v '+n+']' for n,c in zip(NAMES,ns)), 'k r52d['+release+']',
        't[c[k r523[v reference '+COARGS+' v activity v beneficiary v candidate v anchor '+benefit+' '+ground+' v firststandards v laststandards]][v actor]][v point]')+']]].\n'
    assessment='k r52s[k h223h[v reference] k h223h[v candidate]]'
    standard=lambda s:'k h26n6[v actor v office v community v '+s+'group v '+s+'epoch v reference]'
    text+='d r525['+DETAILS+' '+COHORT+' beneficiary a] h[a] e[i[actor a][b point[t[c[k r524['+DARGS+' '+assessment+' '+COARGS+' v beneficiary '+standard('current')+' '+standard('post')+']][v actor]][v point]]]].\n'
    frame='office a community a topic a reference d candidate d anchor d '+COHORT
    text+='d r526['+frame+'] h[a] e[i[actor a][b point['+both('e[v point][v anchor]',
        't[c[k r5xv[v topic v reference]][v actor]][v point]',witness('r525'))+']]].\n'
    from scripts.compose_qualified_prince_frame import FIELDS,ARGS
    text+='d r527['+FIELDS+' candidate d anchor d '+COHORT+'] e[k r5xk['+ARGS+' k r526[v office v community v topic v reference v candidate v anchor '+COARGS+']]].\n'
    return text
def source_definitions():
    def triple(n,body):return 'd '+n+'[] h[a a a] e[i[actor a office a community a][b point['+body+']]].\n'
    text=triple('r53a','k r5xh[v actor v office v community v point]')+triple('r53b',qualified('r5xj'))
    speech=SOURCE+' v office '+CURRENT+' v community '+TOPIC+' k h26ol[v community] '+REF
    refusal=LABEL+' k h26oj[v community] '+SOURCE+' v office '+CURRENT+' v community '+TOPIC+' '+REF
    text+=triple('r53c','t[c[k r5wq['+speech+']][v actor]][v point]')+triple('r53d','t[c[k r5w5['+refusal+']][v actor]][v point]')
    # Close all shared source settings, leaving the individual event witnesses inside.
    merit=witness('r525')
    replace={'reference':REF,'candidate':CANDIDATE,'anchor':ANCHOR,'currentgroup':CURRENT,'postgroup':POST,'currentepoch':EPOCH,'postepoch':POSTEPOCH}
    import re
    merit=re.sub(r'v ([a-z2-7]+)',lambda m:replace.get(m[1],m[0]),merit)
    text+=triple('r53e',both('e[v point]['+ANCHOR+']',merit))
    text+=triple('r53f','t[c[k r5xv['+TOPIC+' '+REF+']][v actor]][v point]')
    text+=triple('r53g','t[k r5v6['+policy()+']][v point]')+triple('r53h','t[k r5v7['+policy()+']][v point]')
    role='k h234f[v office v community '+ANCHOR+']'
    general=both('k r5xr['+fields()+']','t[k r527['+fields()+' '+CANDIDATE+' '+ANCHOR+' '+COFIX+']]['+ANCHOR+']')
    text+='d r53i[] e[b outer[f office a[f community a[y['+role+']['+general+']]]]].\n'
    appraisal='k r5xg['+LABEL+' '+SOURCE+' v office '+CURRENT+' v community '+TOPIC+' '+REF+' k h26op[v office v community] i[point d][k h26oo[v office v community v point]]]'
    text+='d r53j[] e[b outer[f office a[f community a[y['+role+']['+appraisal+']]]]].\n'
    text+='d r53k[] e[b outer['+both('t[k r53i[]][v outer]','t[k r53j[]][v outer]')+']].\n'
    return text
def discourse():
    code=lambda n:'r h[k '+n+'[]]'
    head,qualified=code('r53a'),code('r53b');whole=code('r53k');shared=AUTHOR+' '+SCOPE
    node=lambda n:'k '+n+'[]'
    parts=['k h26n7['+node('h26oq')+' '+AUTHOR+' '+whole+' '+CTX+']',
        'k h26n7['+node('h26oz')+' '+AUTHOR+' '+code('r53j')+' '+CTX+']',
        'k h26oa['+node('h26or')+' '+shared+' '+head+' '+code('r53c')+' '+CTX+']',
        'k h26ob['+node('h26os')+' '+shared+' '+head+' '+code('r53d')+' '+CTX+']',
        'k ud['+AUTHOR+' i[n a][e[v n]['+node('h26or')+']] '+node('h26os')+' '+CTX+']',
        'k h26oc['+node('h26ot')+' '+shared+' '+node('h26os')+' '+head+' '+code('r53d')+' '+LABEL+' '+CTX+']',
        'k h26ob['+node('h26ou')+' '+shared+' '+qualified+' '+code('r53f')+' '+CTX+']',
        'k h26od['+node('h26ov')+' '+shared+' '+node('h26ou')+' '+qualified+' '+code('r53f')+' '+CTX+']',
        'k h26ob['+node('h26ow')+' '+shared+' '+qualified+' '+code('r53e')+' '+CTX+']',
        'k h26oe['+node('h26ox')+' '+AUTHOR+' '+whole+' r c[k r53g[]] r c[k r53h[]] '+CTX+']',
        'k h26of['+node('h26oy')+' '+AUTHOR+' '+whole+' r[p r5zn] '+CTX+']']
    parts += ['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in (('h26m4','h26oq'),('h26or','h26os'),('h26ou','h26ow'))]
    nodes=(*NODE_FRAGMENTS,'h26o2','h26oi','h26m4')
    parts += ['u[e['+node(a)+']['+node(b)+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    return 'd r53l[] c['+both(*parts)+'].\n'
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    roots=(['r52a','r52g','r52k','r52d','r52s','r52t','r5yo','r5ys','r5xv','r5xk','h26n6','h234g'],['r5xg'],['r5xr'],['r5v6'])
    for lib,selected in zip(dependencies(),roots):
        for d in closure(lib.document,selected):
            n=d['name'];e=lib.entries[n]
            if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
            elif n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+response_definitions()+bound_definitions()+source_definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r53l',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r53l']),statements=[new])
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in dependencies()))
    basis=dict(status='qualified_prince_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/named-epoch-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    annotations['entries'].append(dict(symbol='h26oi',role='designation',forms=[dict(text='Toleranz',language='de',role='edition_transcription')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
