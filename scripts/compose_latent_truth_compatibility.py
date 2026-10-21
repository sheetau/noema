"""Compose possible latent truth and absence of opposition to inward religion."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/clerical-report-forecast-basis-v1.json','data/doctrinal-statutes-basis-v1.json')
LIBRARY='examples/v016/latent-truth-compatibility.noema'
BASIS='data/latent-truth-compatibility-basis-v1.json'
PRIMITIVES={
    'h252k':('[a a a i[e] d d] c',['person','container','part','content','reference','point'],
        '同じ固定基準の容れ物・命題部分・閉じた内容について、その内容がそこで真理を表すということは、この人物の認識上の位置からは明らかになっておらず、解釈・吟味によって取り出す余地がある。物理的な遮蔽、単に本人が賛同しないこと、意図的な隠蔽者の存在とは分ける。部分の所属と真理は別条件であり、実際の発見や将来の認識を要求しない。'),
    'h252l':('[a a d d d] c',['person','container','reference','actual','candidate'],
        '同じ本人・内容の容れ物・固定基準について、評価点の検討で利用できる根拠から排除されていない場合として採る候補状況の範囲。真理や抵触の結果を見て選別せず、同じ容れ物の内容・所属の基準を保持する。現実の履歴、全論理的可能世界、数値確率、原文の真理を保証する範囲とはしない。'),
    'h252m':('[a a d] c',['standard','religious_subject','reference'],
        'この定式化は、同じ宗教上の主題について、内的な信仰と良心に即した道徳的態度・義務の承認に関わる基準を表す。外的な礼拝形式や教会の制定規則への適合だけとは区別する。具体的な原則は同じh246eの閉じたNoema内容で示し、特定教派・本人の実際の信仰・神の存在をこの位置付けから導かない。'),
    'h252n':('[i[e] i[e] d d] c',['content','standard_content','reference','point'],
        '同じ固定基準の解釈を保つこの評価状況で、第一の閉じた内容を是とすることは、第二の閉じた内容が定める原則・要求に反し、両者をその実践上の基準の下でともに認めることができない。第一内容の単なる未立証・現実の不成立、違和感、制度上の未採用、観測範囲に共同充足例がないだけの場合とは区別する。両内容の実際の真理、本人の判断や発見は別である。'),
}
MEANINGS={
    'r42t':'同じ固定基準の規定群にr42kで含まれる命題部分があり、その同じh246eの内容が評価状況で真で、本人に対してh252kの意味でまだ明らかになっていない。部分の所属・真理・認識上の隠れ方を別々に結ぶ。',
    'r42u':'同じ本人・規定群・固定基準・評価点のh252lの候補のどれかでr42tの隠れた真理がある。現在の真理や、全体の真理・十分な賛同を含意しない。',
    'r42v':'同じh252lの範囲が非空で、その全てにr42tの隠れた真理がない。全く可能性がないという限定された認識上の読み。空の範囲から不可能性を成立させない。',
    'r42w':'同じ候補範囲が非空で、r42vの全排除が成り立たない。nicht ganz unmöglichの読みとして否定の作用域を保持し、この二値解釈ではr42uと一致する。未知入力を可能性へ変換せず、弱い確率値や現実の真理は補わない。',
    'r42x':'同じ規定群に固定基準で含まれる部分のどれも、同じ基準で指定した内面の宗教の内容と評価状況でh252nの意味で対立しない。既存rgvを用い、所属と双方の閉じた内容を固定する。調査行為の成功や全体の共同充足可能性の証明とはしない。',
    'r42y':'同じ宗教主題h245z・内面的な基準h252mを要求し、本人の同じ非空のh252lの全場合でr42xの抵触不在が成立する。auf alle Fälleを同じ検討範囲全体への読みとして構成し、抵触を確信していないだけの場合と区別する。',
    'r42z':'同じ本人・規定群・宗教主題・内面的な基準・固定基準・評価点について、隠れた真理の全排除の否定r42wと全場合の抵触不在r42yを合わせる。真理の可能性だけから無抵触や引受けの許容を導かない。',
}
LIMITS=[
    'u0012[3899,4278)のweil以下に向けた依存群。引受け可能性の理由としてのweil、aber/wenigstens/dochの対照と焦点、全実益、本文への著者帰属は未統合。確認文字数を増やさない。',
    'verborgen lägeを、規定群に含まれる命題部分の真理が本人には明らかでないという認識上の読みで扱う。物理的位置や意図的な隠蔽者を補わない。Adelungの知識から隠れる語義を参照する。',
    'nicht ganz unmöglichは同じ検討範囲で隠れた真理の可能性を全排除できないという読み。程度語を数値確率や中間真理値へ置き換えず、否定と空範囲を別に扱う。比較範囲の正当性は明示した解釈入力である。',
    '内面の宗教は内的な信仰・良心に即した道徳的態度の基準として読む。Adelung Religion、1776年の書簡AA X 192、後年のAA VI 105を比較するが、1793年の宗教論全体を1784年へ遡及せず、あらゆる宗教や唯一の作者意図の定義とはしない。',
    'angetroffen wirdはここでは当該内容の中に該当する抵触が含まれないという状態の読み。実際に網羅的な探索を終えた行為を要求しない。後続のglaubte ... zu findenは非事実的な判断として別に接続する。',
    'h252nは明示した内容と原則の実践的な抵触であり、有限の可能世界一覧の無交差rgzをそのまま普遍的な抵触とみなさない。部分ごとの無抵触から、規定群全体の共同充足可能性を導かない。',
    '全場合は真理の評価と同じ固定された検討範囲に限る。実際の全世界・全人の信仰へ無条件に拡張せず、良心上の許容h252jや職務遂行可能性をこの連言だけで成立させない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    code='k h246e[v claim v reference]'
    text='d r42t[person a bundle a reference d point d] c[g claim a['+both(
        'k r42k[v bundle v claim v reference]','t[s['+code+']][v point]',
        'k h252k[v person v bundle v claim '+code+' v reference v point]')+']].\n'
    fields='person a bundle a reference d actual d';args='v person v bundle v reference v actual'
    selected='k h252l['+args+' v point]';latent='k r42t[v person v bundle v reference v point]'
    nonempty='g point d['+selected+']'
    text+='d r42u['+fields+'] c[g point d['+both(selected,latent)+']].\n'
    text+='d r42v['+fields+'] c['+both(nonempty,'f point d[y['+selected+'][u['+latent+']]]')+'].\n'
    text+='d r42w['+fields+'] c['+both(nonempty,'u[k r42v['+args+']]')+'].\n'
    clashes='i[claim a standard a point d][k h252n[k h246e[v claim v reference] k h246e[v standard v reference] v reference v point]]'
    text+='d r42x[bundle a religion a reference d point d] c[k rgv[v bundle v religion v reference v point p r42k '+clashes+']].\n'
    fields='person a bundle a subject a religion a reference d actual d'
    text+='d r42y['+fields+'] c['+both('k h245z[v subject v reference]',
        'k h252m[v religion v subject v reference]',nonempty,
        'f point d[y['+selected+'][k r42x[v bundle v religion v reference v point]]]')+'].\n'
    text+='d r42z['+fields+'] c['+both('k r42w['+args+']',
        'k r42y[v person v bundle v subject v religion v reference v actual]')+'].\n'
    return text


def build():
    old,statutes=parents();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['rgv','h245z']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(statutes.document,['r42k','h246e']):
        n=d['name'];e=statutes.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(c.entries) for c in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='possible_latent_truth_and_scoped_inward_religious_compatibility',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
