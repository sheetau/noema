"""Compose conscientious service impossibility and the demand to leave an office."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_perceived_doctrinal_conflict import NAMES as BELIEF_NAMES,NAME_ARGS

PARENT='data/clerical-practical-benefit-basis-v1.json'
DEPENDENCY='data/perceived-doctrinal-conflict-basis-v1.json'
LIBRARY='examples/v016/conscientious-service-exit.noema'
BASIS='data/conscientious-service-exit-basis-v1.json'
PRIMITIVES={
    'h2522':('[a a d] c',['role','activity','reference'],
        '固定基準で、この活動の内容は指定職務に属する担当業務を取り扱い、その職を担って務めることに当たる。単にその職の名を用いる一回の発言、職場にいること、地位を保持するだけ、辞職を申し出るだけの活動とは区別する。対象期間と業務の範囲は同じ基準で固定し、失敗や良心上の評価によって職務活動の分類を取り消さない。職務保持・その立場での行為・実行者と実行は合成側で結ぶ。全生涯の業務を既に終えたことや、個々の業務の完全無欠な成功は要求しない。'),
    'h2523':('[a a d d d] c',['person','role','reference','actual','candidate'],
        '同じ本人・職務・固定基準について、評価点の事情と利用可能な手段・立場を保って、本人がその職を務めることを検討する実践上の可能な場合の全範囲。職務遂行や良心上の許容が成立した場合だけを選ばず、実行できない場合も残す。前提となる本人の信念・対象業務・適用基準を別のものに変更する再訓練や別職への移行を混ぜない。引受け行為だけの候補h252i、成功を保証する方法、全論理的可能世界、現実の履歴とは区別する。完全な範囲の供給は解釈入力で、非空性を合成側で要求する。'),
    'h2524':('[a a a d d] c',['activity','role','person','earlier','later'],
        '同じ前後を結ぶこの活動は、本人が指定職務を手放すという自らの選択に沿って、本人によるその職務の保持を終わらせる働きをする。単なる勤務の一時中断、異動への希望、死去、本人の行為によらない解任、たまたま同時に起きた喪失とは区別する。前後の保持状態・変化・行為者を別に結び、辞意の表明だけで終結したとはしない。外的な圧力の不在、特定の届出形式や受理制度、原文にない法律上の効果は要求しない。'),
    'h2525':('[a a d] a',['person','role','reference'],
        '同じ本人・職務・固定基準に適用する、良心に照らした実践上の基準を規範の出所として参照する。h252jの行為許容と同じ評価の基準に対応し、教会の任用権者、現に命令する人物、本人の罪悪感、国家法令へ自動的に同定しない。個別の退任要求や、その履行・正当性はこの参照だけから導かない。'),
}
MEANINGS={
    'r43s':'同じ本人・職務・活動について、その場面で職務を委ねられているcf、職務の立場での活動cb、本人による実行cg、固定基準での担当業務の遂行というh2522を結ぶ。役職保持だけや別職の活動を職務遂行としない。',
    'r43t':'r43sの同じ実行活動が、同じ本人・固定基準・評価点でh252jにより良心に照らして許容される。同じ場面の別活動の許容を借りず、許容の不在を職務の物理的不実行と同一視しない。',
    'r43u':'同じ本人・職務・固定基準でr43tを満たす活動が少なくとも一つ存在する内容。活動は職務を務める複合的な活動でもよい。',
    'r43v':'同じ本人が評価点でその職務を保持し、同じh2523の実践候補のどれかでr43uの良心に適う職務遂行が成立する。成功保証のある方法や実際の遂行を要求しない。',
    'r43w':'同じ本人が評価点でその職務を保持し、同じh2523範囲が非空で、その全候補にr43uの良心に適う職務遂行がない。空・未知の評価を不能とせず、一つでも可能な遂行があれば不能ではない。',
    'r43x':'同じ本人・職務・活動について、既存hzbyへh2524の本人による保持終結を渡す。現在の保持から将来の同じ履歴内の非保持へ、同じ本人の同じ変化活動で移る内容。単なる非在職や解任とは区別し、期限・届出形式を補わない。',
    'r43y':'正確な本人・職務の二個体列を束縛し、r43xの自己による職務保持の終結を満たす活動があるという内容を作る。規範の対象として引用でき、特定の未実行の辞職行為を外側で存在させない。固定基準は規範の接続用に受け、退任内容は各評価点からの将来を述べる。',
    'r43z':'同じ本人がその場面で同じ職務を保持し、同じ良心上の規範の出所h2525が、同じ本人・職務列をr43yへ適用する退任内容を肯定的に要求するh237zを結ぶ。現在の義務と将来の退任内容を分け、実際の退任や許可だけで要求を成立させない。',
    'r432':'同じ本人・職務・固定基準・評価点に、良心に従った職務遂行不能r43wと同じ職務の自己終結への要求r43zを合わせる。不能から義務を自動導出せず、条件文の帰結として接続するための構成。',
    'r433':'同じ本人・職務・規定群・宗教基準・固定基準と四呼称について、r43rの非空の全仮定候補に、自分が抵触を見いだすという信念と、同じ本人・職務・基準のr432の不能と辞職要求を結ぶ。帰結内の実践候補は各仮定候補を評価点として選び直し、現在の候補範囲を誤って流用しない。現実の信念・抵触・不能・要求・辞職はまだ主張しない。',
}
LIMITS=[
    'u0012[4279,4407)の前提と帰結を結ぶ依存群。先行perceived-doctrinal-conflictの前提r43q/r43rへ同じ本人・職務の帰結を接続する。先行本文の同じ規定群・職務への照応、Dennと全文帰属は未統合。確認文字数を増やさない。',
    'sein Amt verwaltenは、同じ職を担いその担当業務を扱って務める読み。単なる職名の保持とも、全生涯の業務を完全に終えたこととも区別する。mit Gewissenは同じ実行が良心上許容されることとして読み、心理的な罪悪感の不在だけにしない。',
    'nicht ... könnenは、当該事情を保つ実践上の全場合に良心に適う職務遂行がないという読み。旧rg5/xgの成功を保証する方法の不在だけでは、成功可能な候補を残し得るため代用しない。旧定義の意味は変更しない。',
    'h2523は可能性の範囲を明示する基本関係であり、有限検査から現実の全候補を網羅したとはしない。評価点で職務を保持し、候補範囲が非空であることを不能の前提にする。方法や候補の情報欠落を不能という結論へ変換しない。',
    'niederlegenは本人がその職を手放す選択に沿った保持の終結と読む。既存の順序付き履歴と保持の前後差を再利用し、自発的な辞職に外的圧力が全くないこと、特定の法的手続や辞表、当日中の履行は加えない。',
    'müßteは同じ仮定の帰結内の規範的な要求として接続する準備であり、実際の辞職の予測や物理的強制ではない。規範の出所は同じ良心上の基準とする明示した読み。個別の要求を出所参照や不能だけから導かない。',
    'Dudenの職務を務める／役職を手放す語義とAdelungのAmtを補助比較にする。原文前後の良心と同じ教会の職務を読むための資料であり、現代法や唯一の歴史解釈の証明ではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def definitions():
    fields='person a role a activity a reference d point d';args='v person v role v activity v reference v point'
    text='d r43s['+fields+'] c['+both('k cf[v person v role v point]','k cb[v person v activity v role v point]',
        'k cg[v person v activity v point]','k h2522[v role v activity v reference]')+'].\n'
    text+='d r43t['+fields+'] c['+both('k r43s['+args+']','k h252j[v person v activity v reference v point]')+'].\n'
    text+='d r43u[person a role a reference d] e[b point[g activity a[k r43t['+args+']]]].\n'
    fields='person a role a reference d actual d'
    selected='k h2523[v person v role v reference v actual v candidate]'
    goal='t[k r43u[v person v role v reference]][v candidate]'
    holding='k cf[v person v role v actual]'
    text+='d r43v['+fields+'] c['+both(holding,'g candidate d['+both(selected,goal)+']')+'].\n'
    text+='d r43w['+fields+'] c['+both(holding,'g candidate d['+selected+']','f candidate d[y['+selected+'][u['+goal+']]]')+'].\n'
    text+='d r43x[person a role a activity a] e[c[k hzby[v role p h2524]][v person v activity]].\n'
    target='g activity a[t[k r43x[v person v role v activity]][v point]]'
    text+='d r43y[bindings j[a] reference d] e[b point['+bind(('person','role'),target)+']].\n'
    text+='d r43z['+fields+'] c['+both(holding,
        'k h237z[k h2525[v person v role v reference] v person v role r b[p r43y] l[a][v person v role] v reference '+TRUE+' v actual]')+'].\n'
    text+='d r432['+fields+'] c['+both('k r43w[v person v role v reference v actual]','k r43z[v person v role v reference v actual]')+'].\n'
    text+='d r433[person a role a bundle a religion a reference d '+BELIEF_NAMES+' actual d] c[k r43r['
    text+='v person v bundle v religion v reference '+NAME_ARGS+' i[point d][k r432[v person v role v reference v point]] v actual]].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['cf','cb','cg','h252j','hzby','h237z']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    dep=dependency()
    for d in closure(dep.document,['r43r']):
        n=d['name'];e=dep.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(dep.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='conscientious_service_impossibility_and_required_self_departure',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set(old.source_sha256)|set(dep.source_sha256))},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
