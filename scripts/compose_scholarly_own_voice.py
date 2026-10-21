"""Separate public activity candidates, own-voice execution, and two freedoms."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_confessional_teaching import MESSAGE

PARENT='data/clerical-private-conclusion-basis-v1.json'
LIBRARY='examples/v016/scholarly-own-voice.noema'
BASIS='data/scholarly-own-voice-basis-v1.json'
NAMES=('person','activity','scholar','writing','audience','subject')
FIELDS=' '.join(n+' a' for n in NAMES)+' message '+MESSAGE+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v message v reference'
TARGET='i b[h[j[a] d] e]'
PRIMITIVES={
    'h253l':('[a a a a a '+MESSAGE+' d] c',
        ['person','activity','principal','role','subject','message','point'],
        '同じ本人・活動・立場・主題・閉じた発話記述について、その活動の発言が指定した帰属先の名によるものとして位置付けられる。帰属先が本人の場合も他者の場合も正の関係で示す。活動の構成を記述する関係であり、実行前の候補にも適用できる。実際の提示、生起、受領、帰属先の承認、話者の信念、内容の真理や許可は別に要求する。他者への帰属の不在だけから本人への帰属を補わず、同じ意味を持つ別の発話記述へ自動的に移さない。'),
}
MEANINGS={
    'r44s':'同じ本人・活動・学識者の立場・書面・本来の公衆についてr3zの書面による公的使用候補を保ち、同じ主題・発話記述が本人自身の名によるh253lを結ぶ。許可、実行、書面の現存、信念、教義への慎重な吟味や善意によって候補を選び直さない。',
    'r44t':'固定基準のr44sと、評価点で同じ活動を本人が実行するcg、同じ書面のsc/sd、同じ公衆に属する少なくとも一人へのrheの実際の本人名義の提示を結ぶ内容。rheへ同じh253lを渡し、発話記述を脱引用しない。全世界の全員への到達・理解・賛同は要求しない。',
    'r44u':'本人・活動の正確な二個体列を受けてzzqの実行内容を作る。公的分類は規範対象の外の固定基準で扱い、引用した実行内容だけから活動の実行を断言しない。',
    'r44v':'同じ閉じた発話記述と、本人・活動・学識者・書面・公衆・主題の正確な六個体列および固定基準から、r44tの同じ発言実行内容を作る。列の長さと順序、発話の構文同一性を保つ。',
    'r44w':'引用持上げと引用適用で同じ発話記述をr44vへ組み込んだ、六個体列と固定基準を受ける閉じた段階1の内容関数記述を作る。規範がこの対象を受ける際には、発言・記録・実行・発話内容の真理を実行しない。',
    'r44x':'固定基準で同じ本人・活動・学識者の公的理性使用r2ziを分類し、その同じ本人と立場の規範源h247bについて、r44uの同じ活動実行への積極的許可と反対要求の不在r37cを結ぶ。未実行・禁止され得る候補も分類から除かず、信条に関する見解だけへ限定しない。',
    'r44y':'同じ書面による本人名義の公的発言候補r44sについて、同じ本人・学識者の規範源h247bから、r44wへ同じ六個体と固定基準を渡す発言実行への自由r37cを結ぶ。実際に語ったことも発話内容の真理も自由の条件へ移さない。',
    'r44z':'同じ本人・活動・学識者について、公的な理性使用の実行への自由r44xと、同じ書面・公衆・主題・発話を本人の名で提示する実行への自由r44yを別々に要求する。連言への許可一つだけで二つの単独対象への自由を代用しない。',
}
LIMITS=[
    'u0012[4735,5021)の二つの自由対象へ向けた依存群。本文94主張、既存の意味判断と確認文字数は変更しない。全該当候補への量化、同じ聖職者の学識者という立場への接続、Dagegen・nämlich・mithinと全文著者帰属は統合時に扱う。',
    '自由は先行r37cと同じ積極的許可と反対要求の不在という明示読み。教会が実際に許したこと、物理的無妨害、能力、現在の発言、発言しない許可とは区別する。',
    '公的理性使用の対象はr2ziの全分類、書面による本人名義の発言候補はr44s。古いr37jの慎重に吟味した善意の教義批評と改革提案という範囲を、この後続文へ追加しない。単独の候補の検査だけでuneingeschränktを記述済みとはしない。',
    '本人の名で語ることは正の帰属であり、教会の名でないという否定だけでは足りない。信念・真理・独創性・免許・職務の不存在は含めない。公衆はceの読者世界で、局所的な会衆や一定人数以上の集団へ変更しない。',
    '書面で語る実行内容では同じ書面の記録と参照可能性、同じ本人の提示、少なくとも一人の公衆への同じ発話の伝達を要求する。候補分類や規範の成立にはこれらの現実の実行を要求しない。h242gが同じ書面を経路とする活動構成を固定し、別の書面の存在で代用しない。',
    '全読者の実際の受領は要求せず、受領範囲は固定基準のh6tで同じ公衆に属する者に結ぶ。本人名義の発言を同じ基準と評価点の両方で追跡する。規範を評価する時点と、引用した実行内容を評価する時点を混同しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    text='d r44s['+FIELDS+'] c['+both(
        'k r3z[v person v activity v scholar v writing v audience v reference]',
        'k h253l[v person v activity v person v scholar v subject v message v reference]')+'].\n'
    speech='k rhe[v person v activity v scholar i[listener a][e[v listener][v recipient]] v subject v message v point p dg p f3 p f2 p h253l]'
    text+='d r44t['+FIELDS+'] e[b point['+both('k r44s['+ARGS+']',
        'k cg[v person v activity v point]','k sc[v writing v point]','k sd[v writing v point]',
        'g recipient a['+both('k h6t[v audience v recipient v reference]',speech)+']')+']].\n'
    text+='d r44u[bindings j[a] reference d] e[b point['+bind(('person','activity'),
        't[k zzq[v person v activity]][v point]')+']].\n'
    text+='d r44v[message '+MESSAGE+' bindings j[a] reference d] e[b point['+bind(NAMES,
        't[k r44t['+ARGS+']][v point]')+']].\n'
    template='r b[i[message '+MESSAGE+'][i[bindings j[a] reference d][k r44v[v message v bindings v reference]]]]'
    text+='d r44w[message '+MESSAGE+'] '+TARGET+'[o a['+template+'][o r[v message]]].\n'
    source='k h247b[v person v scholar v reference] v person v scholar '
    text+='d r44x[person a activity a scholar a reference d] e[b point['+both(
        'k r2zi[v person v activity v scholar v reference]',
        'k r37c['+source+'r b[p r44u] l[a][v person v activity] v reference v point]')+']].\n'
    text+='d r44y['+FIELDS+'] e[b point['+both('k r44s['+ARGS+']',
        'k r37c['+source+'k r44w[v message] l[a]['+' '.join('v '+n for n in NAMES)+'] v reference v point]')+']].\n'
    text+='d r44z['+FIELDS+'] e[b point['+both('t[k r44x[v person v activity v scholar v reference]][v point]',
        't[k r44y['+ARGS+']][v point]')+']].\n'
    return text


def build():
    old=parent();assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r3z','rhe','dg','f3','f2','cg','sc','sd','h6t','zzq','r37c','h247b']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='written_public_own_voice_candidates_execution_and_two_freedoms',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
