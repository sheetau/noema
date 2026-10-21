"""Compose a people's religious guardians and the quoted demand for immaturity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind

PARENT='data/unrestricted-scholarly-freedom-basis-v1.json'
LIBRARY='examples/v016/spiritual-guardians.noema'
BASIS='data/spiritual-guardians-basis-v1.json'
GUARDIAN_FIELDS='person a role a people a community a matter a reference d'
GUARDIAN_ARGS='v person v role v people v community v matter v reference'
POLICY_NAMES=('source','people','community')
POLICY_FIELDS=' '.join(n+' a' for n in POLICY_NAMES)+' reference d'
POLICY_ARGS=' '.join('v '+n for n in POLICY_NAMES)+' v reference'
PRIMITIVES={
    'h253r':('[a a a a d] c',['guardian','ward','role','matter','reference'],
        '同じ担い手が指定の役割で持つ同じ相手への総括的な指導・監督の立場は、指定の事柄についての判断・指示をその担当範囲に含む。単なる職名、別の相手への別の役割の担当、宗教とは無関係な一般的監督で代用しない。役割の保持、監督関係と事柄の分類は合成側で別に要求する。実際の指導行為、正当性、相手の服従、本人の能力や当該事柄の正しさは要求しない。'),
}
MEANINGS={
    'r45d':'同じ人々の集団の構成員列mpが人のみからなり重複せず非空で、同じ固定基準の政治的共同体の成員h237cと過不足なく一致する。読者の世界全体ceや局所的な教区の会衆を人民全体と同一視せず、民族的同質性や現代の国籍制度を追加しない。',
    'r45e':'同じ政治的共同体の人民r45dについて、本人が同じ役割を持ち、少なくとも一人の他の構成員を指導・監督するdc。その同じ相手の宗教的な生き方に関わる事柄sgが同じ役割の担当範囲h253rに入る。役割・相手・事柄を別々の証人から集めず、全人民を一人で指導するとは要求しない。',
    'r45f':'本人だけの正確な一個体列と基準を受け、既存bfの未成熟の内容をその同じ本人について構成する。基準は規範対象の固定引数として保持し、未成熟はその内容を評価する状況ごとにbfで決まる。未成熟を年少、発言の禁止や現在の不使用へ置き換えない。',
    'r45g':'同じ規範の出所が同じ本人へ同じ役割で、r45fへ本人一個体と固定基準を渡す未成熟の内容を正極性で要求する内容。既存h237zを用い、未成熟の現実の成立、能力の評価、規範の正当性、著者の命令行為をここから導かない。',
    'r45h':'同じ人民・政治的共同体・固定基準に属する宗教上の後見役r45eが非空であり、全本人・役割・宗教的な事柄の該当例に、同じ出所から同じ本人の未成熟への要求r45gがあるという方針内容。未成熟な人や要求済みの役割だけへ対象を絞らない。本人が導く相手の未成熟への要求とは区別する。',
    'r45i':'規範の出所・人民・政治的共同体の正確な三個体列と固定基準からr45hの方針内容を作る。閉じた段階2の記述として評価・帰結関係の対象へ渡せる。引用しただけでは要求方針や未成熟を実行しない。',
}
LIMITS=[
    'u0012[5022,5190)のdie Vormünder des Volks (in geistlichen Dingen) selbst wieder unmündig sein sollenに向けた依存群。全文の不合理という評価、帰結と永続化、selbst wiederの取り立てとDennの理由提示はまだ統合しない。本文95主張と意味確認文字数を保持する。',
    'Volkは文脈上の同じ政治的共同体の人々の全体という明示読み。mpの列とh237cの構成員範囲を全個体上で一致させ、当日の会衆や本来の読者世界とは分ける。全人民への一人の後見人の監督は要求せず、全該当する後見役を方針の対象とする。',
    'geistlichは宗教・教会に関わる領域と読み、既存sgの宗教的な実践・理解と生き方に接続する。精神一般・知的活動一般という広いgeistigへ置き換えない。dcの一般的監督関係に同じ役割・相手・事柄の担当を結ぶ。',
    '後見人自身の未成熟を要求する方針を構成する。誰かが実際にこの要求を出したこと、Kantが要求を是認したこと、後見人が現に未成熟であることは、この引用対象の存在からは主張しない。全文では方針を評価と帰結の対象として引用する必要がある。',
    'unmündigは冒頭から用いたbf、すなわち自立的な理解力使用の現在の通常行使能力の不足という明示読みを継承する。他人を指導する役割を持つことだけから能力や未成熟を結論しない。未知の能力評価を偽へ補わない。',
    '同じ人物が他者を導く一方で自身は指導に依存すべきだという対比がselbst wiederの接続先となる。過去に一度成熟してから再び未成熟に戻る履歴は、この語だけから補わない。取り立ての全文帰属は後続の統合事項。',
    '既存bfの通常評価、役割の分類、未成熟への要求、全後見役への方針を分けて検査する。現実の人民範囲や歴史的な職務の網羅性は入力の解釈に依存し、有限検査はそれを自動証明しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def quant(names,body,operator='f'):
    for n in reversed(names):body=operator+' '+n+' a['+body+']'
    return body


def definitions():
    text='d r45d[people a community a reference d] c['+both(
        'k hi[k mp[v people] p aa]','g member a[k hg[k mp[v people] v member]]',
        'f member a[e[k hg[k mp[v people] v member]][k h237c[v member v community v reference]]]')+'].\n'
    ward=both('k hg[k mp[v people] v ward]','k aa[v ward]','u[e[v person][v ward]]',
        'k dc[v person v ward v reference]','k sg[v ward v matter v reference]',
        'k h253r[v person v ward v role v matter v reference]')
    text+='d r45e['+GUARDIAN_FIELDS+'] c['+both('k r45d[v people v community v reference]',
        'k aa[v person]','k hzwn[v person v role v reference]','g ward a['+ward+']')+'].\n'
    text+='d r45f[bindings j[a] reference d] e[b point['+bind(('person',),'t[k bf[v person]][v point]')+']].\n'
    text+='d r45g[source a person a role a reference d] e[b point[k h237z[v source v person v role r b[p r45f] l[a][v person] v reference '+TRUE+' v point]]].\n'
    candidate='k r45e['+GUARDIAN_ARGS+']'
    text+='d r45h['+POLICY_FIELDS+'] e[b point['+both(quant(('person','role','matter'),candidate,'g'),
        quant(('person','role','matter'),'y['+candidate+'][t[k r45g[v source v person v role v reference]][v point]]'))+']].\n'
    text+='d r45i[bindings j[a] reference d] e[b point['+bind(POLICY_NAMES,'t[k r45h['+POLICY_ARGS+']][v point]')+']].\n'
    return text


def build():
    old=parent();assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=deepcopy(old.document);doc.update(declarations=closure(doc,['hi','hg','mp','aa','h237c','dc','sg','hzwn','bf','h237z']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='same_peoples_religious_guardians_and_quoted_immaturity_requirement',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
