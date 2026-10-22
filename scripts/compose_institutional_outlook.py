"""Separate an introduction purpose from a figurative outlook toward improvement."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_temporary_institution import FIELDS,ARGS

PARENT='data/temporary-institution-basis-v1.json'
LIBRARY='examples/v016/institutional-outlook.noema'
BASIS='data/institutional-outlook-basis-v1.json'
FAMILY='i[h[j[a] d d d] e]'
EXPECTATION_FAMILY='i b[h[j[a] d d d] e]'
CONTEXT='reference d candidate d anchor d'
CONTEXT_ARGS='v reference v candidate v anchor'
STANCE='actor a activity a community a regime a '+CONTEXT
STANCE_ARGS='v actor v activity v community v regime '+CONTEXT_ARGS
PURPOSE_NAMES=('activity','community','regime')
OUTLOOK_NAMES=('people','community','law')
PRIMITIVES={
 'h26c2':('[a a a d] c',['left','right','community','reference'],'同じ共同体の宗教上の共同行為を規律する公的な法を比較するとき、固定した評価基準に照らして左の法のよさが右に少なくとも劣らない。規律の内容の改善という本文の文脈で比較し、幸福量・多数の好み・現行権力の承認・唯一の真の宗教へ置き換えない。同じ二対象の比較尺度を反対向きでも保ち、改善成功に応じて変えない。法の規律の成立と本人の期待は別条件である。'),
 'h26c3':('[a a '+FAMILY+' j[a] d d d] c',['actor','activity','target','bindings','reference','candidate','anchor'],'同じ行為主体が、同じ活動の計画又は遂行において、渡された閉じた内容族を同じ順序付き個体列・固定基準・候補経過・起点へ適用した内容を達成目標として採用する。hztlの目的志向と同じ区別を保ち、状況を個体へ符号化せず型付き引数で固定する。活動の生起、目標の真理・成功・実現可能性、唯一の動機、全成員の個別の心理的同意は要求しない。'),
 'h26c4':('[a a '+EXPECTATION_FAMILY+' j[a] d d d] c',['actor','activity','target','bindings','reference','candidate','anchor'],'同じ主体が、同じ活動に関わるこの起点で、指定内容の到来を見込み待ち受ける将来志向の態度を持つ。内容は閉じた内容族と同じ個体列・固定基準・候補経過・起点で明示する。単なる願望、起きてもよいという許可、確実な知識、到来の現実の成立とは区別し、数値確率や全可能世界での成立は要求しない。集団へ帰属する場合も全成員の内心の一致は補わない。'),
}
MEANINGS={
 'r5fj':'同じ共同体の公的な法として元の法と別の法を分類し、固定基準で双方の自己比較と、新しい法が元の法以上・逆は不成立という厳密な改善を要求する。r5ejで同じ完全な人民に対する改善法の非空の全条項の規律が同じ点に成立する。単なる別名・同程度・比較不能・悪化では足りず、元の法の完全な廃止や特定教派は要求しない。',
 'r5fk':'正確な人民・共同体・元の法の三個体列と基準・候補・起点から、その候補の完全な順序履歴に属する起点より後の点でr5fjの改善法の全条項の規律が成立するという時間内容を作る。改善法は引用した内容の内側で存在量化し、期待する時点に特定の後継法が成立していることを要求しない。',
 'r5fl':'正確な活動・共同体・制度の三個体列と基準・候補・起点から、同じ有効な履歴の起点以後に、その同じ活動が生起し、同じ宗教制度を導入して実施状態にする内容を作る。法の採択資格や全条項はこの目的内容へ重ねず、実際の採択は外側で別に結ぶ。',
 'r5fm':'同じ主体・活動が、同じ活動・共同体・制度の三個体列と同じ基準・候補・起点によるr5flを目的として採用する。目的を引用したまま扱い、たまたま制度が導入されたことから目的を導かない。',
 'r5fn':'同じ主体・活動が、同じ人民・共同体・元の法の三個体列と同じ基準・候補・起点によるr5fkを期待する字義的な描写。本文のgleichsamに対応する見立ての描写側に使う部品であり、暫定的な制度を実施する内容そのものには連言しない。',
 'r5fo':'同じ主体・人民・共同体・法・制度・採択活動・基準・候補・開始と終了について、r5fhの一定の短期の制度導入と批評の維持に、同じ開始を起点とするr5fmの導入目的を加える。期待の字義内容r5fn、よりよい制度の実現、全人民の一致した内心は要求しない。',
 'r5fp':'同じr5foに、指定した到達内容が同じ期限で初めて成立するr5fiを接続する。短期・採択・導入・目的・継続・到達の各条件を同じ候補と同じ活動へ保持する。具体的な洞察内容と全文の可能性・談話帰属は呼出側に残る。',
}
LIMITS=[
 'u0013第七文[1437,2309)の期待と導入目的の依存群。um eine gewisse Ordnung einzuführenは同じ採択行為による同じ宗教上の制度の導入目的と読む。一定の秩序という不定の対象は全文の量化で指定し、特定教派の固有名を補わない。',
 'eines bessernの省略された対象を、直前のein solches Gesetzを受けるよりよい法と読む。Ordnungは女性名詞であり、einesの形と直前の中性名詞Gesetzからこの照応を採る。これは文脈と語形に基づく明示読解で、法と制度配置を同一個体に潰さない。よりよさは固定文脈での厳密な比較として分け、評価基準をこの語だけから一意に決定したとはしない。',
 'gleichsam in der Erwartungは暫定制度を、よりよい法を待つものになぞらえる挿入的な提示と読む。その字義的な期待内容をr5fnへ構成し、実際の全市民の心理状態としてr5fo/r5fpへ連言しない。見立てと同じ本文対象・著者の対応は全文統合で別に接続する必要がある。',
 '期待は同じ主体・活動についての将来志向の態度として意味を明示する。旧riの選んだ全予想候補での成立という確信的なモデルを、この挿入句にそのまま課さない。期待内容の未来性・改善比較・実施対象はNoemaで構成するが、心理機構や期待の正当性の一般理論を証明するものではない。',
 '目的と期待の内容族は、個体列と三つの状況引数を分ける。目的は段階0、全条項を評価するr5ejを含む期待対象は段階1の閉じた内容族を引用し、基準・候補・起点の値を個体に偽装したり、実行時に文字列の引用を生成したりしない。態度の成立から引用内容を実行しない。',
 '目的の実現と導入事実は論理的に別である。本文の仮定候補ではr5fhが実際の導入を別途要求し、r5fmは同じ導入活動の目的を要求する。改善法の到来は目的内容に混ぜず、終点で旧制度が廃止される条件も追加しない。',
 '公的洞察・確証・共同提案に足りる程度、保護・非妨害、聖職者への取り立て、可能性・wohl・Nun・gleichsamの談話帰属と全文通読は残る。確認済み文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    text='d r5fj[people a community a law a reference d candidate d point d] c[g better a['+both(
        'u[e[v better][v law]]','k h26ca[v law v community v reference]','k h26ca[v better v community v reference]',
        'k h26c2[v law v law v community v reference]','k h26c2[v better v better v community v reference]',
        'k h26c2[v better v law v community v reference]','u[k h26c2[v law v better v community v reference]]',
        'k r5ej[v people v community v better v reference v point]')+']].\n'
    history='i[at d][k h257z[v reference v candidate v at]]';order='i[first d last d][k ic[v first v last v candidate]]'
    valid=both('k ta['+history+' '+order+']','k h257z[v reference v candidate v anchor]','k h257z[v reference v candidate v point]')
    future=both(valid,'k ic[v anchor v point v candidate]','k r5fj[v people v community v law v reference v candidate v point]')
    text+='d r5fk[bindings j[a] '+CONTEXT+'] e[b point['+bind(OUTLOOK_NAMES,future)+']].\n'
    intro=both(valid,'x[e[v anchor][v point]][k ic[v anchor v point v candidate]]',
        'k h26cs[v regime v community v reference]','k dg[v activity v point]',
        'k h26cz[v activity v regime v community v reference v candidate v point]',
        'k h26cv[v regime v community v reference v candidate v point]')
    text+='d r5fl[bindings j[a] '+CONTEXT+'] e[b point['+bind(PURPOSE_NAMES,intro)+']].\n'
    seq='l[a][v activity v community v regime]'
    text+='d r5fm['+STANCE+'] c[k h26c3[v actor v activity r[p r5fl] '+seq+' '+CONTEXT_ARGS+']].\n'
    text+='d r5fn[actor a activity a people a community a law a '+CONTEXT+'] c[k h26c4[v actor v activity r b[p r5fk] l[a][v people v community v law] '+CONTEXT_ARGS+']].\n'
    purpose='k r5fm[v actor v activity v community v regime v reference v candidate v start]'
    text+='d r5fo['+FIELDS+' end d] c['+both('k r5fh['+ARGS+' v end]',purpose)+'].\n'
    text+='d r5fp['+FIELDS+' end d milestone e] c['+both('k r5fo['+ARGS+' v end]','k r5fi['+ARGS+' v end v milestone]')+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r5fh','r5fi','r5ej','h26ca','h26cs','h26cv','h26cz','dg','ta','h257z','ic']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='same_introduction_purpose_and_separate_figurative_expectation',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
