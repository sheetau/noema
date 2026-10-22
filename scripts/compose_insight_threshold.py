"""Compose proposal-relative epistemic sufficiency and the same bounded until."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_temporary_institution import FIELDS as INTRO_FIELDS,ARGS as INTRO_ARGS

PARENTS=('data/legislative-touchstone-basis-v1.json','data/public-insight-basis-v1.json','data/protective-petition-basis-v1.json','data/institutional-outlook-basis-v1.json')
LIBRARY='examples/v016/insight-threshold.noema'
BASIS='data/insight-threshold-basis-v1.json'
NAMES=('group','community','regime','field','audience','recipient','policy')
BASE=' '.join(n+' a' for n in NAMES)+' reference d assessment d'
BASE_ARGS=' '.join('v '+n for n in NAMES)+' v reference v assessment'
FRAME=BASE+' candidate d'
FRAME_ARGS=BASE_ARGS+' v candidate'
SCOPE_ARGS='v policy v community v regime v field'
PRIMITIVES={
 'h26d3':('[a a a a a a a d d d d d] c',
     ['group','community','regime','field','audience','recipient','policy','reference','candidate','anchor','alternative','point'],
     '同じ提案集団・政治的共同体・制度・領域・公衆・宛先・政策と固定基準について、候補経過の指定基準点と比較する代替経過・評価点の完全な範囲。公的な認識の状態を変えて比べる一方、関連する外的資源・制度上の発言経路・宛先・成員・既存の実践的機会など、認識以外の背景条件を同じ基準点にそろえる。公的認識そのもの、認識を使った方法の利用可能性や提案可能性の結果は固定条件にせず、成功例だけへ範囲を絞らない。同じ時刻相当の比較であり、以前の貧しい外的条件をそのまま混ぜない。範囲の網羅性と背景固定の妥当性は解釈入力の責任である。'),
 'h26d4':('[a a a a a d] c',['policy','community','regime','field','item','reference'],
     '同じ政策をこの共同体のこの制度と領域について共同で検討・提案する際に関連する、事柄のあり方・根拠・条件の代表認識内容の完全な範囲。政策内容、対象共同体、保護と非妨害の理由・制約などを扱い、単なる無関係な知識の増加を混ぜない。内容はh26aeのNoemaで明示し、成否や時点に応じて範囲を変更しない。実際の把握・公開・確証、十分な程度や提案可能性の真偽はこの関係では返さない。'),
}
MEANINGS={
 'r5gl':'同じ政策・共同体・制度・領域の固定された関連範囲h26d4に代表内容が属し、その同じ項目にr5fuの把握・根拠・公開・確証を伴う公的認識がある。無関係な項目や単なる掲示を十分性の比較へ数えない。',
 'r5gm':'同じ政策対象・公衆・固定基準・真偽評価を保持し、第一の候補点でr5glを持つ全項目を第二の候補点でも持つ。公的認識の充足についての包含であり、項目数・数値尺度・同じ保持者・全市民の同意を要求しない。',
 'r5gn':'r5gmが双方に成立し、同じ政策に関連する公的認識の内容が二つの候補点で等しい。名前の別名や同じ水準の保持者交代だけでは差にしない。',
 'r5go':'基準点に関連する公的認識が非空で、固定背景の比較範囲に同じ基準点自身を含み、同点にr5gkの共同提案可能性がある。さらに、その公的認識内容を全て備える比較点の全てで同じ提案が可能である。特定の一成功例や無関係な認識の存在だけで十分な程度にしない。',
 'r5gp':'同じ有効履歴の前後点で、関連する公的認識が新たに成立する項目があり、後点にr5goが成立する。後点と認識以外の背景をそろえた比較範囲に前点と同じ公的認識を持つ例が非空であり、その全例では同じ提案ができない。背景条件の改善だけや前点側の空集合によって、洞察の不足から十分への到達を認定しない。',
 'r5gq':'同じ対象・固定基準・真偽評価・候補経過・開始点から、評価点でr5gpの同じ共同提案に足りる公的認識へ到達する内容。期間の到達条件に渡せ、提案の実行や保護成功を要求しない。',
 'r5gr':'同じ導入活動・人民・法・制度・共同体・候補経過・開始終了点のr5fpへ、その同じ制度・公衆・政策・提案集団・君主の宛先のr5gqを到達条件として渡す。同じ短期の終了で初めてこの到達内容が成立し、それまで同じ制度と全市民の書面批評の自由を保つ。導入の目的も保持し、現実の必然的到達や終点後の廃止を追加しない。',
}
LIMITS=[
 'so weit ... daß ... könnteを、同じ提案についての公的認識の充足による質的な十分性として読む。公開・確証のある関連内容が到達後の水準以上なら、認識以外の背景をそろえた全比較例で共同提案が可能になる、という明示した強い操作的読みである。数値閾値・発見項目数・投票率・全員の心理的一致は補わない。',
 '前後の公的認識の比較にはr5fuを用い、把握・根拠・公開・同じ内容の検証を保持する。同じ結論の新しい説明や根拠関係を新たに捉えた場合は、その関係の内容を別項目として明示する。旧rknの論理的情報増加や単なる件数だけへ戻さない。',
 '以前の認識の水準を、後点の外的背景条件の下でも不足するものとして比較する。前点に別の外的障害があっただけ、無関係な認識が増えたのみ、比較例がないための空虚な全称では到達を満たさない。すべての可能世界における必要十分性や唯一の最小閾値まで主張しない。',
 '背景を固定した比較例の範囲は明示した入力であり、個々の観測から因果を発見する手続ではない。認識を使う方法の利用可能性まで固定してしまわず、比較点のr5gkを別に評価する。モデル外の背景や有限検査の網羅性を自動的に保証しない。',
 '比較点では元と異なる候補経過・評価点を許すが、政策・宛先・集団・制度・公衆・関連内容の範囲・真偽評価は同じである。前後で他の全知識が失われないことは要求しない一方、到達後の水準以上という比較では関連内容の包含を使う。',
 'r5grはこれまで別々だった同じ導入・短期・維持・公的批評・目的・洞察・保護提案可能性を時間条件へ接続する。r5fp/rkhの最初の到達点と半開区間の読みを保持し、現実の歴史で必ずその点へ到達する予言にはしない。最終的な可能性の内側で使う。',
 '保護を目的とするumの文章上の帰属、vornehmlich、etwaと接続法、非全員の譲歩、王座の換喩、Nun・wohl・gleichsamの描写と可能性、全文の著者帰属と通読は残る。全文確認の文字数は加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def selection(candidate,point):
    return 'k h26d3['+' '.join('v '+n for n in NAMES)+' v reference v candidate v anchor v '+candidate+' v '+point+']'

def definitions():
    text='d r5gl[item a '+FRAME+' point d] c['+both(
        'k h26d4['+SCOPE_ARGS+' k h26ag[v item v reference] v reference]',
        'k r5fu[v item v community v regime v field v audience v reference v assessment v candidate v point]')+'].\n'
    compare_fields=BASE+' sourcecandidate d first d targetcandidate d second d'
    one='k r5gl[v item '+BASE_ARGS+' v sourcecandidate v first]'
    two='k r5gl[v item '+BASE_ARGS+' v targetcandidate v second]'
    text+='d r5gm['+compare_fields+'] c[f item a[y['+one+']['+two+']]].\n'
    text+='d r5gn['+compare_fields+'] c['+both(
        'k r5gm['+BASE_ARGS+' v sourcecandidate v first v targetcandidate v second]',
        'k r5gm['+BASE_ARGS+' v targetcandidate v second v sourcecandidate v first]')+'].\n'
    ability=lambda candidate,point:'k r5gk[v group v community v recipient v policy v reference v '+candidate+' v '+point+']'
    above='k r5gm['+BASE_ARGS+' v candidate v anchor v alternative v point]'
    text+='d r5go['+FRAME+' anchor d] c['+both(
        'g item a[k r5gl[v item '+FRAME_ARGS+' v anchor]]',selection('candidate','anchor'),ability('candidate','anchor'),
        'f alternative d[f point d[y['+both(selection('alternative','point'),above)+']['+ability('alternative','point')+']]]')+'].\n'
    # Fix the background comparison to the later point while matching the earlier
    # public cognition, rather than reusing the earlier external circumstances.
    earlier='k r5gn['+BASE_ARGS+' v candidate v first v alternative v point]'
    selected=selection('alternative','point').replace('v anchor','v last')
    same_earlier=both(selected,earlier)
    timeline='k ta[i[at d][k h257z[v reference v candidate v at]] i[before d after d][k ic[v before v after v candidate]]]'
    text+='d r5gp['+FRAME+' first d last d] c['+both(timeline,
        'k h257z[v reference v candidate v first]','k h257z[v reference v candidate v last]','k ic[v first v last v candidate]',
        'g item a['+both('u[k r5gl[v item '+FRAME_ARGS+' v first]]','k r5gl[v item '+FRAME_ARGS+' v last]')+']',
        'k r5go['+FRAME_ARGS+' v last]',
        'g alternative d[g point d['+same_earlier+']]',
        'f alternative d[f point d[y['+same_earlier+'][u['+ability('alternative','point')+']]]]')+'].\n'
    text+='d r5gq['+FRAME+' start d] e[b point[k r5gp['+FRAME_ARGS+' v start v point]]].\n'
    additional='field a audience a group a recipient a policy a assessment d'
    text+='d r5gr['+INTRO_FIELDS+' end d '+additional+'] c[k r5fp['+INTRO_ARGS+' v end k r5gq['+FRAME_ARGS+' v start]]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['ta','h257z','ic'],['r5fu','h26ag'],['r5gk'],['r5fp'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='proposal_relative_public_insight_threshold_and_bounded_until',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
