"""Generalize fixed compacts to unending intervals and track human progress."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_fixed_religious_compact import NAMES,FIELDS,ARGS,CONTEXT,CTX,SEQ,HISTORY,ORDER

PARENTS=('data/fixed-religious-compact-basis-v1.json','data/provisional-order-sentence-basis-v1.json')
LIBRARY='examples/v016/persistent-compact-progress.noema'
BASIS='data/persistent-compact-progress-basis-v1.json'
PRIMITIVES={
 'h26e3':('[a d d d] c',['period','reference','candidate','point'],
   '固定した期間対象に、その同じ基準と候補履歴のこの点が含まれる。合意内容や結果の成否を評価する前に指定する完全な期間範囲であり、制度が続く点や改善のない点だけを集めない。有界の場合は既存h26exの開始以上終了未満に一致させ、終わりのない場合は開始から先の全履歴に一致させる。この対応、非空・連続性・開始点・終点の有無は合成側で検査する。'),
}
MEANINGS={
 'r5jc':'同じ期間対象の全点が完全な候補履歴内の非空の連続区間をなすことをtbで検査し、指定した開始点がその最小点であることを要求する。起点以前の点や途中の穴を許さず、この段階では終点の有無は決めない。',
 'r5jd':'同じ期間のr5hzの一意な端点と、開始以上終了未満の全履歴点にちょうど一致するh26e3を結ぶ。有界期間への旧構成と新しい範囲表現の明示的な対応であり、実施・許可を含まない。',
 'r5je':'同じr5jcの開始から先の全履歴点に期間範囲が一致し、同じ全履歴の将来に終点がないrbzを要求する。有限のh26ex端点指定との併存は拒否する。終点不明、有限の観測打切り、無限個の点を含むだけの有界期間とは区別する。',
 'r5jf':'同じ期間と開始について、有界のr5jdの終了があるか、終点のないr5jeがある。両形式とも同じ固定期間の全範囲を保つ。物理的な無限長の数値や、制度内容の実現は要求しない。',
 'r5jg':'共同体・制度・公衆・期間の正確な四対象列について、合意基準以後に始まるr5jfの全期間で、同じ制度配置と全人への公的問い直しの禁止r5h5が続く内容。有界部分は旧r5h6へ明示的な期間対応の下で一致し、終点のない場合も同じ内容族で表す。',
 'r5jh':'同じ宗教制度・公衆・期間について、一般化したr5jgを同じ束縛列と基準・候補・合意基準で対象に取るr5jaの共同合意。全当事者の同意は実行するが、引用された期間の存続・無限性・規制を実行しない。旧r5jbの引用記述を無断で同一視しない。',
 'r5ji':'有界期間の明示的対応r5jdと、同じ一人の完全な生涯内に端点を含めて収まるr5h2を結ぶ。一般化された期間範囲の下でauch nurの限定対象を特定する条件。人物が合意の当事者であることや一般命題への限定そのものはここでは述べない。',
 'r5jj':'同じ候補における人類h256mの通時的な全成員h246cを、aaの全人間とちょうど一致させる。現在生存者だけ、合意当事者、国民、特定集団へ縮めず、各点の生存は既存h256oで別に判定する。',
 'r5jk':'同じ期間の改善を比較する評価範囲。h26e3の全点に、有界の場合の同じ終了点を加える。制度の維持は終了直前まででも、終了点で得た改善をその期間の成果から落とさない。終点なしの場合は別の架空終点を追加しない。',
 'r5jl':'同じ有効な期間の評価範囲r5jkに属する厳密な前後点で、全人類を保つr5jjの下で、r5csの認識獲得・理由ある訂正・理由ある自己判断の進展の少なくとも一つがある。範囲と真偽評価を固定し、保持者の入替えだけを改善とせず、他の全項目の無損失も要求しない。',
 'r5jm':'同じ有効な期間の全評価点で全人類の非空性と判断評価の有効性r5cqを保ち、その全ての前後点にr5jlの改善がない内容。未評価や人類の絶滅を不毛さの成立にせず、途中の獲得と喪失を端点だけの比較で見落とさない。合意の原因性や後世への害はこの結果条件だけでは含意しない。',
}
LIMITS=[
 'u0013第八文の固定化の時間範囲と、その間の人類の改善の不在を構成する依存群。全文の不許可、同じ合意による原因性、消去への見立て、後世への害の様相、auch nur等の提示と全文通読は未接続で、意味確認文字数を増やさない。',
 '固定化は有界でも終点なしでも同じ期間対象で表す。有界では既存h26exとの完全一致、終点なしでは既存rbzと開始以後の全履歴への一致を要求する。履歴の完全性は意味規約を満たす入力の責任である。有限模型では終点なしの分岐は成立しない。',
 '有界の期間は開始を含み終了を含まない。人類の改善を比較する範囲には終了点を含める。終了点での改善を無視した不毛さの認定や、期間外の後日の改善を過去の成果へ算入することを避ける。',
 '人類の改善は、先行文の認識拡大・誤りの訂正・啓蒙進展の三つを引き継ぐ明示した読み。国民だけ又は現在の生存者だけへ対象を固定しない。全人間の通時的成員資格と各時点の生存を分け、既存の獲得・訂正・通常の理由ある自己判断の条件を保つ。',
 '不毛を同じ期間内に三種類の改善が一つもないという強い結果条件として構成する。比較対象の完全性、認識内容の真偽評価、判断基盤の有効性を明示入力で固定する。改善過程の一切の価値を一意に定義したものではない。因果的にこの結果を生むことと、その害の可能性は別に接続する。',
 '一般化後の合意は新しい閉じた内容族r5jgを用いる。旧r5h6との有界部分の内容一致は検査するが、内容族の記述そのものが同じという扱いはしない。以前の合意・判断記録と旧意味規約は変更しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    scope='i[at d][k h26e3[v period v reference v candidate v at]]'
    member=lambda at:'k h26e3[v period v reference v candidate v '+at+']'
    le=lambda a,b:'x[e[v '+a+'][v '+b+']][k ic[v '+a+' v '+b+' v candidate]]'
    pf='period a reference d candidate d';pa='v period v reference v candidate'
    text='d r5jc['+pf+' start d] c['+both('k tb['+HISTORY+' '+scope+' '+ORDER+']',member('start'),'f at d[y['+member('at')+']['+le('start','at')+']]')+'].\n'
    inside=both('k h257z[v reference v candidate v at]',le('start','at'),'k ic[v at v end v candidate]')
    text+='d r5jd['+pf+' start d end d] c['+both('k r5hz['+pa+' v start v end]','k r5jc['+pa+' v start]',
        'f at d[z['+member('at')+']['+inside+']]')+'].\n'
    tail=both('k h257z[v reference v candidate v at]',le('start','at'))
    text+='d r5je['+pf+' start d] c['+both('k r5jc['+pa+' v start]','k rbz['+HISTORY+' '+ORDER+' v start]',
        'f at d[z['+member('at')+']['+tail+']]','u[g first d[g last d[k h26ex['+pa+' v first v last]]]]')+'].\n'
    text+='d r5jf['+pf+' start d] c[x[g end d[k r5jd['+pa+' v start v end]]][k r5je['+pa+' v start]]].\n'
    lasting=both('k h26cv[v regime v community v reference v candidate v at]','k r5h5[v regime v community v audience v reference v at]')
    terms=both('k h257z[v reference v candidate v anchor]','k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'g start d['+both('k r5jf['+pa+' v start]',le('anchor','start'),'f at d[y['+member('at')+']['+lasting+']]')+']')
    text+='d r5jg[bindings j[a] '+CONTEXT+'] e[b point['+bind(NAMES,terms)+']].\n'
    text+='d r5jh[agreement a '+FIELDS+' '+CONTEXT+'] c['+both('k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'k r5ja[v agreement r[p r5jg] '+SEQ+' '+CTX+']')+'].\n'
    text+='d r5ji[person a '+pf+' start d end d] c['+both('k r5jd['+pa+' v start v end]','k r5h2[v person '+pa+' v start v end]')+'].\n'
    text+='d r5jj[candidate d] c[f person a[z[k h246c[k h256m[] v person v candidate]][k aa[v person]]]].\n'
    text+='d r5jk['+pf+' point d] c[x['+member('point')+'][g start d[k r5jd['+pa+' v start v point]]]].\n'
    valid='g start d[k r5jf['+pa+' v start]]'
    gains=both(valid,'k r5jj[v candidate]','k r5jk['+pa+' v first]','k r5jk['+pa+' v last]','k ic[v first v last v candidate]',
        'k r5cs[k h256m[] v reference v assessment v candidate v first v last]')
    text+='d r5jl[period a reference d assessment d candidate d first d last d] c['+gains+'].\n'
    loss=both(valid,'k r5jj[v candidate]','f at d[y[k r5jk['+pa+' v at]][k r5cq[k h256m[] v reference v candidate v at]]]',
        'u[g first d[g last d[k r5jl[v period v reference v assessment v candidate v first v last]]]]')
    text+='d r5jm[period a reference d assessment d candidate d] c['+loss+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5hz','r5h2','r5h5','r5h6','r5ja','h26cv'],['rbz','r5cs','r5cq','h256m'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='bounded_or_unending_compact_and_complete_human_progress_interval',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
