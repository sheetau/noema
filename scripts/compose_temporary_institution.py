"""Connect one enactment, its determinate short term and continuous public freedom."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/legislative-touchstone-basis-v1.json','data/institutional-criticism-basis-v1.json')
LIBRARY='examples/v016/temporary-institution.noema'
BASIS='data/temporary-institution-basis-v1.json'
NAMES=('actor','people','community','law','regime','activity')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d candidate d start d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference v candidate v start'
FRAME='community a regime a reference d candidate d start d end d'
FRAME_ARGS='v community v regime v reference v candidate v start v end'
HISTORY='i[point d][k h257z[v reference v candidate v point]]'
ORDER='i[first d last d][k ic[v first v last v candidate]]'
CONTENT='k r5fc[v community v regime v reference v candidate]'
PRIMITIVES={
 'h26cx':('[a d d d d] c',['activity','reference','candidate','start','end'],'この同じ行為に属する決定が、その候補経過で開始から終了までの期限を指定する。期限は導入時の決定内容に含まれ、後から成功した範囲だけを切り出すものではない。日付又は同じ経過で終点を一意に定める条件で指定できるが、単なるいつか・無期限・延長し続ける終点ではない。行為の現実の生起、履歴への所属、前後関係、期間の短さやその間の成立内容は別に検査する。'),
 'h26cy':('[a a d d d d] c',['community','regime','reference','candidate','start','end'],'同じ共同体の同じ制度の暫定的な維持を評価する固定基準に照らし、この候補経過の開始から終了までの時間的長さが短い。短長の比較尺度と許容幅は固定基準に属し、許可・実行成功・洞察到達に合わせて広げない。点の個数や語数ではなく時間の長さの文脈的比較であり、原文にない日数・数値の閾値は補わない。期限が指定されること、順序、制度の維持とは別の関係である。'),
 'h26cz':('[a a a d d d] c',['activity','regime','community','reference','candidate','point'],'この同じ行為が、この候補経過のこの点で、指定された宗教上の制度配置を同じ政治的共同体の運用される秩序として導入する制度的な働きをする。法の採択と別行為の効果、単に既存の制度が同時に存続すること、目的として考えるだけの場合とは区別する。全ての構成要素の歴史上初の発明や、以前の同じ教えの不在は要求しない。行為の生起、法の条項状態、以後の存続・正当性は別に結ぶ。'),
}
MEANINGS={
 'r5fd':'同じ固定基準・候補経過の完全な履歴h257z/icがtaの厳密全順序をなし、開始と終了がともにその履歴に属し、開始が終了より厳密に先である非零の有界期間。外部点、逆転、循環、欠けた順序、瞬間だけの空期間を拒む。離散時間や終点後の廃止は要求しない。',
 'r5fe':'同じr5fdの期間が同じ導入行為の決定で指定されh26cx、その同じ期間が固定基準で短いh26cy。順序だけから短さを導かず、単に短いだけで一定の期限が定まっているとしない。',
 'r5ff':'同じ主体・人民・共同体・法・活動・基準・候補・開始点について、全条項を含む公的採択r5ek、その共同体の宗教上の配置h26cs、その同じ行為による同じ制度の導入h26czを結ぶ。主体を人民へ束縛すれば自己賦課の導入例となるが、この定義自体は主体一般である。',
 'r5fg':'同じr5fdの期間の開始を含み終了を含まない全履歴点に、同じ制度・共同体・基準・候補のr5fc、すなわち制度存続と各点の全市民の書面批評の自由を要求する。都合のよい点の部分集合へ縮めず、開始時だけの許可や別制度・別経過の維持では満たさない。終点自体とその後の継続・廃止は決めない。',
 'r5fh':'同じ採択活動による制度導入r5ffと、その活動の指定した短い期間r5fe、その全期間の同じ制度と全市民の批評の維持r5fgを結ぶ。一つの候補の中での内容であり、現実の導入・規範的許可・目的・期待・洞察到達をこの連言から追加しない。',
 'r5fi':'同じr5fhの指定期間の終了が、渡された同じ到達内容の開始以後の最初の成立点であることをrkhで結ぶ。制度と批評はそこまで維持され、未到達のまま無期限に続くrkjの分岐はない。具体的な洞察内容は呼出側で与え、全候補や現実で到達するという予言にはしない。',
}
LIMITS=[
 'u0013第七文[1437,2309)の制度導入・一定の短い期間・全期間の存続と批評の依存群。全文の可能性・期待・目的・洞察・保護・非妨害と談話帰属は未接続で、意味確認文字数は加算しない。',
 '法を採択して一定の秩序を導入するという読解に向け、同じ採択行為の制度的効果を別に結ぶ。単に法の成立と宗教制度の存在を並べない。新しい制度配置の導入を要求するが、教えや規律が全てそれまで存在しなかったとはしない。',
 'bestimmte kurze Zeitの一定性を決定内容中の期限指定、短さを固定した文脈的時間比較として分ける。原文は日数や時計尺度を指定しないため数値化しない。この二つの外部入力だけへ文全体の真偽を預けず、履歴・非零の期間・同一行為・全期間の維持はNoemaで構成する。',
 '維持の期間は開始を含み終了を含まない。bisの到達点での瞬間的な継続と廃止は原文から一意に決まらないため要求しない。終了後も同じ制度が続くことは禁止しない。指定期限は固定の日付又は終了を一意に定める条件を許すが、事後的な短い成功区間への切詰めは認めない。',
 'r5fhは期間内の維持だけであり、洞察が到達しない模型でも成立し得る。r5fiは同じ有界期間の終点で初めて到達する強い構成である。全文では仮定の可能な経過の中でr5fiに具体的な洞察・提案可能性を渡す予定であり、現実の将来で必ず洞察が実現するとは読まない。弱いuntilだけで短期性を失う構成は使わない。',
 '終点が最初の成立点となるrkhの制限を継承する。稠密時間でも利用できるが、成立点に最小点がない開いた到達集合はこの形では満たさない。区間内の完全な履歴と期限指定・短長比較の供給は解釈入力の責任で、有限模型の通過はその現実的網羅性の証明ではない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5fd[reference d candidate d start d end d] c['+both('k ta['+HISTORY+' '+ORDER+']',
        'k h257z[v reference v candidate v start]','k h257z[v reference v candidate v end]',
        'k ic[v start v end v candidate]')+'].\n'
    period='k r5fd[v reference v candidate v start v end]'
    text+='d r5fe[activity a '+FRAME+'] c['+both(period,
        'k h26cx[v activity v reference v candidate v start v end]','k h26cy['+FRAME_ARGS+']')+'].\n'
    text+='d r5ff['+FIELDS+'] c['+both('k r5ek[v actor v people v community v law v activity v reference v candidate v start]',
        'k h26cs[v regime v community v reference]','k h26cz[v activity v regime v community v reference v candidate v start]')+'].\n'
    inside=both('k h257z[v reference v candidate v point]',
        'x[e[v start][v point]][k ic[v start v point v candidate]]','k ic[v point v end v candidate]')
    text+='d r5fg['+FRAME+'] c['+both(period,'f point d[y['+inside+'][t['+CONTENT+'][v point]]]')+'].\n'
    text+='d r5fh['+FIELDS+' end d] c['+both('k r5ff['+ARGS+']',
        'k r5fe[v activity '+FRAME_ARGS+']','k r5fg['+FRAME_ARGS+']')+'].\n'
    text+='d r5fi['+FIELDS+' end d milestone e] c['+both('k r5fh['+ARGS+' v end]',
        'k rkh['+HISTORY+' '+ORDER+' v start '+CONTENT+' v milestone v end]')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5ek','ta','h257z','ic','rkh'],['r5fc','h26cs'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_enactment_short_term_and_continuous_institutional_criticism',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
