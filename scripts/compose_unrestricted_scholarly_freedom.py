"""Integrate unrestricted scholarly freedom with written address and contrast."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import NAMES,MESSAGE
from scripts.compose_scholarly_own_voice import ARGS as SPEECH_ARGS

PARENT='examples/v016/kant-clerical-private-conclusion.noema'
PARENT_BASIS='data/clerical-private-conclusion-basis-v1.json'
DEPENDENCY='data/scholarly-own-voice-basis-v1.json'
FULL='examples/v016/kant-unrestricted-scholarly-freedom.noema'
CORE='examples/v016/unrestricted-scholarly-freedom-core.noema'
BASIS='data/unrestricted-scholarly-freedom-basis-v1.json'
ANNOTATIONS='data/unrestricted-scholarly-freedom-identifiers-v1.json'
FIELDS='person a scholar a reference d'
ARGS='v person v scholar v reference'
SPEECH_VARIABLES=[('activity','a'),('writing','a'),('audience','a'),('subject','a'),('message',MESSAGE)]
PRIMITIVES={
    'h253m':('[] a',[],'固定原文kant-1784:u0012[4735,5021)、Dagegen als Gelehrterからin seiner eigenen Person zu sprechen.までの、同じ聖職者の学識者としての無制限の自由を述べる一文全体。'),
    'h253n':('[] a',[],'同じ一文の[4782,4803)、eigentlichen Publikumという宛先の名指し箇所。r44sの各候補内の同じaudienceをceで本来の公衆と分類する箇所で、続く世界とは別の宛先を導入しない。'),
    'h253o':('[] a',[],'同じ一文の[4805,4821)、nämlich der Weltという、同じ宛先を読者世界として説明する同格箇所。r44s内の同じaudienceとceの読者世界全体という意味を受け、物理的な地球や教区内の会衆に置き換えない。'),
    'h253p':('[] a',[],'同じ一文の[4743,4831)、als Gelehrter, der durch Schriften zum eigentlichen Publikum, nämlich der Welt, spricht,という学識者の立場の特徴を述べる箇所。主語は先行する同じ聖職者であり、単発の現実の発言の報告ではなく書面で公衆に語る活動構成を述べる一般的な読みを採る。'),
    'h253q':('[] a',[],'同じ一文の[4832,4896)、mithin der Geistliche im öffentlichen Gebrauche seiner Vernunft,という、同じ聖職者をその公的理性使用の立場として説明する箇所。前の書面で世界へ語る学識者の特徴を受け、職務上の会衆への私的使用へ戻さない。'),
}
MEANINGS={
    'r442':'同じ本人・学識者の立場・固定基準に、cdの立場分類と少なくとも一つの書面による本人名義の公的発言候補r44sがある内容。活動・書面・宛先・主題・閉じた発話は同じ候補内で量化する。実際の発信、書面記録、許可や内容の真理は要求しない。',
    'r443':'同じ本人・学識者の立場・固定基準に属する全公的理性使用候補r2ziに、同じ評価点でr44xの理性使用実行への自由がある内容。書面による既実行の活動だけ、教義批評だけ、許可済みの活動だけへ範囲を縮めない。',
    'r444':'同じ本人・学識者の立場・固定基準について、全活動・書面・公衆・主題・全型適合発話のうちr44sに属する全候補に、同じ評価点のr44yの本人名義の発言実行への自由がある内容。発話を有限列に制限せず、内容の真理や現実の記録・伝達を選別条件にしない。',
    'r445':'同じ本人・立場・固定基準について、r442の非空の書面による公的発言候補と、r443の全公的理性使用候補への自由、r444の全本人名義の書面発言候補への自由を同じ評価点で結ぶ。空の対象範囲だけで無制限の自由を満たさず、両自由を別々の対象に保持する。',
    'r446':'同じ本人・学識者の立場・固定基準にcdの分類と少なくとも一つの公的理性使用候補r2ziがある内容。書面による公衆への発言構成を公的使用と説明する節の要約で、本人の実行や教示職務の不在は含めない。',
    'r447':'第五段落の固定基準で全聖職者事例r35tを受け、同じ本人の学識者の立場h247dにr445の特徴と二つの全範囲の自由を要求する全文内容。元の教会・職務・会衆は同じ事例に保持するが、公的な発言主題をその事例の教義主題だけに限定しない。',
    'r45a':'r447と同じ全聖職者事例、本人、固定基準、学識者の立場について、r442の書面を介した公衆への発言候補という特徴を述べる関係節の一般内容。現実の一発言や特定作品の出版を断言しない。',
    'r45b':'r447と同じ全聖職者事例と同じ学識者の立場について、r446の公的理性使用という特徴を述べる説明節の一般内容。mithinが受ける本人と立場を選び直さない。',
    'r45c':'全文r447と書面発言の特徴r45a・公的使用の説明r45bを同じ著者と第五段落の文脈へ帰属する。前文の私的使用r44qと同じ理性使用の次元で対照し、公衆を世界と説明する同格、書面で公衆に語ることから公的使用への説明、本文の順序を結ぶ。引用内容を実行せず、私的職務の制約を撤回しない。',
}
LIMITS=[
    'u0012[4735,5021)249非空白文字を対象とする。原刊487頁の同じ聖職者の職務上の非自由と学識者としての自由との対照を保ち、異なる人の対比に変えない。',
    'der durch Schriften ... sprichtは、学識者の立場が書面を介して本来の公衆へ語るという一般的な活動構成の特徴として読む。少なくとも一つの候補の存在を要求し、書面の現存や現に語った発言例を原文外に断言しない。空候補で全称の自由だけを満たす読みは採らない。',
    'uneingeschränkte Freiheitは、明示された学識者の公的使用という立場の中で、全r2ziの理性使用候補と全r44sの本人名義の書面発言候補へ自由が及ぶこと。全職務・全行為の無制限や、あらゆる私的生活上の発言許可を追加しない。',
    '自由は既存r37cの積極的許可と反対要求の不在という規範的な読み。genießtはその自由を持つことであり、発言の実行、快楽、物理的能力、実際の無妨害、不実行の許可を追加しない。出所h247bを教会の許可者に置き換えない。',
    'sich seiner eigenen Vernunft zu bedienenは同じ本人の公的理性使用候補の実行、in seiner eigenen Person zu sprechenは同じ本人を正の帰属先とする発言の実行。自己名義を他者名義の単なる不在や内心の確信に置き換えず、二つの自由対象を保持する。',
    'r37jの古い範囲に付く慎重な吟味・善意・教義上の欠陥・改革提案という条件を、この後続文の対象へ追加しない。公的な主題と発話を全称で取り、同じ聖職者の教示主題へ束縛しない。禁止されたり未実行であったりする候補も、分類から事後に除かない。',
    'eigentliches PublikumとWeltは同じ宛先。ceが職務の部分集団を越える全読者世界という読みを既に持ち、ufで後者が前者の説明として提示されることを保つ。別の大集団、物理的地球、現実の全世界の読了や理解へ変えない。',
    'mithinは書面で公衆へ語る学識者の特徴から公的使用という説明への接続としてudに結ぶ。Dagegenはh236kの同じ理性使用の次元で前文の職務上の私的制約と対照する。説明を客観的因果法則、対照を先行内容の撤回や矛盾としない。',
    '全称する発話記述の領域を診断用の二記述へ置き換えた検査は、全域の証明ではない。全域の有限評価は拒否し、量化構文と引数の接続、既存の候補・実行・規範の通常評価を別々に確認する。全文通読による明示解釈下の判断と検査成功を区別する。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def quant(variables,body,operator='f'):
    for n,t in reversed(variables):body=operator+' '+n+' '+t+'['+body+']'
    return body


def definitions():
    text='d r442['+FIELDS+'] e[b point['+both('k cd[v scholar v reference]',
        quant(SPEECH_VARIABLES,'k r44s['+SPEECH_ARGS+']','g'))+']].\n'
    text+=('d r443['+FIELDS+'] e[b point[f activity a[y[k r2zi[v person v activity v scholar v reference]]'+
        '[t[k r44x[v person v activity v scholar v reference]][v point]]]]].\n')
    text+='d r444['+FIELDS+'] e[b point['+quant(SPEECH_VARIABLES,
        'y[k r44s['+SPEECH_ARGS+']][t[k r44y['+SPEECH_ARGS+']][v point]]')+']].\n'
    text+='d r445['+FIELDS+'] e[b point['+both(*('t[k '+n+'['+ARGS+']][v point]' for n in ('r442','r443','r444')))+']].\n'
    text+='d r446['+FIELDS+'] e[b point['+both('k cd[v scholar v reference]',
        'g activity a[k r2zi[v person v activity v scholar v reference]]')+']].\n'
    ref='k h232v[]';case='k r35t['+' '.join('v '+n for n in NAMES)+' '+ref+']'
    args='v person k h247d[v person '+ref+'] '+ref
    for name,target in (('r447','r445'),('r45a','r442'),('r45b','r446')):
        text+='d '+name+'[] e[b point['+quant([(n,'a') for n in NAMES],
            'y['+case+'][t[k '+target+'['+args+']][v point]]')+']].\n'
    author,ctx='k wa[]','k h232o[]';quote=lambda n:'r d[k '+n+'[]]'
    claims=['k h236i[k '+node+'[] '+author+' '+quote(content)+' '+ctx+']' for node,content in (
        ('h253m','r447'),('h253p','r45a'),('h253q','r45b'))]
    claims+=['k h236k[k h253m[] '+author+' k h253g[] '+quote('r44q')+' k h253m[] '+quote('r447')+' r[p r2zg] '+ctx+']',
        'k uf['+author+' k h253n[] k h253o[] '+ctx+']',
        'k ud['+author+' i[node a][e[v node][k h253p[]]] k h253q[] '+ctx+']']
    claims+=['k ue[k '+a+'[] k '+b+'[] '+ctx+']' for a,b in (('h253g','h253m'),('h253p','h253q'),('h253n','h253o'))]
    nodes=('h253g','h253m','h253n','h253o','h253p','h253q')
    claims+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r45c[] c['+both(*claims)+'].\n'
    return text


def build():
    old,lib=parent(),dependency();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for d in lib.document['declarations']:
        n=d['name'];previous=old.entries.get(n)
        if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r45c',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='unrestricted_scholarly_freedom_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-private-conclusion-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
