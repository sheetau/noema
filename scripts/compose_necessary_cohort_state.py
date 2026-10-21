"""Compose a later cohort condition and the necessity of blocked progress in it."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/covenant-nullity-basis-v1.json','data/cohort-progress-options-basis-v1.json','data/epoch-undertakings-basis-v1.json')
LIBRARY='examples/v016/necessary-cohort-state.noema'
BASIS='data/necessary-cohort-state-basis-v1.json'
PRIMITIVES={
 'h26al':('[a a d] c',['condition','aspect','reference'],'同じ固定基準で、この状態を構成する条件項目の全範囲にこの項目が含まれる。人々の置かれる制度的・実践的な条件の構成を指定する。進展不能という結果を見て項目を除かず、項目名だけで状態の成立を述べない。各項目の内容はh26amで別に与える。'),
 'h26am':('[a a d d] e',['aspect','group','reference','candidate'],'同じ条件項目が、指定した同じ集団・固定基準・候補経過について要求する状態の命題内容。Noemaの内容として与え、原文の単語や状態名だけで代用しない。項目が条件一覧にあることと、その内容が評価点で真であることを分ける。'),
 'h26an':('[a a d d d d] c',['condition','group','reference','base','start','candidate'],'同じ状態・集団・固定基準・基準経過・評価点について、状態からの帰結を比較する全候補経過にこの経過が含まれる。状態の構成と対象者の同定、評価時点までの背景を保ち、状態の成立や進展不能の真偽で候補を事後選別しない。状態が成り立たない比較候補も許す。基準経過自体の包含は合成側で確認する。'),
 'h26ao':('[d d d] d',['base','start','candidate'],'基準経過のこの評価点に対応する、指定比較候補内の評価点。候補の別の時期へ移して不能性を作らず、比較する同じ状態の評価位置を保持する。基準経過自身への対応が元の点であることは合成側で確認する。'),
 'h26ap':('[a a d d d] c',['group','method','reference','candidate','start'],'この同じ集団・固定範囲・候補経過・開始点で、構成員が個別に又は共同で取り得る学習・研究・検討・改訂の全方法に、この方法が属する。実際に選んだ方法、成功する方法、集団として公式決定した方法だけへ狭めない。'),
 'h26aq':('[a a d d d d] c',['group','method','reference','candidate','start','end'],'同じ集団・方法・固定範囲・候補経過・開始点から生じ得る全結果状況の一つ。日付だけでなく可能な結果状況を指定し、成功と失敗の両方を含める。実際の実現や成功保証を含意しない。その結果への経過は既存h26akで同じ方法へ結ぶ。'),
 'h26ar':('[d] d',['reference'],'固定した認識対象範囲において、認識内容の真偽を前後・候補の間で比較する同じ評価状況。判断領域を指定する参照と真偽評価の役割を区別し、得られた結果に合わせて評価状況を替えない。内容の時刻・指示対象は既存h26aeの規約で固定する。'),
}
MEANINGS={
 'r5cx':'固定した同じ状態の条件項目が非空で、その全項目のh26amの内容が、同じ集団・基準・候補経過の指定点で成り立つ。状態への命名や条件の列挙だけを、その状態の実現としない。',
 'r5cy':'同じ集団・固定範囲・真偽評価・候補経過・開始点の方法h26apと結果h26aqを、同じ引数でr5cwの三種類の進展不能へ渡す。別の候補や開始点の選択肢を借りない。',
 'r5cz':'指定点で同じ状態r5cxが成り立ち、基準経過が比較候補に含まれ自身への対応点が元の点である。その上で既存rjkにより、全比較候補で同じ状態が成り立つなら、その対応点でr5cyの進展不能が成り立つ。状態の実例を欠く空虚な条件だけで達成としない。',
 'r5c2':'同じ前後時代・集団・合意についてr5bzを保ち、先行時代の合意基準より後の後続時代内の点で、同じ後続集団がr5czの必然的な進展不能を伴う状態にある。各経過に成立点があればよく、全候補に同一の日付、永続性、以前は可能だったという逆の事実は加えない。',
 'r5c3':'先行集団・後続集団・先行時代・後続時代・合意・状態の正確な六個体列と固定基準をr5c2へ結び、真偽評価h26arを固定した結果内容を返す。目的として引用できる状態の達成内容であり、因果・目的採用・合意形成・正当性そのものはまだ述べない。',
}
LIMITS=[
 'Zustandは同じ集団が置かれる条件項目の非空の全構成として読む。条件の内容はNoemaで指定し、状態という名や不能性の単一フラグで全文を置き換えない。具体的な合意の結果内容を束縛する段階で同じ条件を保つ。',
 'mussは、同じ状態が成り立つ比較候補では三種類の進展不能が成立するという、状態に条件づけられた必然性として読む。比較候補は非空で基準経過自身を含み、実際の評価点で状態が成り立つことも要求する。状態がない候補で不能性を強制しない。',
 '候補・対応点の選定と背景の保存は解釈入力であり、有限模型から現実の全可能性を網羅したとはしない。比較候補の条件と、各方法の結果への継続h26akを区別し、同じ候補経過に結んだ方法・結果をr5cwへ渡す。',
 'werdenは先行時代の合意基準より後の後続時代内で成立するという将来の位置付けを採る。成立前に進展可能だったこと、不能性が永久に続くこと、全候補が同じ日付に至ることはこの一文から追加しない。',
 'r5c3は目的に使う達成内容を構成する段階。実際の因果、同じ合意の共同目的への採用、当事者の同じ相互宣誓行為、条項内容との接続は別に必要。目的を述べる際にこの達成内容を実行して成功を前提にしない。',
 'kann nichtの規範的否認、括弧の重要性・überhauptの総括・共謀的提示・全文帰属と通読判断は残る。本文99主張と既存判断を保持し、確認済み文字数を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    member='k h26al[v condition v aspect v reference]'
    text='d r5cx[condition a group a reference d candidate d point d] c['+both('g aspect a['+member+']',
        'f aspect a[y['+member+'][t[k h26am[v aspect v group v reference v candidate]][v point]]]')+'].\n'
    available='i[owner a method a start d][k h26ap[v owner v method v reference v candidate v start]]'
    outcomes='i[owner a method a start d end d][k h26aq[v owner v method v reference v candidate v start v end]]'
    text+='d r5cy[group a reference d assessment d candidate d point d] c[k r5cw[v group v reference v assessment v candidate v point '+available+' '+outcomes+']].\n'
    at='k h26ao[v candidate v point v branch]'
    subject='b branch[k r5cy[v group v reference v assessment v branch '+at+']]'
    condition='b branch[k r5cx[v condition v group v reference v branch '+at+']]'
    candidates='i[base d branch d][k h26an[v condition v group v reference v base v point v branch]]'
    text+='d r5cz[condition a group a reference d assessment d candidate d point d] c['+both(
        'k r5cx[v condition v group v reference v candidate v point]',
        'k h26an[v condition v group v reference v candidate v point v candidate]',
        'e[k h26ao[v candidate v point v candidate]][v point]',
        'k rjk['+subject+' '+condition+' v candidate '+candidates+']')+'].\n'
    fields='firstgroup a nextgroup a earlier a later a agreement a condition a reference d assessment d candidate d'
    pair='v firstgroup v nextgroup v earlier v later v agreement v reference v candidate'
    attained='g point d['+both('k h26ab[v later v reference v candidate v point]',
        'k ic[k h254z[v agreement] v point v candidate]',
        'k r5cz[v condition v nextgroup v reference v assessment v candidate v point]')+']'
    text+='d r5c2['+fields+'] c['+both('k r5bz['+pair+']',attained)+'].\n'
    text+='d r5c3[bindings j[a] reference d] e[b candidate['+bind(('firstgroup','nextgroup','earlier','later','agreement','condition'),
        'k r5c2[v firstgroup v nextgroup v earlier v later v agreement v condition v reference k h26ar[v reference] v candidate]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['rjk'],['r5cw'],['r5bz','h26ab','h254z','ic'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='later_cohort_condition_and_conditioned_necessity_of_inability',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
