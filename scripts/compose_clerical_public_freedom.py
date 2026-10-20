"""Integrate the clergyman's scholarly freedom, calling and discourse contrast."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_example import quantify
from scripts.compose_confessional_teaching import NAMES

PARENT='examples/v016/kant-clerical-obligation.noema'
PARENT_BASIS='data/clerical-obligation-basis-v1.json'
DEPENDENCIES=('data/scholarly-mission-basis-v1.json',)
FULL='examples/v016/kant-clerical-public-freedom.noema'
CORE='examples/v016/clerical-public-freedom-core.noema'
BASIS='data/clerical-public-freedom-basis-v1.json'
ANNOTATIONS='data/clerical-public-freedom-identifiers-v1.json'
PRIMITIVES={
    'h247d':('[a d] a',['person','reference'],
        '同じ本人が職務上の委任と区別して、自ら理性を用い本来の読者世界へ向けて語る学識者の立場を、この固定基準で参照する。cdの分類と具体的な活動のr2ziは別に要求する。免許・学位・任命や、既に発言した事実を参照だけで補わない。'),
    'h247e':('[] a',[],'固定原文kant-1784:u0012[3186,3452)、Aber als Gelehrterからdem Publikum mitzutheilen.までの、同じ聖職者の公的な伝達の自由と使命を述べる一文全体。'),
    'h247f':('[] a',[],'同じ一文の[3186,3227)、Aber als Gelehrter hat er volle Freiheit,という自由節の主部を指す箇所。内容は後続の共有不定詞句[3253,3452)を補って読む。'),
    'h247g':('[] a',[],'同じ一文の[3228,3252)、ja sogar den Beruf dazu,という追加される使命節の主部を指す箇所。前の本人・学識者の立場と後続の共有不定詞句[3253,3452)を受ける。'),
}
MEANINGS={
    'r37m':'第五段落の同じ基準h232vで、先行する全聖職者事例r35tの同じ本人・教会・信条・宗教主題を、本人の同じ学識者の立場h247dとr37jの全対象の公的伝達の自由へ結ぶ。職務上の教示の実行・信条の真理を前提にしない。',
    'r37n':'r37mと同じ全聖職者事例、本人・教会・信条・主題・学識者の立場について、r37kの全対象を公に伝える課題を述べる。職務上の信条に沿う教示義務や案の採用義務へ置き換えない。',
    'r37o':'同じ評価点で自由r37mと使命r37nを合わせる一文全体の内容。自由から使命、使命から許可・実行を推論せず、二つの規範内容を独立に保持する。',
    'r37p':'同じ著者の固定基準の期待比較で、自由と使命の自己比較が成立し、自由は使命以上に見込まれ逆は不成立という追加焦点の背景。数値確率、義務の論理的強さ、内容の現実の真理を補わない。',
    'r37q':'全文・自由節・使命節を同じ著者と第五段落の提示文脈へ帰属し、h245kでja sogarの追加焦点とr37pの期待背景を結ぶ。h236kで直前の職務上の教示義務・任用条件r36kと同じ公私使用の次元r2zgで対照し、本文順序を保持する。引用内容は実行しない。',
}
LIMITS=[
    '先行文のr35tの全一般事例をそのまま受け、erとjenem Symbolを同じ本人と信条へ結ぶ。唯一の実在者、実際の教示、信条の真理を公的活動の前提にしない。als Gelehrterは本人の学識者の立場であり、職務委託とは別に保持する。',
    'alleとvolleは固定した分類に属する全見解・全提案と、その全公的伝達候補への自由として読む。自由は積極的許可と反対要求の不在であり、実行済み・真なる内容・許可済みの候補だけへ範囲を縮めない。物理的な無妨害や不実行への許可を補わない。',
    'seine Gedankenは同じ本人の肯定する見解。sorgfältig geprüftは同じ内容を基準点以前に一応の結論まで吟味し、固定した全関連事項へ注意を配ること、wohlmeinendは同じ見解判断で他者の利益をそれ自体求める目的と読む。真理・成功・他の動機の不在を要求しない。',
    'über das Fehlerhafteは同じ信条の備えるべき条件の不充足を論点として扱う読み。見解全体を一つの単純な否定命題へ縮めず、欠点の現実の実在を著者の別主張として加えない。',
    'Vorschlägeは本人の改善提案。宗教と教会の営みの構成を、基準時の現行構成と同じ評価基準で厳密に比較し、候補の改善と実施を提案内容へ引用して渡す。単なる比較評言・建物の配置・実施済みと同一視しない。吟味と善意の修飾はGedankenにかけ、提案側へ追加しない。',
    'dem Publikum mitzutheilenは本来の全読者世界への同じ内容の提示とする。非空の全宛先への提示を保持し、実際の全員の受領・理解・賛同を要件にしない。自由と使命の双方がこの共有不定詞句を受ける。',
    'Berufは公的伝達への課題という規範的な読み。解釈で指定した課題期間内に各項目をいずれかの方法・時機で伝える方針を要求する。原文にない日時・締切、全候補方法の実行、全案の採用・実施の義務を補わない。学識者の規範源h247bを雇用教会の命令権と同一化しない。',
    'ja sogarは先行する自由に使命まで加える強調として、二節の帰属と期待背景を結ぶ。背景を主たる世界内容へ混ぜず、義務から自由を導く論理規則や著者の実測心理へ変えない。',
    'Aberは同じ人の職務上の制約と学識者としての公的自由・使命との対照。先行の教示義務を撤回せず、二つの立場が論理的に矛盾するともしない。',
    '意味判断は原刊486頁と依存定義群の通読による明示解釈下のアシスタント判断。有限診断・型付き境界・引用の非事実性の検査は意味同値性の自動証明、独立査読、現実の全範囲の網羅性の証明ではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)


def definitions():
    ref='k h232v[]';case='k r35t['+' '.join('v '+n for n in NAMES)+' '+ref+']'
    scholar='k h247d[v person '+ref+']'
    args='v person '+scholar+' v church v creed v subject '+ref
    text=''
    for name,target in [('r37m','r37j'),('r37n','r37k')]:
        text+='d '+name+'[] e[b point['+quantify(NAMES,'y['+case+']['+both('k cd['+scholar+' '+ref+']',
            't[k '+target+'['+args+']][v point]')+']')+']].\n'
    text+='d r37o[] e[b point['+both('t[k r37m[]][v point]','t[k r37n[]][v point]')+']].\n'
    compare=lambda a,b:'k h245j[k wa[] r c[k '+a+'[]] r c[k '+b+'[]] '+ref+']'
    text+='d r37p[] e[b point['+both(compare('r37m','r37m'),compare('r37n','r37n'),
        compare('r37m','r37n'),'u['+compare('r37n','r37m')+']')+']].\n'
    author,ctx='k wa[]','k h232o[]';quote=lambda n:'r d[k '+n+'[]]'
    claims=['k h236i[k '+node+'[] '+author+' '+quote(content)+' '+ctx+']' for node,content in (
        ('h247e','r37o'),('h247f','r37m'),('h247g','r37n'))]
    claims+=['k h245k[k h247e[] '+author+' k h247f[] '+quote('r37m')+' k h247g[] '+quote('r37n')+' '+quote('r37p')+' '+ctx+']',
        'k h236k[k h247e[] '+author+' k h246q[] '+quote('r36k')+' k h247e[] '+quote('r37o')+' r[p r2zg] '+ctx+']',
        'k ue[k h246q[] k h247e[] '+ctx+']','k ue[k h247f[] k h247g[] '+ctx+']']
    claims+=['u[e[k '+a+'[]][k '+b+'[]]]' for a,b in [('h246q','h247e'),('h247e','h247f'),('h247e','h247g'),('h247f','h247g')]]
    text+='d r37q[] c['+both(*claims)+'].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r37q',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='clerical_scholarly_freedom_calling_and_contrast',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings,primitives=prims,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-obligation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
