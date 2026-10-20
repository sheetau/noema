"""Present the same teaching content as prescribed, commissioned exposition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_example import quantify
from scripts.compose_confessional_teaching import NAMES,FIELDS,ARGS,MESSAGE
from scripts.compose_protected_remarks import bind

PARENT='examples/v016/kant-clerical-conscience.noema'
PARENT_BASIS='data/clerical-conscience-basis-v1.json'
DEPENDENCIES=('data/teaching-discretion-basis-v1.json',)
FULL='examples/v016/kant-clerical-explanation.noema'
CORE='examples/v016/clerical-explanation-core.noema'
BASIS='data/clerical-explanation-basis-v1.json'
ANNOTATIONS='data/clerical-explanation-identifiers-v1.json'
PROPERTY='i c[h[j[a] '+MESSAGE+' d] e]'
PRIMITIVES={
    'h247r':('[a a a a '+MESSAGE+' '+PROPERTY+' j[a] d d] c',
        ['speaker','activity','recipient','subject','message','characterization','bindings','reference','point'],
        'この話者は同じ活動でこの受け手に、同じ主題の同じ閉じた発話内容を、指定の段階2の内容関数へ順序付き個体列・その同じ発話記述・固定基準を渡した性質を備えるものとして提示する。人物・活動・宛先・発話の実際の伝達は別に結ぶ。性質を提示していることと、その性質や内側の発話内容が真であることを分け、引用した性質をここで実行しない。'),
    'h247s':('[a a a a '+MESSAGE+' '+PROPERTY+' '+PROPERTY+' j[a] d d] c',
        ['speaker','activity','recipient','subject','message','negative_characterization','positive_characterization','bindings','reference','point'],
        'この話者は同じ活動・受け手・主題・発話について、同じ束縛列・発話・基準を受ける第一の否定的な性格付けに対して、第二の肯定的な性格付けを代わる説明として対置する。内容の否定と肯定は各関数で明示し、ここで二重に否定しない。単なる順序のない連言、意外性の尺度、二内容の論理的排他性や真理を要求しない。'),
    'h247t':('[] a',[],'固定原文kant-1784:u0012[3528,3793)、Dennからangestellt ist.までの、職務として教示する内容の提示の仕方を、直前の良心の文の説明として述べる一文全体。'),
}
MEANINGS={
    'r4g':'同じ九個体と固定基準について、代表教示の一般方針への現任用r4cがあり、この同じ主題・閉じた発話記述が、同じ信条の同じ採用条件列を評価点で満たすという性格付け。一般的な任用だけで任意の内容を任用対象とせず、この発話の規定適合も引用内容内に保持する。',
    'r4h':'正確な九個体列と同じ発話・基準から、同じ教会・本人・職務・主題についての自由な教示内容決定権限の否定r4eを構成する。外側の教示内容を別の発話へ差し替えない。',
    'r4i':'同じ九個体列と同じ発話・基準を、規定に沿う同じ内容を教会の名で述べる現任用の性格付けr4gへ接続する。',
    'r4j':'同じ束縛列・発話・基準・評価点についてr4hの否定とr4iの任用の性格付けを合わせる。本人による提示に引用するための全内容であり、二つの関係を相互に導出しない。',
    'r4k':'同じ職務上の業務担当者の実際の教示r372について、実際にその同じ発話を伝えた全担当宛先へ、その発話をr4jのようなものとして提示し、r4hとr4iを訂正的に対置する。教示内容自体とその性格付けを分け、引用した裁量否定・任用・規定適合を外側で実行しない。',
    'r4l':'第五段落の固定基準について、同じ全聖職者事例・全担当機会・全活動・全型適合発話で、職務上の業務担当者の実際の教示r372があれば同じr4kの提示をするという一般内容。実行例の存在を追加せず、was/das/dessenを同じ主題・発話へ束縛する。',
    'r4m':'全文r4lを同じ著者と第五段落の提示文脈へ段階3で帰属し、本箇所を直前の良心の文h247mの説明としてudで結ぶ。Dennを因果や論理的十分性の自動導出に変えず、本文順序を保持する。',
}
LIMITS=[
    'was ... lehrt / das / dessen / dasは同じ本人の同じ職務上の教示の主題と閉じた発話内容を受ける。全型適合発話を扱い、一つの模範例や自然言語の埋込みで代用しない。zu Folge seines AmtsとGeschäftträgerはr372の同じ職務・教会・業務担当・実行へ結ぶ。',
    'stellt er als etwas vorは、同じ教示内容を指定の制度的性格を備えるものとして本人が提示する読み。性格付けは段階2で引用し、話者の提示からその真理や教義の真理を導かない。実際の教示を受けた担当宛先について全てこの提示を要求する。',
    'nicht freie Gewalt ... nach eigenem Gutdünkenは内容決定権限と本人の判断を最終基準にできることの組合せの否定。物理的な教示不能・不実行・全ての局所的な実務判断の禁止へ強めない。',
    'nach Vorschrift / im Namen eines andern / angestelltは同じ教会への現任用、同じ全担当機会の代表教示方針と、当該発話の同じ採用基準への適合を引用内で結ぶ。本人と異なる委託元は同じ教会とし、別の上司名・儀礼・法的有効性を補わない。',
    '一般方針は期間内の履行存在と全追加教示の適合・代表を保持する。任意の一活動の条件に縮めず、全方法の実行や全時点の連続発言にも強めない。実際の発話に合わせて基準列や担当宛先を選び直さない。',
    'sondernは本人がその内容をどう提示するかの中で、自由な自己裁量の否定と他者の規定・名による任用を対置する。単なる著者の段落順序として代用せず、二内容の真理や排他性を外側へ出さない。',
    'Dennは本一文を直前の良心の否定の説明として著者が提示する関係。説明の十分性、命題の論理的含意、どんな職務行為も無条件に免責されることは追加しない。後続の確信・内面の宗教との抵触・辞職条件は別に記述する。',
    '原刊486/487頁と依存構成の通読による明示解釈下の判断。型付き境界・二発話への診断展開・有限検査を意味同値性の自動証明や第五段落全体の判断としない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)


def definitions():
    text='d r4g['+FIELDS+' message '+MESSAGE+'] e[b point['+both(
        't[k r4c['+ARGS+']][v point]',
        'k r35s[v church v creed v subject v standard v reference]',
        't[k rfu[v subject v message s[k h246j[v standard v reference]]]][v point]')+']].\n'
    for name,body in [('r4h','t[k r4e[v church v person v role v subject v message v reference]][v point]'),
        ('r4i','t[k r4g['+ARGS+' v message]][v point]')]:
        text+='d '+name+'[bindings j[a] message '+MESSAGE+' reference d] e[b point['+bind(NAMES,body)+']].\n'
    text+='d r4j[bindings j[a] message '+MESSAGE+' reference d] e[b point['+both(
        't[k r4h[v bindings v message v reference]][v point]',
        't[k r4i[v bindings v message v reference]][v point]')+']].\n'
    task=ARGS+' v occasion v activity v message';seq='l[a]['+' '.join('v '+n for n in NAMES)+']'
    reached=both('k h246o[v occasion v recipient v reference]','k f2[v activity v recipient v subject v message v point]')
    prefix='v person v activity v recipient v subject v message '
    meta=both('k h247r['+prefix+'r c[p r4j] '+seq+' v reference v point]',
        'k h247s['+prefix+'r c[p r4h] r c[p r4i] '+seq+' v reference v point]')
    text+='d r4k['+FIELDS+' occasion a activity a message '+MESSAGE+'] e[b point['+both(
        't[k r372['+task+']][v point]','f recipient a[y['+reached+']['+meta+']]')+']].\n'
    fixed=' '.join('v '+n for n in NAMES)+' k h232v[] v occasion v activity v message'
    inner='f message '+MESSAGE+'[y[t[k r372['+fixed+']][v point]][t[k r4k['+fixed+']][v point]]]'
    text+='d r4l[] e[b point['+quantify((*NAMES,'occasion','activity'),inner)+']].\n'
    text+='d r4m[] c['+both('k h236i[k h247t[] k wa[] r d[k r4l[]] k h232o[]]',
        'k ud[k wa[] i[node a][e[v node][k h247t[]]] k h247m[] k h232o[]]',
        'k ue[k h247m[] k h247t[] k h232o[]]', 'u[e[k h247m[]][k h247t[]]]')+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r4m',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='clerical_exposition_characterized_as_prescribed_representative_appointment',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings,primitives=prims,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-conscience-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
