"""Join the conscientious exit condition to the preceding shared witnesses."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_example import quantify
from scripts.compose_clerical_practical_benefit import NAMES,CASE_NAMES,WITNESSES,FIELDS,ARGS,FAMILY,SCOPE

PARENT='examples/v016/kant-clerical-practical-benefit.noema'
PARENT_BASIS='data/clerical-practical-benefit-basis-v1.json'
DEPENDENCY='data/conscientious-service-exit-basis-v1.json'
FULL='examples/v016/kant-clerical-resignation-condition.noema'
CORE='examples/v016/clerical-resignation-condition-core.noema'
BASIS='data/clerical-resignation-condition-basis-v1.json'
ANNOTATIONS='data/clerical-resignation-condition-identifiers-v1.json'
PRIMITIVES={
    'h2526':('[] a',[],'固定原文kant-1784:u0012[4279,4407)、Denn glaubte erからniederlegen.まで、抵触を見いだすと信じる場合の職務遂行不能と辞職要求を述べる条件文の箇所。'),
    'h2527':('[] a',[],'固定原文kant-1784:u0012[3899,4407)、実益と説明引受けの理由を述べる文と、これに続く抵触を信じる場合の辞職条件文を合わせた連続二文の箇所。'),
    'h253a':('[a a i d[e] '+FAMILY+' d] c',['node','presenter','whole','component','context'],
        '提示者がこの文章箇所で、全体内容の一部に当たる指定内容関数を述べるものとして提示する。箇所の意味はこの全体内の当該部分であり、別の独立した量化を持つ全文へ置き換えない。'+SCOPE),
}
MEANINGS={
    'r434':'先行r43iと同じ十五引数の内容関数として、同じ宗教基準を指す閉じた第四呼称の存在を明示し、同じ本人・職務・規定群・宗教基準・固定基準と四呼称をr433へ渡す。第四呼称は仮定全体の外で選び、その全候補で保持する。本人が抵触を見いだすと信じる仮定に、良心的遂行不能と辞職要求を結ぶ。',
    'r435':'同じ十五引数と評価点の先行文内容r43iと条件文内容r434を連言する。各文を独立に存在量化して別の規定群や宗教基準を選ぶことは許さない。',
    'r436':'同じ固定基準の全聖職者事例r35tに対し、規定群・宗教基準・三呼称を一度だけ存在量化してr435の両文へ共有する。先行r43jの量化を保持して次の条件を同じ対象へ接続する。宗教基準の呼称だけはr434内で追加する。',
    'r437':'連続二文の共通内容r436を著者と第五段落文脈へ段階3で帰属し、各文の内容族を同じ量化の下で各箇所へ帰属する。前文の譲歩・理由・対照・最低限・強調も同じ共通範囲へ接続する。後続の条件文を先行文への説明として提示するud、本文順序ue、三箇所の区別を保持する。説明提示は実際の抵触不在の証明や辞職の実行ではない。',
}
LIMITS=[
    '原刊487頁と固定原文u0012[4279,4407)を、先行実益文および後続の私的使用の結論と合わせて読む。das letztereは直前の内面的宗教に反するもの、darinは同じ教会の関連規定群、erは同じ聖職者、sein Amtとesは同じ職務を指す。',
    '先行文の規定群と内面的宗教基準を同じ存在証人で共有する。前文r43iと条件文r434を連言してから一度だけ存在量化する。既存の先行文の主張を変更せず、連続二文の共通範囲を新しい主張で明示する。先行325文字は再加算しない。',
    'glaubte er ... zu findenは、本人が同じ規定群に当該抵触を自分で見いだすと信じる場合。単に抵触があると信じることや現実の抵触へ縮めず、信念の内容は実行しない。仮定を現実に偽だとする条件も補わない。perceived-doctrinal-conflictの明示読みと四呼称の一致を保持する。',
    'würde ... nicht ... könnenは、その仮定の事情を保つ全実践候補に良心上許容される同じ職務遂行がないこと。成功保証方法の不在だけでは足りない。müßteは同じ仮定下で同じ良心上の基準による辞職要求。要求の内容は同じ本人の選択に沿う将来の職務保持の終結で、要求から退任を実行しない。conscientious-service-exitの解釈を保持する。',
    'Dennは、この条件文を前文の説明として提示する働き。良心上の限界が、前文の説明引受けの可能性と無抵触の留保を説明する。仮定の帰結だけから現実の無抵触や教義の真理を論理的に証明する関係とはしない。セミコロン後の辞職要求も同じ仮定の帰結に含める。',
    '新しいh253aは全体の共通束縛内の部分内容を文章箇所へ帰属する一般関係。内容族の型は先行文のインターフェースを再利用し、語彙の内容はr43i/r434の合成に置く。本文内容や辞職条件を一つの未説明の基本関係に隠していない。',
    '有限診断は一つの外側事例と明示した呼称候補だけを使う。個体としての規定群・宗教基準の存在量化を保持し、二文の対象の食い違いを検査する。無制限の記述域の評価は拒否し、有限検査を原文との意味同値性の自動証明としない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def definitions():
    condition='k r433[v person v role v bundle v religion v reference v personname v bundlename v religionname v referencename v point]'
    text='d r434['+FIELDS+'] e[b point[g religionname i[a]['+both('e[v religion][s[v religionname]]',condition)+']]].\n'
    text+='d r435['+FIELDS+'] e[b point['+both(*( 't[k '+n+'['+ARGS+']][v point]' for n in ('r43i','r434')))+']].\n'
    fixed=' '.join('v '+n for n in NAMES)+' k h232v[]'
    args=' '.join('v '+n for n in CASE_NAMES)+' v personname v bundlename v referencename k h232v[]'
    case='t[k r435['+args+']][v point]'
    for name,sort in reversed(WITNESSES):case='g '+name+' '+sort+'['+case+']'
    text+='d r436[] e[b point['+quantify(NAMES,'y[k r35t['+fixed+']]['+case+']')+']].\n'
    prefix='k h252s[] k wa[] r d[k r436[]] '
    pair=lambda relation,a,b:'k '+relation+'['+prefix+'r c[p '+a+'] r c[p '+b+'] k h232o[]]'
    focus=lambda relation,a:'k '+relation+'['+prefix+'r c[p '+a+'] k h232o[]]'
    clauses=['k h236i[k h2527[] k wa[] r d[k r436[]] k h232o[]]',
        'k h253a['+prefix+'r c[p r43i] k h232o[]]',
        'k h253a[k h2526[] k wa[] r d[k r436[]] r c[p r434] k h232o[]]',
        pair('h252t','r43d','r43e'),pair('h252u','r43h','r43e'),pair('h252v','r43f','r43g'),
        focus('h252w','r43g'),focus('h252x','r43f'),focus('h252x','r43g'),
        'k ud[k wa[] i[node a][e[v node][k h2526[]]] k h252s[] k h232o[]]',
        'k ue[k h252s[] k h2526[] k h232o[]]']
    for a,b in (('h252s','h2526'),('h252s','h2527'),('h2526','h2527')):clauses.append('u[e[k '+a+'[]][k '+b+'[]]]')
    return text+'d r437[] c['+both(*clauses)+'].\n'


def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={};lib=dependency()
    for d in lib.document['declarations']:
        n=d['name'];previous=old.entries.get(n)
        if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r437',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='clerical_resignation_condition_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-practical-benefit-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
