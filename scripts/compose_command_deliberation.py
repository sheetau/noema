"""Compose signed command appraisals and intended audible discussion in service."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, PROFILE, PARGS

PARENTS=('data/scholarly-compatibility-basis-v1.json','data/officer-command-binding-basis-v1.json')
LIBRARY='examples/v016/command-deliberation.noema'
BASIS='data/command-deliberation-basis-v1.json'
FIELDS='person a action a notice a institution a polarity c reference d'
ARGS='v person v action v notice v institution v polarity v reference'
QUESTION='i[h[a a a a c d] f]'
PRIMITIVES={
    'h242y':('[a d] i[e]',['notice','reference'],
        '同じ命令の提示に結び付けて取り上げる目的内容の閉じた記述。命令の実行内容と目的は区別し、命令が実際に目的へ適うこと、目的の実現、道徳的な正当性を含意しない。比較する間は同じ目的を保つ。'),
    'h242z':('[a d] j[a]',['notice','point'],
        '同じ命令について指定評価状況で採る、指定極性への対応とその効果を比較する構造モデルの有限変数列。有害な解や都合の悪い変数を結果から除かない。命令の目的評価と有用性評価に同じモデルを使う。'),
    'h243a':('[a d a h[a] c] c',['notice','point','variable','state'],
        '同じ命令・評価状況の構造モデルで、指定変数にこの割当てから与える二値の方程式の値。指定極性に対応する側としない側で、他の方程式・外生背景を固定する。目的や利益の尺度は別に与える。'),
    'h243b':('[a d] a',['notice','point'],
        '同じモデルで、命令の同じ本人・行為・指定極性の内容が成立する側としない側を比較する要因。列内の所属と内容への対応は合成側で検査する。否定命令では単なる行為実行の有無と逆向きになる。従う態度や指示に基づく調整はこの変数だけで表さない。'),
    'h243c':('[a d h[a] c] d',['notice','point','state'],
        '同じ命令・評価状況のモデル割当てが指す比較状況。命令内容への対応と結果の評価に同じ状況を使い、別命令の実行や別組織の成果を借りない。'),
    'h243d':('[i[e] d d] c',['goal','reference','point'],
        '同じ固定基準で、指定目的内容への到達の進み具合がこの比較状況について評価されている。達成済みか否かだけに限定せず、不明を達成や無害へ補わない。'),
    'h243e':('[i[e] d d d] c',['goal','reference','left','right'],
        '同じ固定基準で、左の状況の指定目的への到達の進み具合が右以上である。目的内容自体の是非、金銭価格、命令への服従そのものの大小へ置き換えない。比較の整合性は合成側で検査する。'),
    'h243f':('[a d d] c',['beneficiary','reference','point'],
        '同じ固定基準で、この受益対象の実務上の利害に関する結果が指定状況について評価されている。今回の受益対象は同じ軍事組織であり、論じる本人の私益へ黙って置き換えない。'),
    'h243g':('[a d d d] c',['beneficiary','reference','left','right'],
        '同じ固定基準の実務上の利害で、左の状況の指定受益対象にとっての結果が右以上である。具体的に命じた目的への到達だけとは限らず、費用や支障なども採用基準に含み得る。道徳的正当性や全員への利益とは同一視しない。'),
    'h243h':('[a a a a a c '+QUESTION+' d] c',
        ['discussion','first','second','third','fourth','polarity','question_family','reference'],
        'この議論の活動構成では、指定した同じ順序の四対象・極性・基準を閉じた質問関数へ適用した問いを、理由を述べて検討する対象として扱う。対象の評価への単なる言及や、同じ話題の別の問いとは区別する。問いの二値形式は検討の論点を指定するものであり、議論全体を短い質問発話一つへ縮めない。実際の発言・検討、肯定の結論、内容の真理、特定の宛先や全読者への公開は含意しない。'),
    'h243i':('[a a d] c',['person','activity','reference'],
        'この本人が、指定活動を自分で行うつもりで取り掛かろうとする実践的な意向を持つ。単に起きてほしいという希望、他人が行う予測、対象命題の肯定、すでに行ったこととは区別する。実行の開始・成功・規範的許可は要求しない。'),
    'h243j':('[a a a a d] c',['person','activity','office','institution','reference'],
        '同じ本人が同じ組織の職務を遂行する場面の内で行うものとして、指定活動が位置付けられている。役職保持者の全生活、勤務外の学識者としての発信、単なる職場の建物への所在とは区別する。職務への役割帰属cbは別に確認し、議論の実際の開始を含意しない。'),
    'h243k':('[a d] c',['activity','reference'],
        'この活動は、他者に聞こえるよう外に声に出して論じる様式で計画・分類される。内心の吟味や黙読とは区別する。叫び、怒り、数値的な大音量、読者世界全体への刊行や実際の聴取は要求しない。'),
}
MEANINGS={
    'r32o':'同じ本人・行為の実行zzqが指定極性に一致するという内容。肯定命令なら実行、否定命令なら不実行であり、指示に従う態度・規範的正当性・本人の意図は追加しない。',
    'r32p':'同じモデルの両側で、要因が同じ本人・行為・指定極性の内容r32oと一致するhzeを要求する。そのモデルにr2viの評価済みの非悪化と少なくとも一つの改善を適用する。否定命令に対しても内容成立側を取り違えない。',
    'r32q':'同じ命令・本人・行為・極性について、同じ命令の固定した目的h242yへの進み具合を尺度としてr32pを評価する内容。目的に資するという明示した操作的な候補であり、目標の全面的達成や唯一の適切な方法を要求しない。',
    'r32r':'r32qと同じ命令のモデルを使い、固定した同じ制度的組織の実務上の利害を尺度としてr32pを評価する内容。目的への到達と利益の観点を分け、一方が改善しても他方の改善を補わない。',
    'r32s':'同じ六引数に対する目的適合の内容r32qが成立するかを問う発話。問いの構成だけでは目的適合の真理も本人の否定的判断も導かない。',
    'r32t':'同じ六引数に対する有用性の内容r32rが成立するかを問う発話。r32sと別の評価観点であり、対象命令・人物・行為・極性・組織は変えない。',
    'r32u':'同じ本人・職務・軍事組織の勤務中に、同じ活動が本人の理性による言語的検討ca/h232p、職務帰属cb、外に声に出す様式h243kを持ち、その本人が実行する意向h243iを持つ。論点は同じ命令の目的適合r32sまたは有用性r32tで、包括的選言として両方も許す。議論や命令の実行、評価の真理は要求しない。',
    'r32v':'前段r32nの同じ任用された将校・上官・役職・組織・提示行為・命令対象・極性を、r32uの勤務中に議論しようとする条件へ束縛する。命令された行為と議論の活動は別の引数で追跡するが、原文にない一律の不等式は加えない。',
}
LIMITS=[
    'u0012[2123,2331)の前件へ向けた依存群。重大な害、würdeの仮定的評価、服従への要求、Soによる例示と文全体の帰属は未統合であり、新規意味確認済み文字数は加算しない。',
    'Zwekmäßigkeitは同じ命令の目的への進行に資すること、Nützlichkeitは同じ組織の実務上の利益に資することとして構成する候補を明示する。両者を同一にせず、道徳的な正当性へ置き換えない。目的と実務上の基準は原文が特定していないため明示的な入力として保持する。',
    'r2viの固定背景・全解比較における非悪化と改善という操作的な読みである。確率的な期待効用、利益の相殺、あらゆる状況での絶対的な適切さ、全目的の完全達成の語義を同時に説明したとはしない。本文の通読時にはこの読みの適合も確認する。',
    '命令内容成立の有無を介入するが、命令を耳にしたことや指示に従う態度そのものを要因にしていない。否定命令では内容成立が行為の不実行に対応する。モデル入力と現実の因果構造の適合は別の仮定である。',
    'über ... oder ...は同じ命令の二つの論点の包括的選言として扱い、双方の真理の選言や排他的選言としない。議論の全内容をyes/no一言へ縮めず、問いは理拠を述べ検討する論点を指定する。',
    'lautは外に声に出す様式と読み、公衆の全読者世界へ向ける公的使用とは区別する。wollteは実行しようとする意向として扱い、単なる内心の思考を禁止対象へ広げず、発言済みの事実を要求しない。',
    '意向、勤務場面、外に声に出す様式、内容への検討という一般関係を公開した意味規約で区別する。文ごとの完成内容を原始記号へ隠さず、命令、二つの評価、問い、活動範囲を別々に合成する。',
]


@lru_cache(None)
def parents():
    return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r32o[person a action a polarity c] e[b point[e[t[k zzq[v person v action]][v point]][v polarity]]].\n'
    text+='d r32p[person a action a polarity c '+PROFILE+' view h[h[a] c] d] c['+both(
        'k hze[k r32o[v person v action v polarity] v variables v equations v factor v view]',
        'k r2vi['+PARGS+']')+'].\n'
    model=('k h242z[v notice v point] i[item a state h[a] c][k h243a[v notice v point v item v state]] '
           'k h243b[v notice v point]')
    view='i[state h[a] c][k h243c[v notice v point v state]]'
    goal='k h242y[v notice v reference]'
    for name,checked,atleast,subject in [('r32q','h243d','h243e',goal),('r32r','h243f','h243g','v institution')]:
        assessment='i[state h[a] c][k '+checked+'['+subject+' v reference k h243c[v notice v point v state]]]'
        order=('i[left h[a] c right h[a] c][k '+atleast+'['+subject+
               ' v reference k h243c[v notice v point v left] k h243c[v notice v point v right]]]')
        text+='d '+name+'['+FIELDS+'] e[b point[k r32p[v person v action v polarity '+model+' '+assessment+' '+order+' '+view+']]].\n'
    for name,content in [('r32s','r32q'),('r32t','r32r')]:
        text+='d '+name+'['+FIELDS+'] f[j q[k '+content+'['+ARGS+']]].\n'
    prefix='person a office a institution a notice a action a polarity c discussion a reference d'
    topics='x[k h243h[v discussion v person v action v notice v institution v polarity r[p r32s] v reference]][k h243h[v discussion v person v action v notice v institution v polarity r[p r32t] v reference]]'
    text+='d r32u['+prefix+'] c['+both(
        'k ca[v person v discussion v reference]','k h232p[v discussion v reference]',
        'k cb[v person v discussion v office v reference]',
        'k h243j[v person v discussion v office v institution v reference]',
        'k h243k[v discussion v reference]','k h243i[v person v discussion v reference]',topics)+'].\n'
    text+='d r32v[person a office a institution a issuer a higher a notice a action a polarity c discussion a reference d] c['+both(
        'k r32n[v person v office v institution v issuer v higher v notice v action v polarity v reference]',
        'k r32u[v person v office v institution v notice v action v polarity v discussion v reference]')+'].\n'
    return text


def build():
    old,officer=parents()
    doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['zzq','hze','r2vi','ca','cb','h232p']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(officer.document,['r32n']):
        n=d['name']
        if n in imported:
            assert d==imported[n]['declaration'] and officer.entries[n]['meaning_ja']==imported[n]['meaning_ja']
        else: doc['declarations'].append(d);imported[n]=officer.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS)) & set(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']};meanings={};primitives={}
    for n,e in imported.items():
        d=e['declaration']
        if e['kind']=='definition':meanings[n]=e['meaning_ja']
        else:primitives[n]=dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='intended_in_service_deliberation_about_signed_command_appraisals',document=LIBRARY,
        primitives=primitives,definitions=meanings|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
