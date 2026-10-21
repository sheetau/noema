"""Compose actual congregational reason use and size-independent internal scope."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_representative_teaching import TASK_FIELDS,TASK_ARGS,NAMES

PARENT='data/clerical-resignation-condition-basis-v1.json'
LIBRARY='examples/v016/congregational-private-use.noema'
BASIS='data/congregational-private-use-basis-v1.json'
PRIMITIVES={
    'h253b':('[a a a a d d] c',['activity','role','principal','subject','reference','point'],
        '同じ基準で指定する委託元・職務・主題に属する受託業務を、この活動が取り扱って遂行する位置付けにある。任務が割り当てられているだけ、無関係な同時活動、委託元の名を引用しただけとは区別する。本人・職務委任・他者への奉仕・実際の活動は合成側で結ぶ。全任務の完了、完全な成功、全規定への適合、内容の真理、委託元の全見解を代弁することは要求しない。'),
    'h253c':('[a a a d d] c',['group','institution','subject','reference','point'],
        '同じ組織との関係において、この集団は指定主題に関する共通の働きかけを受けるために集まる人々の集会として位置付けられる。単なる人数の集合、建物、無関係な同席とは区別する。継続する集団を集会として捉える分類であり、全成員が常時同じ場所に現に居合わせることや、一回限りの会合への同定は要求しない。話者・対象集団・受領者への実際の提示は別に結ぶ。'),
    'h253d':('[a a d d] c',['group','institution','reference','point'],
        '同じ基準で、この集団の共同の用事と宛先としての立場が、指定組織の成員・担当の関係によって内側の範囲を持つ。家の者が家の共同の用事で集まる場合になぞらえた、組織内部の集まりとしての性格である。単に人数が少ない、物理的な家屋内、同居・血縁、全員の親密さ、秘密の会合という条件へ置き換えない。外部の見学者を完全排除することや、同じ人が他の場で公衆へ語れないことは要求しない。集会の分類、読者世界全体との区別、規模や機会を変えてもこの性格が保たれることは合成側で別に要求する。'),
    'h253e':('[a a a d d d] c',['group','institution','subject','reference','actual','candidate'],
        '同じ集団・組織・主題・固定基準について、評価点で論じる当該集会の機能と担当関係を保ち、その集会としての関連する機会と規模を変えて考察する場合の全範囲。構成員や人数は候補間で変わり得る。任意に大きい規模もそれだけで範囲外にせず、原文にない人数上限や現実に訪れた機会だけへの制限を設けない。家内的であること、読者世界全体でないこと、私的分類や自由の不在を選択条件にして結論を先取りしない。現実の無限人数の集会の存在や、考えられる全規模の現実化は要求しない。範囲の完全性は解釈入力の条件で、現在の評価点の包含を合成側で要求する。'),
}
MEANINGS={
    'r44a':'r372の同じ聖職者・職務・教会・担当機会・発話の実際の教示に、同じ時点の本人の理性使用ca、同じ活動の会衆宛てccを結ぶ。実際の担当受領者のうち少なくとも一人が同じ会衆の成員であり、同じ主題・発話を受けたことを要求する。生徒だけへの教示を会衆の前での使用へ混ぜず、全会衆への到達は要求しない。',
    'r44b':'同じ会衆の前での職務上の理性使用r44aが、同じ本人・活動・職務・評価点の私的分類r2zjを満たし、同じ立場で公的分類r2ziを満たさない。bloßの排他性を同じ使用の立場に限定する。本人の別の学識者活動や別の立場を全面的に否定しない。',
    'r44c':'r44aの同じ実際の活動が、同じ教会・職務・主題について受託業務の遂行h253bである。r37zの本人と委託元の非同一性を引き継ぎ、他者の委託を遂行する内容を結ぶ。任務の存在だけから遂行を導かない。',
    'r44d':'同じ集団・組織・主題・固定基準・評価点に、集会としての分類h253c、家内的な内側の範囲h253d、読者世界全体ceではないことを合わせる。人数だけで家内的とも本来の公衆とも判定しない。',
    'r44e':'同じ集会について、現在点を含むh253eの全関連機会・規模の候補でr44dを要求する。immerとobzwar noch so großを、当該集会として扱う限り機会・規模によらず家内的な範囲に留まるという読みで構成する。空範囲や一つの小さい例の成功だけでは成立しない。',
    'r44f':'同じ聖職者事例・活動・発話・評価点に、会衆の前での私的使用r44b、他者の業務遂行r44c、同じ会衆・教会・主題の規模と機会に依存しない家内的性格r44eを連言する。後続の自由の否定や規範はまだ含めない。',
}
LIMITS=[
    'u0012[4408,4734)の一文に向けた意味依存群。Lehrerは文脈の同じ任用された聖職者、vor seiner Gemeindeは同じ会衆への実際の教示として読む。旧r372の代表教示事例を再利用し、信条への内心の同意や全成員への到達を追加しない。',
    'bloß ein Privatgebrauchは同じ本人・活動・職務としての使用について私的分類を満たし公的分類を満たさないという明示読み。私的分類一般を公的分類の否定で定義し直さず、同じ人の学識者としての別の使用を妨げない。',
    'häuslicheは、直後の本来の公衆すなわち世界との対照に照らし、家の内部の用事になぞらえた組織内の集まりという読みを採る。Dudenの家・家庭に関する語義だけからこの文脈的解釈が証明されるわけではない。物理的な家屋・同居家族という事実は補わない。',
    'Versammlungはここでは継続する会衆を集まる人々として捉える。常時全員が一つの場所にいるという出来事の反復にはしない。規模の譲歩は現実に巨大な会衆が存在したという追加主張ではなく、規模がいかに大きくとも内部的性格が変わらないという範囲の読みとする。',
    'immerは当該会衆をこの集会として扱う全関連機会についての持続と読む。本人の全生涯・宇宙の全時点へ広げない。h253eは機会と規模の完全な考察範囲を指定し、結果による選別を禁止する。有限検査で現実の範囲の完全性を証明したとはしない。',
    'Auftrag ausrichtenは実際の同じ教示活動が受託業務を遂行するという読み。任務の存在と遂行を分け、本人と異なる委託元に同じ教会を使う。全委託業務の完了や教会の全規定への適合は追加しない。',
    'nicht freiとdarf es auch nicht sein、also・二つのweil・in Ansehung dessen・obzwarの談話提示・全文帰属は次の統合事項。今回の依存群だけで文全体を意味確認済みにせず、確認文字数は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    point='v point'
    reached='g recipient a['+both('k r35p[v congregation v recipient v reference]',
        'k h246o[v occasion v recipient v reference]','k f2[v activity v recipient v subject v message v point]')+']'
    text='d r44a['+TASK_FIELDS+'] e[b point['+both('t[k r372['+TASK_ARGS+']][v point]',
        'k ca[v person v activity v point]','k cc[v activity v congregation v point]',reached)+']].\n'
    text+='d r44b['+TASK_FIELDS+'] e[b point['+both('t[k r44a['+TASK_ARGS+']][v point]',
        'k r2zj[v person v activity v role v point]','u[k r2zi[v person v activity v role v point]]')+']].\n'
    text+='d r44c['+TASK_FIELDS+'] e[b point['+both('t[k r44a['+TASK_ARGS+']][v point]',
        'k h253b[v activity v role v church v subject v reference v point]')+']].\n'
    text+='d r44d[group a institution a subject a reference d] e[b point['+both(
        'k h253c[v group v institution v subject v reference v point]',
        'k h253d[v group v institution v reference v point]','u[k ce[v group v point]]')+']].\n'
    selected='k h253e[v group v institution v subject v reference v actual v candidate]'
    text+='d r44e[group a institution a subject a reference d actual d] c['+both(
        'k h253e[v group v institution v subject v reference v actual v actual]',
        'f candidate d[y['+selected+'][t[k r44d[v group v institution v subject v reference]][v candidate]]]')+'].\n'
    text+='d r44f['+TASK_FIELDS+'] e[b point['+both('t[k r44b['+TASK_ARGS+']][v point]',
        't[k r44c['+TASK_ARGS+']][v point]','k r44e[v congregation v church v subject v reference v point]')+']].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r372','r35p','r2zj','r2zi']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='actual_congregational_private_use_and_size_independent_internal_assembly',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
