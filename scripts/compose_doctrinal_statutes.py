"""Bind prescribed doctrinal formulations, their conjunction and contained truth."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_personal_conviction import CONTENT,PREMISE
from scripts.compose_unsettled_teaching import SELECTION

PARENTS=('data/clerical-report-forecast-basis-v1.json','data/personal-conviction-basis-v1.json')
LIBRARY='examples/v016/doctrinal-statutes.noema'
BASIS='data/doctrinal-statutes-basis-v1.json'
FIELDS='church a creed a subject a standard a bundle a rules j[a] reference d'
ARGS='v church v creed v subject v standard v bundle v rules v reference'
PRIMITIVES={
    'h252e':('[a a d] c',['standard','formulation','reference'],
        'この定式化は、同じ基準において、教示すべき立場を定める規定として位置付けられている。単に基準に適合すること、引用してもよいこと、誰かの未採用の提案とは区別する。基準の採用主体と、定式化が表す教義内容は別に結ぶ。教義内容の真理、規定の正当性、本人の確信や実際の教示を含意しない。'),
    'h252f':('[a a d] c',['formulation','part','reference'],
        '同じ固定基準で、この部分の定式化が表す命題内容は、元の定式化が肯定的に含む構成部分である。単なる同じ主題への言及、真偽が偶然同じこと、任意の論理的帰結、否定・反駁するためだけの埋込みとは区別する。間接に含む部分もこの関係の範囲へ明示する。内容は双方のh246eの閉じたNoema記述で指定し、原始関係の真偽だけで自然言語の未記述部分を代用しない。部分の真理・全体への十分性を要求しない。'),
}
MEANINGS={
    'r42h':'固定基準の同じ規定列の各h246eを、真の内容から始めて連言する閉じた段階0の内容記述を構成する。各項の内容を実行せず、要求の履行を教義の真理へ変換しない。空列の構成は恒真だが、規定群の接続r42jは空列を認めない。',
    'r42i':'r42hの同じ閉じた連言内容を、対象と基準を引数に取る閉じた段階0の内容関数へ持ち上げる。内容自体は構成時の規定列・基準に固定し、候補で調べ直さない。判断の対象・基準との同一性はr42mで別に結ぶ。',
    'r42j':'同じ教会・信条・主題・採用基準r35sに対し、指定列が固定された規定群の成員を尽くすrcmを要求する。群には異なる二定式化が少なくともあり、全成員が同じ基準の教示規定h252eで、その閉じた教義内容h246eを同じ教会が共同の立場h246gとして採用する。教会の全規定をこの群に含める要求ではない。',
    'r42k':'同じ固定基準の規定群に属する定式化そのもの、または、その成員がh252fにより肯定的に含む命題的部分である。無関係な規定の部分や、候補で初めて加わった部分を流用しない。',
    'r42l':'同じ本人・規定群・固定基準の可能状況のどれかで、r42kに属する部分の同じh246eの内容が真である。既存rgnを再利用し、所属と内容を基準に固定する。群全体の真理や本人の賛同を要求せず、隠れていること自体はまだ加えない。',
    'r42m':'r42jの同じ規定群と列について、r42iで構成した同じ教義内容をr42gへ渡し、同じ本人が仮定の下で十分な確信を伴っては肯定しないことを結ぶ。基準の採用・教義の真理・本人の確信・仮定の帰結を別々に保持する。',
}
LIMITS=[
    'u0012[3899,4278)に向けた規定群・確信・含まれる真理の依存群。本文の具体的な事例と著者帰属は未統合。本文と意味確認文字数を増やさない。',
    'Satzungenを、教会が教示すべき立場として定めた教義の定式化群と読む。Adelungの宗教・信仰に関する規定の語義と前後の教示との対照を参照する。命令の履行状況を教義の真理と同一視せず、条件付き行為要求rbaを各教義の真理条件へ代入しない。',
    '群はこの箇所で問題となる複数の規定を表す明示された有限列で指定する。列の完全性はrcmとh6tの完全な所属解釈により検査する。無限の全規定を列挙できるとはしない。重複は拒否して列順は保持し、同じ意味の別構文へ自動正規化しない。',
    '十分な確信を伴う賛同は、この群の全内容への集合的な肯定として読む。各規定を個別に全て否定することや、全規定が偽だという主張にはしない。各項への肯定から連言への確信を論理的全知として導かない。',
    'h252fの命題的部分と、その閉じたNoema内容の適切さは明示解釈の意味契約であり、有限真理表だけから認定しない。隠れた真理の発見、真理が隠れている仕方、可能候補の認識上の妥当性は残る。',
    'r42mへ渡す仮定の具体的な補充、会衆への全実益、引受け可能性、内面の宗教への抵触不在、談話関係は未接続。personal-convictionの本人の確信に限定する読みを継承し、客観的な正当性へ強めない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    combine='r[i[left e right e][b point[w[t[v left][v point]][t[v right][v point]]]]]'
    text='d r42h[rules j[a] reference d] i[e][q[v rules][r[b point['+TRUE+']]][i[content i[e] rule a][o a['+combine+'][v content k h246e[v rule v reference]]]]].\n'
    text+='d r42i[rules j[a] reference d] '+CONTENT+'[o a[r[i[body e][i[target a anchor d][v body]]]][k r42h[v rules v reference]]].\n'
    member='k h6t[v bundle v rule v reference]'
    text+='d r42j['+FIELDS+'] c['+both('k r35s[v church v creed v subject v standard v reference]',
        'k rcm[v rules i[rule a][k h6t[v bundle v rule v reference]]]',
        'g first a[g second a['+both('k h6t[v bundle v first v reference]',
            'k h6t[v bundle v second v reference]','u[e[v first][v second]]')+']]',
        'f rule a[y['+member+']['+both('k h252e[v standard v rule v reference]',
            'k h246g[v church v rule k h246e[v rule v reference] v reference]')+']]')+'].\n'
    text+='d r42k[bundle a claim a reference d] c[x[k h6t[v bundle v claim v reference]][g rule a['+both(member,
        'k h252f[v rule v claim v reference]')+']]].\n'
    text+='d r42l[person a bundle a reference d alternatives '+SELECTION+'] c[k rgn[v person v bundle v reference v alternatives p r42k i[claim a][s[k h246e[v claim v reference]]]]].\n'
    text+='d r42m[person a '+FIELDS+' premise '+PREMISE+' actual d] c['+both('k r42j['+ARGS+']',
        'k r42g[v person v bundle k r42i[v rules v reference] v reference v premise v actual]')+'].\n'
    return text


def build():
    old,personal=parents();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['r35s','h6t','rcm','rgn']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(personal.document,['r42g']):
        n=d['name'];e=personal.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(c.entries) for c in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_prescribed_doctrines_conjunction_and_possible_contained_truth',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
