"""Integrate the officer example: hypothetical harm and directed obedience."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, side, PROFILE, PARGS, STATE, TRUE

PARENT = 'examples/v016/kant-scholarly-compatibility.noema'
PARENT_BASIS = 'data/scholarly-compatibility-basis-v1.json'
DEPENDENCY = 'data/command-deliberation-basis-v1.json'
FULL = 'examples/v016/kant-officer-example.noema'
CORE = 'examples/v016/officer-example-core.noema'
BASIS = 'data/officer-example-basis-v1.json'
ANNOTATIONS = 'data/officer-example-identifiers-v1.json'
NAMES = ('person', 'office', 'institution', 'issuer', 'higher', 'notice', 'action', 'work')
PREFIX = 'a a a d d'
PRIMITIVES = {
    'h243l': ('['+PREFIX+'] j[a]', ['person','activity','work','reference','point'],
        '同じ本人による同じ活動の実行が同じ事務へ及ぼす影響を比較する有限変数列。同じ固定基準・評価状況の背景を保ち、有害な解を結果から除かない。意向だけの存在を実行の有無へ置き換えない。'),
    'h243m': ('['+PREFIX+' a h[a] c] c', ['person','activity','work','reference','point','variable','state'],
        '同じ活動・事務・固定基準・評価状況の構造モデルで、指定変数にこの割当てから与える二値の方程式の値。実行の有無を変える両側で他の方程式と外生背景を固定する。'),
    'h243n': ('['+PREFIX+'] a', ['person','activity','work','reference','point'],
        '同じモデルで指定本人による指定活動の実行の有無を比較する要因。列内の所属、両側の解の存在、同じ実行内容との対応は合成側で確認する。命令の不履行や内心の意向をそれだけでこの要因としない。'),
    'h243o': ('['+PREFIX+' h[a] c] d', ['person','activity','work','reference','point','state'],
        '同じモデル割当てが指す仮定的な比較状況。活動の実行と同じ事務の結果をこの状況で評価する。比較状況を現実の実行や被害の発生として断言しない。'),
    'h243p': ('[a d d d] a', ['work','reference','on','off'],
        '同じ事務・固定基準で、実行側の状況と不実行側の状況の結果の差に与える程度。程度対象は同じ評価観点に依存し、数値である必要はない。低下の方向と重大さは別々に確認する。'),
    'h243q': ('[a d a] c', ['work','reference','degree'],
        '同じ事務・固定基準で、この程度が文脈上の高い水準に達している。原文にない数値閾値、全面的破壊、取り返しのつかなさを要求しない。差があるだけでこの判定を補わない。'),
    'h243r': ('[a a a i b[h[j[a] c d] e] j[a] c d c d] c',
        ['source','person','role','target','bindings','target_sign','reference','required_sign','point'],
        '規範の出所が、同じ本人に同じ立場で、段階1の閉じた内容関数へ同じ順序の個体列・対象極性・基準を渡した内容の要求極性を満たすよう要求する。h237zの対象に極性引数を明示した一般化。対象極性と要求極性を混同しない。要求対象を評価せず、実際の履行・規範の正当性・許可を含意しない。'),
    'h243s': ('[a a a i d[e] i d[e] d] c',
        ['example_node','author','general_node','general_content','example_content','context'],
        '著者が同じ提示文脈で、この箇所の内容を先行箇所の一般内容の具体例として示す。h233lと同じ例示関係を段階3の閉じた内容で扱う。帰属された条件や規範を維持し、現実の実例の存在、内容の真理、全事例の網羅、論理的証明を含意しない。'),
    'h243t': ('[] a', [], '固定原文kant-1784:u0012[2123,2331)、So würdeからer muß gehorchen.までの将校の例示文全体の箇所。'),
}
MEANINGS = {
    'r32w': '同じモデルの評価済みで整合した比較r2vdを要求し、実行側と不実行側の非空の全解対について、実行側が厳密に劣り、その差の程度が高いことを要求する。単なる低下、比較不能、解なしを重大な害へ補わない。',
    'r32x': '同じ本人の同じ活動の実行zzqと要因が両介入で対応するhzeを、同じ事務の固定した評価h242n/oと差の程度h243p/qによるr32wへ結ぶ内容。仮定的な実行の影響であり、基準時の実行・被害を断言しない。',
    'r32y': '同じ出所・本人・職務・行為・極性の基準時の要求h7aについて、評価点で内容r32oを満たし、その要求を自分の遂行の指示として受け入れ調整するh234bという単一命令への服従内容。結果の偶然の一致や別命令への服従で代用しない。',
    'r32z': '出所・本人・職務・行為の正確な四個体列、対象極性、基準を、同じ単一命令への服従内容r32yへ適用する閉じたアダプター。不足・余分の列を拒否する。',
    'r322': '同じ上官を当該指示の規範の出所として、同じ本人・職務・行為・対象極性・基準のr32zを正極性で要求する内容。否定命令でも服従自体への要求は正極性であり、実際の服従や指示の正当性は断言しない。',
    'r323': '同じ任用された将校・上官・上下役職・組織・命令提示・対象行為・極性r32nを、先行する同じ担当職務と事務r3m、およびその事務の対象行為h237xへ束縛する例示範囲。規範の成立や服従の成否で範囲を選び直さない。',
    'r324': '固定基準h232vでr323に属する各命令事例について、同じ上官の指示への服従要求r322を提示する。それとは別に、同じ職務・事務の議論活動についてr32uの意向条件が成立するなら、その実行にはr32xの重大な害があるという仮定的内容を結ぶ。意向がなければ義務まで消える構造にしない。',
    'r325': '将校の例示文全体r324を著者waと同じ提示h232oへ帰属し、先行r3nの職務内の制約の具体例として示す。直前の学識者の文h242iからの順序を保持し、例示や引用を実際の出来事にしない。',
}
LIMITS = [
    'Soは先行する職務内の制約r3nの具体例として読む。実在の特定将校の出来事を報告したとはせず、同じ機構に割り当てられた職務・事務の例示範囲を明示する。直前の学識者としての可能性を撤回しない。',
    'wenn ... wollteは勤務中に当該命令を声に出して論じようとする実践的意向を条件とする。wouldの評価対象はその企てを実行する場合の影響であり、意向が内心にあるだけで被害が発生したとはしない。仮定の前件や議論の実行を現実の事実として追加しない。',
    'sehr verderblichは同じ事務の遂行に対する重大な低下として読む。固定背景のモデルの実行側と不実行側の全解対に厳密な低下と文脈上高い程度を要求する頑健な読みである。通常性や確率的期待値、全面的破壊、道徳的邪悪さに置き換えない。尺度と程度基準の現実への適合は解釈上の仮定であり、本文から数値を捏造しない。',
    'Offizierは任用された将校、Oberenは同じ軍事組織の指揮上位者であり、直属のみには限定しない。anbefohlenは同じ提示者から本人への指示の力を持つメッセージとする。指示内容は肯定・否定の両極性を保持する。',
    'Zwekmäßigkeitは同じ命令の固定した目的への進行、Nützlichkeitは同じ組織の実務上の利害への寄与という操作的な読みを採る。比較は非悪化と少なくとも一つの改善による。問いは理拠を述べ検討する論点であり、議論全体をyes/no一言へ縮めない。oderは包括的選言とし、評価内容の真理は要求しない。',
    'im Diensteとlautは同じ職務・事務の遂行中に外へ声に出す様式であり、内心の吟味・勤務外の学識者としての刊行・叫ぶ大音量とは分ける。議論の活動と命じられた行為は別々に追跡する。',
    'er muß gehorchenは、この指示の出所である同じ上官から同じ本人に同じ職務で求められる、同じ命令への服従として読む。ここでは単一命令の内容への対応と指示に基づく調整を構成し、前文の全職務要求への服従r3iを削除・有限化しない。上官の規範的要求の報告は正当性の承認ではない。',
    '服従要求は議論の意向に依存させず、命令事例の範囲に置く。命令提示r32nから要求を論理的に導出したのではなく、原文の後半の規範内容として別に記述する。引用した服従内容のh7a・h234b・実行をその場で評価しない。',
    '検査は束縛・極性・比較・帰属の対照を確認するもので、原文との同義性や現実の因果関係を自動証明しない。有限域での巨大な全文評価を避け、個別の実評価と量化境界の診断を区別する。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def dependency(): return load_catalog(ROOT, DEPENDENCY)


def definitions():
    severe = both('c[v atleast][v off v on]', 'u[c[v atleast][v on v off]]', 'c[v high][v on v off]')
    pairs = side('rw', True, 'i[on '+STATE+']['+side('rw', False, 'i[off '+STATE+']['+severe+']')+']')
    text = 'd r32w['+PROFILE+' high h['+STATE+' '+STATE+'] c] c['+both('k r2vd['+PARGS+']', pairs)+'].\n'
    prefix = 'v person v activity v work v reference v point'
    model = 'k h243l['+prefix+'] i[item a state '+STATE+'][k h243m['+prefix+' v item v state]] k h243n['+prefix+']'
    def view(s): return 'k h243o['+prefix+' v '+s+']'
    assessed = 'i[state '+STATE+'][k h242n[v work v reference '+view('state')+']]'
    order = 'i[left '+STATE+' right '+STATE+'][k h242o[v work v reference '+view('left')+' '+view('right')+']]'
    high = 'i[on '+STATE+' off '+STATE+'][k h243q[v work v reference k h243p[v work v reference '+view('on')+' '+view('off')+']]]'
    text += 'd r32x[person a activity a work a reference d] e[b point['+both(
        'k hze[k zzq[v person v activity] '+model+' i[state '+STATE+']['+view('state')+']]',
        'k r32w['+model+' '+assessed+' '+order+' '+high+']')+']].\n'
    text += 'd r32y[source a person a role a action a polarity c reference d] e[b point['+both(
        'k h7a[v source v person v role v action r[p zzq] v polarity v reference]',
        't[k r32o[v person v action v polarity]][v point]',
        'k h234b[v source v person v role v action r[p zzq] v polarity v reference v point]')+']].\n'
    body = both('k rdr[v bindings n p e b]', *(f'a[v bindings][n p {digit} b][v {name}]' for name,digit in zip(('source','person','role','action'),'abcd')),
        't[k r32y[v source v person v role v action v polarity v reference]][v point]')
    for n in reversed(('source','person','role','action')): body = 'g '+n+' a['+body+']'
    text += 'd r32z[bindings j[a] polarity c reference d] e[b point['+body+']].\n'
    text += 'd r322[source a person a role a action a polarity c reference d] e[b point[k h243r[v source v person v role r b[p r32z] l[a][v source v person v role v action] v polarity v reference '+TRUE+' v point]]].\n'
    fields = ' '.join(n+' a' for n in NAMES)+' polarity c reference d'
    args = ' '.join('v '+n for n in NAMES)+' v polarity'
    text += 'd r323['+fields+'] c['+both(
        'k r32n[v person v office v institution v issuer v higher v notice v action v polarity v reference]',
        'k r3m[v person v office v work v reference]',
        'k h237x[v person v office v work v action v reference]')+'].\n'
    ref = 'k h232v[]'
    intent = both('k r32u[v person v office v institution v notice v action v polarity v discussion '+ref+']',
                  'k h237x[v person v office v work v discussion '+ref+']')
    content = 'y[k r323['+args+' '+ref+']]['+both(
        't[k r322[v issuer v person v office v action v polarity '+ref+']][v point]',
        'f discussion a[y['+intent+'][t[k r32x[v person v discussion v work '+ref+']][v point]]]')+']'
    content = 'f polarity c['+content+']'
    for n in reversed(NAMES): content = 'f '+n+' a['+content+']'
    text += 'd r324[] e[b point['+content+']].\n'
    n, author, ctx, quote = 'k h243t[]', 'k wa[]', 'k h232o[]', 'r d[k r324[]]'
    text += 'd r325[] c['+both('k h236i['+n+' '+author+' '+quote+' '+ctx+']',
        'k h243s['+n+' '+author+' k h242c[] r d[k r3n[]] '+quote+' '+ctx+']',
        'k ue[k h242i[] '+n+' '+ctx+']', 'u[e[k h242i[]]['+n+']]')+'].\n'
    return text


def build():
    old, lib = parent(), dependency()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imported = {}
    for d in lib.document['declarations']:
        name = d['name']
        if name in old.entries:
            assert d == old.entries[name]['declaration']
            assert lib.entries[name]['meaning_ja'] == old.entries[name]['meaning_ja']
        else:
            doc['declarations'].append(d); imported[name] = lib.entries[name]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(imported))
    doc = parse(format_graph(doc, 'compact') + ''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r325', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    ds = {d['name']: d for d in added}
    meanings = {n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'} | MEANINGS
    primitives = {n:dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=e['arguments'], meaning_ja=e['meaning_ja'])
                  for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis = dict(status='officer_example_hypothetical_serious_harm_and_obedience', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, definitions=meanings, primitives=primitives,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)}, limitations=LIMITS)
    body = format_graph(doc, 'compact')+'\n'
    annotations = json.loads((ROOT/'data/scholarly-compatibility-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda v: json.dumps(v, ensure_ascii=False, indent=2)+'\n'
    return {FULL:body, CORE:format_graph(core,'compact')+'\n', BASIS:enc(basis), ANNOTATIONS:enc(annotations)}
