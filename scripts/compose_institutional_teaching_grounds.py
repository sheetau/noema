"""Connect institutional instruction and its used justificatory grounds."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import MESSAGE

PARENT='data/clerical-explanation-basis-v1.json'
LIBRARY='examples/v016/institutional-teaching-grounds.noema'
BASIS='data/institutional-teaching-grounds-basis-v1.json'
PRIMITIVES={
    'h247u':('[a a d] c',['organization','judgment','point'],
        '同じ状況で、この判断がこの組織自身の判断として制度・慣行上帰属する。成員個人の私的な判断や組織についての外部評価とは区別し、全員の同意・個人としての判断行為・判断の正しさを要求しない。帰属する内容と教示上の位置付けは別に結ぶ。'),
    'h247v':('[a a d] c',['organization','judgment','point'],
        'この組織がこの判断の内容を、自らの教えとして伝えるべき立場として公に位置付けている。単に他者の見解として紹介すること、私的検討、条件に適合するだけの未採用内容とは区別する。特定の人の講義の実行、受け手の理解、教えの真理や全員の信念一致は要求しない。'),
    'h247w':('[a a d] c',['judgment','reason','point'],
        'この判断に関してこの理由は、判断内容の正しさを示すための論拠として位置付けられる。便宜・利益・動機としての理由だけの場合とは分ける。論拠としての実際の使用、客観的な支持、単独での十分性、形式的演繹の妥当性はそれぞれ別であり、この関係から導かない。'),
}
MEANINGS={
    'r4n':'同じ組織に帰属する同じ判断を、同じ主題・閉じた発話内容へ結び、組織の教えとしての公的位置付けを要求する。内側の発話を実行せず、個人の判断faや講義の実行へ置き換えない。',
    'r4o':'同じ組織・主題・発話についてr4nの教示上の判断が存在する。判断の一意性や全教義の網羅を追加しない。',
    'r4p':'同じ判断・理由・状況について、理由が実際に用いられるfcと、正しさを示す論拠という位置付けh247wを結ぶ。実際の支持fdとは独立である。',
    'r4q':'同じ組織の同じ教示判断r4nに対し、非空の指定範囲が、その判断で実際に用いる論拠r4pを尽くす。rggの使用関係をr4pに限定し、論拠ではない動機・便宜上の理由まで一覧に混ぜない。同じ判断への別の論拠は除外できない。',
    'r4r':'同じ組織と内側の発話を固定し、同じ主題について組織がその内容を教えるr4oという外側の主張をrgdから作る。引用・提示だけでは教示関係や内側の真理を成立させない。',
    'r4s':'同じ組織・教示判断・内側の発話・理由範囲を固定し、同じ主題についてr4qを主張する外側の発話を作る。使用論拠の完全性を報告内容に置き、報告する行為から完全性や支持を導かない。',
}
LIMITS=[
    'u0012[3794,3898)の教示報告とBeweisgründeの依存群。本文への発言予想・われわれの教会への照応・dieses oder jenesの不特定性・二報告の提示と全文帰属は未統合。本文と意味確認文字数を増やさない。',
    '組織の教示を、制度的に帰属する判断内容の公的な教えとしての位置付けと読む。全成員の同意、個々の教示の実行、内側の真理、特定の宗派や意思決定手続は補わない。組織判断の一般理論を完成したとはしない。',
    'Beweisgründeは教示内容の正しさを示すために用いられる論拠。Dudenの現代語義を補助確認し、原刊487頁の本人の確信との対照を保持する。歴史的な唯一の解釈の証明にはしない。',
    'die ... deren sie sich bedientを、同じ教示判断・状況で用いる論拠の指定範囲が完全な一覧であるという読みで扱う。全状況・全教義・全可能な根拠に拡張せず、便宜上の理由まで尽くすとはしない。',
    '内側の発話は閉じたNoema記述であり、原文が指定しない具体的教義や理由を外部から捏造しない。真偽が同じ別名・質問への差替えを自動同一視しない。',
    '用いる論拠の地位と支持を分ける。原文が形式的な証明や具体的推論を指定していないため、それを勝手に追加しない。有限診断は全解釈の意味同値性の証明ではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    fields='organization a judgment a subject a message '+MESSAGE+' point d'
    args='v organization v judgment v subject v message v point'
    text='d r4n['+fields+'] c['+both('k h247u[v organization v judgment v point]',
        'k fb[v judgment v subject v point]','k hzv[v judgment v subject v message v point]',
        'k h247v[v organization v judgment v point]')+'].\n'
    text+='d r4o[organization a subject a message '+MESSAGE+' point d] c[g judgment a[k r4n['+args+']]].\n'
    text+='d r4p[judgment a reason a point d] c['+both('k fc[v judgment v reason v point]',
        'k h247w[v judgment v reason v point]')+'].\n'
    text+='d r4q[organization a judgment a subject a message '+MESSAGE+' reasons h[a] c point d] c['+both(
        'k r4n['+args+']','k rgg[v organization v judgment v subject v message v reasons v point p h247u p fb p hzv p r4p]')+'].\n'
    text+='d r4r[organization a message '+MESSAGE+'] h[a] f[k rgd[v organization v message p r4o]].\n'
    text+='d r4s[organization a judgment a message '+MESSAGE+' reasons h[a] c] h[a] f[i[subject a][j s[b point[k r4q[v organization v judgment v subject v message v reasons v point]]]]].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['rgd','rgg']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    # These existing relations were outside the generic report closures.
    for d in closure(old.document,['fb','hzv','fc']):
        if d['name'] not in imported:doc['declarations'].append(d);imported[d['name']]=old.entries[d['name']]
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='institutional_teaching_and_exhaustive_used_justificatory_grounds',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
