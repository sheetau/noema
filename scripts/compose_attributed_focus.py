"""Reuse scoped claim/background attribution for a closed dissemination pair."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_described_dissemination import declaration
from scripts.compose_thinking_disseminators import call as k
from scripts.compose_scalar_backgrounds import PAIR,CC
from scripts.compose_focused_dissemination import FRAME,PREDICATE
from scripts.compose_focused_permission import basis as permission_basis
from scripts.compose_policy_recognition import basis as policy_basis

PARENT='examples/v016/kant-expected-focus.noema'
PARENT_BASIS='data/expected-focus-basis-v1.json'
FULL='examples/v016/kant-attributed-focus.noema'
CORE='examples/v016/attributed-focus-core.noema'
LIBRARY='examples/v016/attributed-content-pairs.noema'
BASIS='data/attributed-focus-basis-v1.json'
REUSED='examples/v016/kant-focused-permission.noema'
IMPORTED=('rtq','hznreport','hzrbgreport')
GUARDIAN=[('governed','i[a]'),('appoints','i[h[a a a a d] c]'),('guardianrole','i[h[a a d] c]')]
MEANINGS={
 'rqtu':'階数2の閉じた内容記述へ、階数3の恒等関数記述を適用し、同じ内容を返す閉じた階数3の記述にする。引用の構成であり、内容やその内部の基本関係を評価しない。元と変換後の構文同一性は要求しない。',
 'rqtv':'同じ組から主張と背景を一回ずつ取り出し、rqtuで既存rtqの引用階数へ接続する。同じ箇所・著者・文脈を共用し、主張範囲と背景範囲は別に渡す。既存hznreportとhzrbgreportで帰属し、内容の真理や背景の実際の成立を含意しない。',
 'hzpx':'同じ公衆の閉じた記述、任用関係、後見役関係から、hzhbを呼ぶ閉じた部分集団述語を構成する。人物と時点は述語の引数に残し、別人・別時点の任用を補わない。',
 'hzpy':'指定した閉じた条件付き内容の枠とhzpxの後見役述語をhzpwへ渡し、主張と期待背景を同じ理由側箇所hzp5・著者wa・提示文脈hzp3へrqtvで帰属する。主張範囲hzpzと背景範囲hzq2を区別する。枠と公衆・任用・役割の解釈は明示した引数として必要である。',
}
REFERENCES={
 'hzpz':'カント1784のu0011、原文位置137以上448未満の伝播を述べる節の範囲。範囲への参照であり、その全文内容が記述済みであることは含意しない。',
 'hzq2':'同じu0011の原文位置178以上217未満、sogarと任用された後見役を焦点として示す範囲。主張全体の範囲や、期待比較の評価時点とは区別する。',
}
LIMITS=[
 '既存rtq・hznreport・hzrbgreportの宣言と意味を再利用する。異なる引用階数で同じ帰属の基本関係を増やさず、閉じた恒等適用で接続する。',
 '引数を満たした接続例は、自由の条件・存在する伝播・後見役・期待背景を同じ帰属へ渡す。原文に適した全ての履歴・公衆・評価基準・範囲の解釈を確定したわけではない。',
 '帰属は内容の真理とは独立である。帰属の検査で世界の事実を未知のまま保持できることは、任意長の伝播内容の真理の証明ではない。',
 '本文34文と意味確認済み七単位を保持する。帰属用の引数付き定義を追加するが、新しい無条件の本文主張と原文対応文字は増やさない。',
]


def definitions():
    text=declaration('rqtu',[('content',CC)],'i d[e]','o a[r d[i[value e][v value]]][v content]')
    fields=[('node','a'),('author','a'),('package',PAIR),('foregroundscope','a'),('backgroundscope','a'),('context','d')]
    text+=declaration('rqtv',fields,'c',k('rtq','v node','v author',k('rqtu',k('rsu','v package')),
        k('rqtu',k('rsv','v package')),'v foregroundscope','v backgroundscope','v context','p hznreport','p hzrbgreport'))
    factory='r[i[governed a appoints h[a a a a d] c guardianrole h[a a d] c][i[person a point d]['+k('hzhb','v person','v governed','v point','v appoints','v guardianrole')+']]]'
    text+=declaration('hzpx',GUARDIAN,PREDICATE,'o a['+factory+']['+' '.join('v '+n for n,t in GUARDIAN)+']')
    package=k('hzpw','v frame',k('hzpx',*('v '+n for n,t in GUARDIAN)))
    text+=declaration('hzpy',[('frame',FRAME)]+GUARDIAN,'c',k('rqtv',k('hzp5'),k('wa'),package,k('hzpz'),k('hzq2'),k('hzp3')))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not (set(IMPORTED)|set(MEANINGS)|set(REFERENCES))&set(old.entries)
    source=parse((ROOT/REUSED).read_text(encoding='utf-8'));imported=[d for d in source['declarations'] if d['name'] in IMPORTED]
    assert len(imported)==3
    size=len(doc['declarations']);doc['declarations']+=deepcopy(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+'[] a.' for n in REFERENCES)+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzpy','rqtp','hzps','hzny','rqsx','rsw'])
    library=deepcopy(doc);library['statements']=[];library['declarations']=closure(doc,['rqtv','rst','rsw','rsx','rsy'])
    descriptions={'hznreport':policy_basis()['bindings']['hznreport'],'hzrbgreport':permission_basis()['bindings']['hzrbgreport'],**REFERENCES}
    args={'hznreport':['node','author','content','scope','context'],
        'hzrbgreport':['node','author','foreground','background','foreground_scope','background_scope','context'],**{n:[] for n in REFERENCES}}
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=args[d['name']],meaning_ja=descriptions[d['name']])
        for d in doc['declarations'][size:] if d['kind']=='primitive'}
    basis=dict(status='shared_source_attribution_of_foreground_and_expectation_background',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions={'rtq':permission_basis()['definitions']['rtq'],**MEANINGS},
        reused_declarations=dict(document=REUSED,names=list(IMPORTED)),new_local_references=REFERENCES,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Scoped attribution reused for closed content pairs',flush=True)


if __name__=='__main__':main()
