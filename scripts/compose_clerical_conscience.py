"""Connect scoped conscientious non-imputability to the same clerical arrangement."""
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
from scripts.compose_protected_remarks import bind

PARENT='examples/v016/kant-clerical-public-freedom.noema'
PARENT_BASIS='data/clerical-public-freedom-basis-v1.json'
DEPENDENCIES=('data/conscientious-imputation-basis-v1.json',)
FULL='examples/v016/kant-clerical-conscience.noema'
CORE='examples/v016/clerical-conscience-core.noema'
BASIS='data/clerical-conscience-basis-v1.json'
ANNOTATIONS='data/clerical-conscience-identifiers-v1.json'
ARRANGEMENT=(*NAMES,'scholar')
PRIMITIVES={
    'h247k':('[a a i c[h[j[a] d] e] j[a] d] c',['person','matter','arrangement','bindings','reference'],
        '固定基準において、この本人の行為・実践上の立場に関し、閉じた段階2の構成記述へ正確な順の個体列と同じ基準を渡した構成それ自体に由来する事柄の完全な範囲。この事柄がその範囲に入る。構成の各部分だけでなく、それらの併存・関係に関する事柄も含める。構成に反する逸脱行為や同じ職場の無関係な出来事は含めない。引用した構成をこの関係で実行せず、無関係な生活全体へ広げず、実行・非難・正当化の成否で事後に選別しない。構成記述自体は別の合成定義で説明する。'),
    'h247l':('[a a a i d[e] a i d[e] d] c',['node','presenter','prior_node','prior_content','added_node','added_content','context'],
        '同じ提示者がこの箇所・文脈で、先行箇所の指定内容を既に置いた背景として受け、その上に第二の箇所の指定内容を加えて提示する。無順序の連言と区別して追加方向を保持する。先行の撤回、内容の真理・論理的含意、強さや意外性の順位、聞き手の同意、他の追加項目の網羅は含意しない。段階3の両内容は引用し、提示関係から実行しない。'),
    'h247m':('[] a',[],'固定原文kant-1784:u0012[3453,3527)、Es ist hiebei auch nichtsからwerden könnte.まで、先行する同じ聖職者の二立場に関して良心に帰責され得るものはないと述べる一文全体。'),
}
MEANINGS={
    'r37v':'正確な十個体列を、先行r35tの九個体と同じ本人の学識者の立場へ分ける。r35t、cd、同じ一般教示方針の義務・過去任用条件r36hと、同じ本人・学識者・教会・信条・宗教主題の公的自由・使命r37lを合わせた構成を記述する。hiebeiが受ける二立場の内容を名前だけで代用しない。',
    'r37w':'同じ十個体のr37vの構成と基準を固定し、本人に関してその構成に属する全事柄h247kをr37uへ渡す。職務上の教示と公的伝達の各側、両側の併存に関する事柄について、正当な良心的帰責の可能性を否定する。引用した構成を外側で実行しない。',
    'r37x':'第五段落の同じ基準について、全聖職者事例r35tの本人とその学識者の立場h247dを保持し、cdとr37wの範囲内の非帰責可能性を述べる。事例や実際の自責の存在を追加しない。',
    'r37y':'同じ著者・第五段落の提示文脈へr37xを段階3で帰属し、直前の公的自由・使命r37oを受けた追加h247lと本文順序を結ぶ。auchを一段強い尺度比較や先行内容の撤回には変えず、引用内容の真理を帰属から導かない。',
}
LIMITS=[
    'hiebeiは同じ聖職者の職務上の教示と学識者としての公的伝達、およびその二立場の併存を受けるという明示した読み。r37vで先行の九個体と学識者を正確に結び、原文外の別人物・別教会・別信条・全人生へ広げない。',
    '事柄の範囲h247kは指定した構成それ自体に関する全項目で、単独の実行活動だけではない。両立場の併存についての事柄を含め、無害な項目・既に非難した項目・成功した活動だけへ事後に縮めない。記述に反する逸脱行為一般の免責へは広げない。現実に何が属するかの完全な決定手続を有限検査で証明しない。',
    'nichtsはこの固定範囲内の全対象への否定、könnteは同じ事柄を保持する候補のいずれかで正当化できる道徳的自己帰責があるという可能性。実際の自責・罪悪感の欠如、心理的な誤った非難の不可能性、教義の真理とは分ける。',
    '良心は既存smと同じfa/seの機能上の自己判断を用いる。h247hの帰責内容、h247iの正当化、h247jの候補範囲を別に保持し、その意味規約と一般理論の限界はconscientious-imputationの記録を引き継ぐ。',
    '先行の構成をh247kへ引用することで範囲を固定する。先行の教示義務・任用・自由・使命の真理や実行を新しい一文の外側の条件に追加しない。単なる同時点の真偽一致で他の構成へ置き換えない。',
    'auchは、先に提示した公的自由・使命を受けて、良心に関する否定も加えるという論述上の読み。別の人物に同じ否定が成立するという主張、sogarの意外性の尺度や因果を補わない。',
    '原刊486頁と先行二文・次のDennの開始、および依存定義群を照合した明示解釈下のアシスタント判断。有限診断と型付き境界は意味同値性の自動証明、独立査読、第五段落全体の意味確認ではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)


def args(names):return ' '.join('v '+n for n in names)+' v reference'
def fields(names):return ' '.join(n+' a' for n in names)+' reference d'
def seq(names):return 'l[a]['+' '.join('v '+n for n in names)+']'


def definitions():
    arrangement=both('k r35t['+args(NAMES)+']','k cd[v scholar v reference]',
        't[k r36h['+args(NAMES)+']][v point]',
        't[k r37l[v person v scholar v church v creed v subject v reference]][v point]')
    text='d r37v[bindings j[a] reference d] e[b point['+bind(ARRANGEMENT,arrangement)+']].\n'
    scope='i[matter a][k h247k[v person v matter r c[p r37v] '+seq(ARRANGEMENT)+' v reference]]'
    text+='d r37w['+fields(ARRANGEMENT)+'] e[k r37u[v person '+scope+' v reference]].\n'
    ref='k h232v[]';scholar='k h247d[v person '+ref+']'
    case='k r35t['+' '.join('v '+n for n in NAMES)+' '+ref+']'
    claim='t[k r37w['+' '.join('v '+n for n in NAMES)+' '+scholar+' '+ref+']][v point]'
    text+='d r37x[] e[b point['+quantify(NAMES,'y['+case+']['+both('k cd['+scholar+' '+ref+']',claim)+']')+']].\n'
    author,ctx='k wa[]','k h232o[]'
    text+='d r37y[] c['+both(
        'k h236i[k h247m[] '+author+' r d[k r37x[]] '+ctx+']',
        'k h247l[k h247m[] '+author+' k h247e[] r d[k r37o[]] k h247m[] r d[k r37x[]] '+ctx+']',
        'k ue[k h247e[] k h247m[] '+ctx+']','u[e[k h247e[]][k h247m[]]]')+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r37y',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='clerical_scoped_conscientious_non_imputability',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings,primitives=prims,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-public-freedom-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
