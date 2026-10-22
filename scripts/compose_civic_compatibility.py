"""Compose genuine or believed improvement and joint civil-order compatibility."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='data/monarchical-sentence-basis-v1.json'
LIBRARY='examples/v016/civic-compatibility.noema'
BASIS='data/civic-compatibility-basis-v1.json'
NAMES=('change','field','community','older','newer','standard')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
CMP_NAMES=('older','newer','field','standard')
CMP_ARGS=' '.join('v '+n for n in CMP_NAMES)
PRIMITIVES={
 'h26g6':('[a a a a a a d] c',list(NAMES)+['reference'],
   '同じ共同体・検討領域・固定基準で対象とする変更案又は変更の全範囲に属し、その変更が同じ領域のあり方を比較元から変更後へ移す内容と、両者のよさを比較する同じ評価基準に結ばれる。あり方は同じh246eの閉じたNoema内容で示す。改善するもの・誰かの賛同があるもの・実施可能なものだけを先に選別せず、検討すべき全変更を固定する。現に変更したこと、改善、規範的許容、他領域への影響は別に構成する。'),
 'h26g7':('[a a d] c',['field','community','reference'],
   '同じ共同体に関わる宗教的な理解・判断・実践と、その共同の営みや制度的なあり方を検討する領域。個人の信念の見直しと共同体の制度変更をともに含め、教会組織だけや現在の多数派の教えだけに限定しない。宗教内容の真理・改善・実施・公的承認は別である。'),
 'h26ha':('[a a a a d d] c',['standard','field','left','right','reference','assessment'],
   '固定した同じ評価基準で同じ領域の二つのあり方を比較し、この評価状況では左のよさが右に少なくとも劣らない。両対象の内容はh246eで明示し、規則・役割の構成だけでなく理解や個人の実践も比較できる。相互成立は同程度、双方不成立は比較不能であり未知と区別する。本人の人気投票や統治者の好みを評価基準へ暗黙に置換せず、実施済み・全観点での無損失・唯一正しい基準を含意しない。'),
 'h26hb':('[a a d] c',['order','community','reference'],
   'この秩序は同じ政治的共同体で人々の外的な共同生活を公的な拘束規則・権利関係・裁定と執行により組織する市民的な法秩序である。保持すべき条件は同じh26hcの全項目とh246eの内容で指定する。特定宗派の内面の真理や統治者個人の好みと同一視せず、現在のすべての制度細目を一字一句変えない条件を補わない。実際の条件充足と改善案との両立は別に構成する。'),
 'h26hc':('[a a d] c',['order','condition','reference'],
   '同じ固定基準の市民的秩序が成り立つための条件の完全な範囲に、この条件定式化が含まれる。全条件は同じh246eの閉じたNoema内容で与え、適合する条件だけへ事後選別しない。法律の条文が単に存在することと、そこで定めた秩序が機能する条件を区別し、空かどうかと全条件充足は合成側で調べる。'),
 'h26hd':('[a a d d] c',['change','order','reference','candidate'],
   '同じ変更と市民的秩序の併存を検討する、固定基準で相互に矛盾しない実践的な可能状況の完全な範囲。変更の対象・変更前後の内容・秩序の全条件と他の背景を保持し、変更や秩序を満たす候補だけに先に選別しない。各部分の別々の実現、実際の成立、単なる本人の信念候補や有限検査で観測された状況集合と同一視しない。'),
}
MEANINGS={
 'r5mw':'同じ共同体の宗教的な検討領域h26g7について、h26g6が固定する全変更候補と比較元・変更後・評価基準の対応。客観的改善、改善という信念、秩序との両立を範囲条件へ先取りしない。',
 'r5mx':'同じ比較元・変更後・領域・評価基準・固定基準について、両者の自己比較が成り立ち、変更後が比較元以上、逆は不成立という厳密な改善の内容。同程度・比較不能・自己比較の欠落を通さない。',
 'r5my':'正確な比較元・変更後・領域・評価基準の四対象列と固定基準をr5mxへ渡す内容族。信念と現実の改善に同じ内容を使える。',
 'r5mz':'同じ四対象と固定基準の閉じた呼称から、r5mxによる厳密な改善の閉じた内容記述を構成する。構成時に比較を実行せず、単なる候補名への賛同に縮めない。',
 'r5m2':'h223g/h223hが供給する四対象と固定基準の呼称が元の対象を指すことを確認する。未知や別対象の呼称を、改善と思われていない場合へ置換しないための妥当性条件。',
 'r5m3':'同じ人が、同じ四対象と基準を指す呼称で作ったr5mzの改善内容をh233cで真として受け入れている。客観的改善や現在の実施、全員一致、確信の無欠如は要求しない。',
 'r5m4':'同じ変更候補r5mwについて、客観的に厳密な改善r5mxであるか、ある人が同じ内容を改善だと受け入れるr5m3がある。包含的選言とし、両方の場合も、客観的には誤る信念だけの場合も含める。',
 'r5m5':'同じ共同体の市民的秩序h26hbと、その全条件h26hcが非空であることを確認する。条件充足や特定の変更案への好意をこの枠へ先取りしない。',
 'r5m6':'同じr5m5の秩序の全条件h26hcが、同じ固定基準のh246e内容として同じ一状況で成立する。条件ごとに別の状況を選ばない。',
 'r5m7':'同じ変更候補r5mwと秩序r5m5について、h26hdの同じ一候補で変更後のh246e内容と秩序の全条件r5m6が共に成立する。別々の充足例や、抵触が未発見なことだけで両立を補わない。',
 'r5na':'同じ変更・比較・共同体・秩序で呼称妥当性r5m2を先に確認し、真の改善又は改善という信念r5m4があるなら、同じ変更と秩序の両立r5m7を要求する。呼称誤りを前件の偽に隠さない。',
 'r5nb':'同じ共同体・秩序・固定基準の全変更候補r5mwについてr5naを要求する。評価点での真又は見かけの改善をすべて対象とし、各改善ごとに両立例を選べる。相互に排他的な全改善案の同時採択や現実の実施、君主の監督行為は要求しない。',
}
LIMITS=[
 '第十一文のalle wahre oder vermeinte Verbesserung mit der bürgerlichen Ordnung zusammen besteheに向けた依存群。変更の全候補、真の改善と改善という信念の区別、同じ市民的秩序との両立を構成する。君主の監督・不介入・臣民・救済目的・妨害防止・全文提示は残り、意味確認文字数を加算しない。',
 'Verbesserungはこの宗教上の文脈での理解・判断・実践・共同制度のあり方の改善として読む。教会の規則配置に限定した既存r36zをそのまま流用せず、同じ厳密比較の構造を一般の内容定式化へ広げる。原文が具体的な候補や唯一の評価基準を列挙したとはしない。',
 'wahreは固定された評価基準による実際の厳密な優越、vermeinteは同じ比較内容が人に真と受け入れられることとする。後者を必ず偽とする条件は加えず、oderを包含的に保つ。君主だけが改善と認めたものへ範囲を狭めない。',
 '信念の内容は既存h233cに同じr5mxの閉じた記述を渡す。既存h223g/h223hの呼称の指示先を確認し、不正な呼称を前件がないこととして全称条件から除外しない。この記述可能性の条件は形式化の契約であり、本人がNoemaの綴りを知るという心理要件ではない。',
 'bürgerliche Ordnungは公的法による外的共同生活の秩序と読む。実在の政権の全細目や多数派の宗教教義を無変更で残す条件とはしない。ただし秩序の具体的な全条件は閉じたNoema記述として与える責任があり、任意の空集合を秩序と称して通さない。',
 'zusammen bestehenは、同じ変更後のあり方と同じ秩序の全条件を一つの実践的可能状況でともに満たせるという明示読解。現在ともに成立すること、全可能状況での成立、変更案を全部一度に実施することとは分ける。君主がこの両立をどのように確保するかは次の監督構成で接続する。',
 '有限検査は構成と引数・量化・引用の作用を調べる。候補範囲や評価基準の歴史上の正当性、原文との全文同値、現実の全可能状況の完全列挙を証明しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    frame='k r5mw['+ARGS+' v reference]'
    text='d r5mw['+FIELDS+' reference d] c['+both('k h26g7[v field v community v reference]','k h26g6['+ARGS+' v reference]')+'].\n'
    cmp=lambda x,y:'k h26ha[v standard v field v '+x+' v '+y+' v reference v point]'
    text+='d r5mx[older a newer a field a standard a reference d] e[b point['+both(cmp('older','older'),cmp('newer','newer'),cmp('newer','older'),'u['+cmp('older','newer')+']')+']].\n'
    text+='d r5my[bindings j[a] reference d] e[b point['+bind(CMP_NAMES,'t[k r5mx['+CMP_ARGS+' v reference]][v point]')+']].\n'
    names=' '.join(n+'name i[a]' for n in CMP_NAMES)+' referencename i[d]'
    text+='d r5mz['+names+'] i[e][o a[r[p r5mx]]['+' '.join('v '+n+'name' for n in (*CMP_NAMES,'reference'))+']].\n'
    codes=' '.join('k h223g[v '+n+']' for n in CMP_NAMES)+' k h223h[v reference]'
    ids=['e[s[k h223g[v '+n+']]][v '+n+']' for n in CMP_NAMES]+['e[s[k h223h[v reference]]][v reference]']
    fields=' '.join(n+' a' for n in CMP_NAMES)+' reference d'
    text+='d r5m2['+fields+'] c['+both(*ids)+'].\n'
    text+='d r5m3[person a '+fields+' point d] c['+both('k aa[v person]','k r5m2['+CMP_ARGS+' v reference]',
        'k h233c[v person k r5mz['+codes+'] v point]')+'].\n'
    qualifies='x[t[k r5mx['+CMP_ARGS+' v reference]][v point]][g person a[k r5m3[v person '+CMP_ARGS+' v reference v point]]]'
    text+='d r5m4['+FIELDS+' reference d point d] c['+both(frame,qualifies)+'].\n'
    text+='d r5m5[order a community a reference d] c['+both('k h26hb[v order v community v reference]',
        'g condition a[k h26hc[v order v condition v reference]]')+'].\n'
    text+='d r5m6[order a community a reference d point d] c['+both('k r5m5[v order v community v reference]',
        'f condition a[y[k h26hc[v order v condition v reference]][t[s[k h246e[v condition v reference]]][v point]]]')+'].\n'
    joint='g candidate d['+both('k h26hd[v change v order v reference v candidate]',
        't[s[k h246e[v newer v reference]]][v candidate]',
        'k r5m6[v order v community v reference v candidate]')+']'
    text+='d r5m7['+FIELDS+' order a reference d] c['+both(frame,'k r5m5[v order v community v reference]',joint)+'].\n'
    text+='d r5na['+FIELDS+' order a reference d point d] c['+both('k r5m2['+CMP_ARGS+' v reference]',
        'y[k r5m4['+ARGS+' v reference v point]][k r5m7['+ARGS+' v order v reference]]')+'].\n'
    universal='y['+frame+'][k r5na['+ARGS+' v order v reference v point]]'
    for n in reversed(NAMES):universal='f '+n+' a['+universal+']' if n!='community' else universal
    text+='d r5nb[community a order a reference d] e[b point['+both('k r5m5[v order v community v reference]',universal)+']].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['aa','h233c','h223g','h223h','h246e']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='genuine_or_believed_improvement_jointly_compatible_with_civil_order',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
