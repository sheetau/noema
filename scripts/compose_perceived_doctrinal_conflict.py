"""Construct believing oneself to discern conflict in fixed doctrinal content."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/clerical-practical-benefit-basis-v1.json'
LIBRARY='examples/v016/perceived-doctrinal-conflict.noema'
BASIS='data/perceived-doctrinal-conflict-basis-v1.json'
PREMISE='i[h[d] c]'
NAMES='personname i[a] bundlename i[a] religionname i[a] referencename i[d]'
NAME_ARGS='v personname v bundlename v religionname v referencename'
FIELDS='person a bundle a religion a reference d '+NAMES
PRIMITIVES={
    'h252z':('[a a a i[h[a a d] e] d d] c',['person','object','criterion','content','reference','point'],
        '本人は同じ固定基準でこの対象の内容に目を向け、検討や気付きによって、指定した閉じた内容関数へ同じ対象・比較基準・固定基準をこの順で渡す内容に当たる事柄をその対象の中に認めるという認識を得ている。単なる暗記・伝聞の再述・検討する予定・認識に至らない探索、対象を調べずに同じ内容を信じるだけの場合とは区別する。事柄の客観的な成立は合成側で別に要求する。過去に全く知らなかったこと、探索の所要時間、特定の証拠、完全な確信や意図的な探求は要求しない。内容記述はこの関係では実行しない。'),
}
MEANINGS={
    'r43l':'固定基準の同じ規定群にr42kで含まれる命題部分が少なくとも一つあり、その部分の同じh246e内容が同じ宗教基準のh246e内容へh252nの意味で抵触する内容。r42xの無抵触と同じ部分・内容・基準を用いる。本人の信念や発見はまだ要求しない。',
    'r43m':'規定群・宗教基準・固定基準の閉じた呼称から、r43lをそれらへ適用する閉じた内容記述を構成する。単なる原語の文字列ではなく、所属と内容間の抵触をNoemaで記述する。',
    'r43n':'同じ本人・規定群・宗教基準・固定基準について、r43lの抵触が同じ状況で実際に成り立ち、本人がその同じr43lの内容関数へ同じ規定群・宗教基準・固定基準を渡す事柄を認めるh252zが成立する内容。見いだすは事柄の成立と本人の認識の結合。外側の信念内へ置く場合、現実の発見や抵触は要求しない。',
    'r43o':'本人・規定群・宗教基準・固定基準の四閉じた呼称から、r43lの抵触内容を同じ本人が同じ規定群内に見いだすr43nの閉じた内容記述を構成する。自己に関する発見の内容を、r43mによる抵触の裸の命題と区別する。',
    'r43p':'四呼称が同じ本人・規定群・宗教基準・固定基準を指すことを確認し、本人がr43oの同じ自分の発見内容を真として受け入れるh233cを結ぶ。信じた内容の実際の抵触・認識・正当性や十分な確信を実行しない。',
    'r43q':'同じ四呼称から、r43oの内容を本人が真として受け入れるh233cを候補状況ごとに述べる閉じた前提関数を構成する。glaubteの仮定に渡す前提であり、候補範囲の選択や帰結自体はまだ供給しない。',
    'r43r':'四呼称と本人・規定群・宗教基準・固定基準の一致を要求し、同じ本人のr43qの信念前提と指定帰結をr42fの非空の全仮定候補へ結ぶ。前提だけが偽の候補や空範囲では成功せず、現実の前提の偽や現実の帰結は要求しない。',
}
LIMITS=[
    'u0012[4279,4407)の条件文へ向けた前提の依存群。das letztereは直前の内面的宗教に反する部分の存在、darinは同じ規定群を受ける。職務遂行不能・辞職義務・Dennと全文帰属は次に接続する。本文・確認文字数はまだ増やさない。',
    'glaubte ... zu findenは、本人がその対象を検討することで抵触を見いだすと考える自己に関する信念として読む。抵触の事実だけ、裸の抵触命題への信念だけ、外部の誰かの発見の伝聞、探索の将来計画だけとは区別する。DudenとIDSのfindenの認識・検討に関わる現代語義を補助にし、1784年の唯一の語義を証明したとはしない。',
    'r43nの内容は抵触の実在を含むが、その全体がh233cの信念対象に入る。誤った信念でも前提になり得る。信念を評価する際、h252n・r42k・h252zを外側で評価しない。抵触の証人となる部分の存在量化も閉じた信念内容の内側に置く。',
    '本人の四呼称は閉じたNoema記述で供給し、r43p/r43rで指示先を確認する。原文の同じ本人・規定群・基準を、コードの別の対象へすり替えない。本文への統合では先行文の同じ事例からこれらの引数を束縛する必要がある。',
    'findenの認識を、本人が以前は全く知らなかったことや、意図した検索の成功、完全な確信まで強めない。r43nは認識的な把握と内容の成立を分け、信念の下ではいずれも現実の事実にしない。',
    'r43rは帰結を受け取る接続であり、信念から職務遂行不能や辞職義務を導く公理ではない。次の統合では帰結の中で同じ職務・良心上の基準・実践可能性・退任の義務を構成する。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def identities():
    return ['e[v '+n+'][s[v '+code+']]' for n,code in (
        ('person','personname'),('bundle','bundlename'),('religion','religionname'),('reference','referencename'))]


def definitions():
    text='d r43l[bundle a religion a reference d] e[b point[g claim a['+both(
        'k r42k[v bundle v claim v reference]',
        'k h252n[k h246e[v claim v reference] k h246e[v religion v reference] v reference v point]')+']]].\n'
    text+='d r43m[bundle i[a] religion i[a] reference i[d]] i[e][o a[r[p r43l]][v bundle v religion v reference]].\n'
    text+='d r43n[person a bundle a religion a reference d] e[b point['+both(
        't[k r43l[v bundle v religion v reference]][v point]',
        'k h252z[v person v bundle v religion r[p r43l] v reference v point]')+']].\n'
    text+='d r43o['+NAMES+'] i[e][o a[r[p r43n]]['+NAME_ARGS+']].\n'
    found='k r43o['+NAME_ARGS+']'
    text+='d r43p['+FIELDS+' point d] c['+both(*identities(),'k h233c[v person '+found+' v point]')+'].\n'
    template='r[i[person a content i[e]][i[point d][k h233c[v person v content v point]]]]'
    text+='d r43q['+NAMES+'] '+PREMISE+'[o a['+template+'][v personname o r['+found+']]].\n'
    text+='d r43r['+FIELDS+' consequent h[d] c actual d] c['+both(*identities(),
        'k r42f[v person k r43q['+NAME_ARGS+'] v consequent v actual]')+'].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r42k','h246e','h252n','h233c','r42f']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='believed_self_discovery_of_fixed_doctrinal_conflict',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
