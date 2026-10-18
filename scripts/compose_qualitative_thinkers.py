"""A nonnumerical response disposition, connected to native dissemination."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_described_dissemination import declaration,PER_PERSON
from scripts.compose_thinking_disseminators import call as k,conjunction as both,THINKING
from scripts.compose_existential_dissemination import EXISTENTIAL,FUTURE
from scripts.compose_existential_focus import FAMILY,PREDICATE
from scripts.compose_shared_future_period import CONDITION

PARENT='examples/v016/kant-shared-future-period.noema'
PARENT_BASIS='data/shared-future-period-basis-v1.json'
FULL='examples/v016/kant-qualitative-thinkers.noema'
CORE='examples/v016/qualitative-thinkers-core.noema'
LIBRARY='examples/v016/preferred-responses.noema'
BASIS='data/qualitative-thinkers-basis-v1.json'
QUALITATIVE=[('thinkcases','h[a d d] c'),('thinkpreferred','h[a d d d] c'),
    ('thinktopics','h[a d d] a'),('thinkpresented','h[a a d] c')]
FIELDS=[(n,t) for n,t in FUTURE if n not in dict(THINKING)]+QUALITATIVE
PROVIDERS=[(n,'h[d] '+t) for n,t in FIELDS if n not in ('history','before')]
MEANINGS={
 'rqt2':'指定範囲内の場面で、その範囲の別の場面に比べて劣後しないもの。preferredは第一場面を第二場面より文脈上通常とみなす厳密な関係として渡す。範囲外の場面は候補にならない。',
 'rqt3':'指定範囲上でpreferredの非反射性・推移性と、全候補が極小候補であるか極小候補に劣後することを要求する。数値尺度・全比較可能性・候補の有限列挙を要求しない。',
 'rqt4':'rqt3を満たす同じ候補範囲に極小候補が少なくとも一つあり、その全てで同じ応答条件が成立する。劣後する例外候補での失敗を許すが、比較不能な極小候補の失敗は消さない。空範囲や極小候補を欠く範囲を空虚に真としない。',
 'hzq3':'同じ本人・基準状況から候補範囲・通常性の比較・話題を固定し、hzhgの同じ本人による同じ話題への独立判断をrqt4の応答へ渡す。重み・数値閾値・評価済みフラグを必要としない性向の候補であり、現在の一回の判断とは区別する。',
 'hzq4':'同じ本人・同じ初期機会で、hzq3の性向と既存hzpdの自己離脱・存在する伝播を結ぶ。発信者と判断する人を交換しない。',
 'hzq5':'将来の各機会で、人の母集団に複数のhzq4該当者と、その中の指定部分集団の該当者がいる内容。人・機会と各供給関数を共用し、有限の評点プロフィールを条件に加えない。',
 'rqt5':'許可に使う期間枠から同じ候補の履歴と順序を作り、残る17供給関数を同じ候補へ適用してhzq5の内容族を作る。比較対象の部分集団で通常性の条件を差し替えない。',
 'rqt6':'許可条件の枠rqtpへrqt5の内容族を接続する。既存hzpyへ閉じた枠として渡せ、後見役とその外側の比較背景・著者帰属を保持する。',
}
LIMITS=[
 '有限の加重プロフィールhzhhは測定条件を明示する構成として保持する。新しい構成はそれと同値とせず、独立判断への性向を数値なしで記述する別の読解候補である。',
 '候補は同じ本人・基準状況に相対的な仮定場面で、preferredはその比較条件である。応答の成功を見て候補や比較を選び直すことを正当化しない。原文に適した通常性・反事実条件の説明はなお必要である。',
 'Kraus・Lehmann・Magidorの極小状態に基づく意味論を構成の参考にするが、その体系全体や全ての部分範囲での滑らかさは実装・証明していない。空候補を拒否する追加条件がある。',
 '状況全域への量化を用い、文法に候補列の長さ上限を設けない。有限評価器の検査を無限状況の完全な検証とは扱わない。',
 'hzhgは独立した理由ある判断という読みを保つ。想像・探索・疑問を含む思考の全てや、性向の心理機構を説明済みとはしない。',
 '受け手が取得する性向hznyは別の内容であり、今回その定義を変更していない。本文34文・確認済み七単位・既存原文範囲を保持する。',
]


def definitions():
    fields=[('cases','h[d] c'),('preferred','h[d d] c')]
    minimal=lambda point:k('rqt2','v '+point,'v cases','v preferred')
    text=declaration('rqt2',[('point','d')]+fields,'c',both('c[v cases][v point]',
        'u[g other d['+both('c[v cases][v other]','c[v preferred][v other v point]')+']]'))
    irreflexive='f first d[y[c[v cases][v first]][u[c[v preferred][v first v first]]]]'
    transitive='f first d[f second d[f third d[y['+both('c[v cases][v first]','c[v cases][v second]','c[v cases][v third]',
        'c[v preferred][v first v second]','c[v preferred][v second v third]')+'][c[v preferred][v first v third]]]]]'
    smooth='f point d[y[c[v cases][v point]][x['+minimal('point')+'][g better d['+both(minimal('better'),'c[v preferred][v better v point]')+']]]]'
    text+=declaration('rqt3',fields,'c',both(irreflexive,transitive,smooth))
    text+=declaration('rqt4',fields+[('response','h[d] c')],'c',both(k('rqt3','v cases','v preferred'),
        'g point d['+minimal('point')+']','f point d[y['+minimal('point')+'][c[v response][v point]]]'))
    response=k('hzhg','v person','c[v thinktopics][v person v anchor v scene]','v scene','v thinkpresented')
    text+=declaration('hzq3',[('person','a'),('anchor','d')]+QUALITATIVE,'c',both(k('aa','v person'),k('rqt4',
        'i[scene d][c[v thinkcases][v person v anchor v scene]]',
        'i[first d last d][c[v thinkpreferred][v person v anchor v first v last]]','i[scene d]['+response+']')))
    text+=declaration('hzq4',EXISTENTIAL+QUALITATIVE,'c',both(k('hzq3','v origin','v initial',*('v '+n for n,t in QUALITATIVE)),
        k('hzpd',*('v '+n for n,t in EXISTENTIAL))))
    args=['v person' if n=='origin' else 'v opportunity' if n=='initial' else
        'c[v '+n+'][v person v opportunity]' if n in PER_PERSON else 'v '+n for n,t in EXISTENTIAL+QUALITATIVE]
    qualified='i[person a opportunity d]['+k('hzq4',*args)+']'
    human='f person a[y[c[v members][v person v opportunity]][k aa[v person]]]'
    atpoint=both(human,k('rqti','v opportunity','v members','v subgroup',qualified))
    text+=declaration('hzq5',FIELDS+[('subgroup','h[a d] c')],'e','b base['+
        k('rqtj','v history','v before','v base','i[opportunity d]['+atpoint+']')+']')
    supplied={n:'c[v '+n+'][v branch]' for n,t in PROVIDERS}
    supplied.update(history=k('rqtw','v period','v branch'),before=k('rqtx','v branch'))
    text+=declaration('rqt5',[('period','a')]+PROVIDERS,FAMILY,'i[subgroup '+PREDICATE+' branch d]['+
        k('hzq5',*(supplied[n] for n,t in FIELDS),'s[v subgroup]')+']')
    text+=declaration('rqt6',CONDITION+PROVIDERS,'h['+PREDICATE+'] e',k('rqtp',*('v '+n for n,t in CONDITION),
        k('rqt5','v permissionframe',*('v '+n for n,t in PROVIDERS))))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['rqt6','hzpy','hzny','rqsx'])
    library=deepcopy(doc);library['statements']=[];library['declarations']=closure(doc,['rqt4'])
    basis=dict(status='qualitative_preferred_response_candidate_for_independent_thinkers',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        research_reference='https://arxiv.org/abs/cs/0202021',
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Qualitative response disposition connected to native dissemination',flush=True)


if __name__=='__main__':main()
