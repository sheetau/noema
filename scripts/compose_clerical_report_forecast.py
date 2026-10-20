"""Describe a prospective example of the cleric's paired church reports."""
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

PARENT='examples/v016/kant-clerical-explanation.noema'
PARENT_BASIS='data/clerical-explanation-basis-v1.json'
DEPENDENCIES=('data/paired-church-reports-basis-v1.json',)
FULL='examples/v016/kant-clerical-report-forecast.noema'
CORE='examples/v016/clerical-report-forecast-core.noema'
BASIS='data/clerical-report-forecast-basis-v1.json'
ANNOTATIONS='data/clerical-report-forecast-identifiers-v1.json'
DETAILS=(('utterance','a'),('churchname','i[a]'),('judgment','i[a]'),('message',MESSAGE),('reasons','i[h[a] c]'),('audience','h[a] c'))
PRIMITIVES={
    'h247z':('[a i c[h[j[a] d] e] j[a] d d d] c',
        ['viewpoint','prospect','bindings','reference','evaluation','candidate'],
        'この視点から同じ評価文脈で、指定の段階2の内容関数へ同じ順序の個体列と固定基準を渡す内容を見込む際に採用する候補状況。対象となる人・職務等を同じ束縛で保持する。候補の選別は提示された見込みの解釈入力であり、実際に内容が成功する候補だけを事後に選ばない。非空性、将来への位置付け、各候補での内容成立は合成側で要求する。全可能世界や実現済みの履歴、数値確率、視点主体の伝記的な内心とは区別する。'),
    'h252a':('[a a i[h[a] c] d d] c',['utterance','speaker','referents','reference','point'],
        '同じ発話で同じ話者が、固定基準の下で、この閉じた範囲記述の指す対象群を、指示的にこれらとして同定して提示する。別の範囲や単なる無指定の存在と区別する。指示する身振り・物理的な位置・有限列挙は要求しない。その対象群について述べた性質や、その記述を用いる報告内容の真理をこの指示関係から導かない。'),
    'h252b':('[] a',[],'固定原文kant-1784:u0012[3794,3898)、Er wird sagenからderen sie sich bedient.まで、同じ聖職者の二つの報告を例示して見込む一文全体。'),
    'h252c':('[a a a i d[e] a i d[e] d] c',
        ['node','presenter','prior_node','prior_content','example_node','example_content','context'],
        '同じ提示者がこの箇所・文脈で、先行の説明内容を、後続箇所の指定内容が述べる具体的な場合によって例示する。先行と例示の方向を保持し、単なる隣接、例による論理的証明、唯一の可能な例、例示内容の現実の真理を要求しない。両方の段階3の内容記述を実行しない。'),
}
MEANINGS={
    'r4x':'同じ九個体・固定基準について、同じ聖職者の職務上の二報告r4wを、その基準で固定した生徒・会衆の和集合内の非空の宛先に結ぶ。論拠報告と同じ範囲記述を話者が指示するh252aも保持する。論拠の妥当性や個人的確信は評価しない。',
    'r4y':'正確な九個体列と同じ基準について、r4xを満たす発話・教会呼称・教示判断呼称・内側の発話記述・論拠範囲記述・受け手範囲が存在する内容。全て型に適合する領域を量化し、検査用の教義に限定しない。個別内容と範囲は見込みの候補ごとに異なってよいが、各候補では二報告が同じ対象を共有する。',
    'r4z':'同じ九個体・固定基準のr4yを著者が見込む候補h247zが非空であり、その全候補が評価点より先のtxに位置付き、それぞれで同じr4yが成立する。見込みを現実の発言済みや全可能世界の必然に変えず、候補ごとに異なる発話内容を許す。',
    'r42a':'第五段落の同じ基準における全聖職者事例r35tについて、同じr4zの二報告の見込みを述べる。事例の存在を追加せず、個別教義・根拠を指定せず、職務外の他の発言を制限しない。',
    'r42b':'同じ著者と第五段落の文脈へ全文r42aを段階3で帰属し、直前の職務上の教示内容の性格付けr4lを、この発言の見込みで例示する関係と本文順序を保持する。例示や帰属から内容の真理を実行しない。',
}
LIMITS=[
    'Erは直前と同じr35tの本人、unsere Kircheとsieは同じ教会を受ける。実際の職務上の発言としてのr4wは予想候補の内側に置く。原文にない固有の聖職者・教会・教義は補わない。',
    'wird sagenは、前の説明に続いて、その立場での発言を見込んで例示する読み。非空の採用候補全てについて将来的発言内容を要求し、実現済みの履歴・期日・数値確率・本人の発言意思には置き換えない。予測の哲学全体や作者意図の唯一性を証明しない。',
    'dieses oder jenesは、何を教えるかをここでは確定しない例示的な不特定表現と読む。候補内で内側の発話記述を存在量化し、二つの特定教義の論理和や排他的選択を捏造しない。全候補に一つの固定教義を要求せず、全教義を同時に教えるとも述べない。',
    'unsereの一人称複数による同じ組織の指示、教示報告から論拠報告への説明的な継続、両報告の同じ内側の内容をpaired-church-reportsから保持する。所属や教義への確信を引用から事実化しない。',
    'dasは論拠報告の同じ範囲記述を指示するh252aへ結ぶ。die Beweisgründeの非空性・同じ判断で実際に用いる論拠を尽くすことは報告内容r4qの内側に保持し、論拠の客観的支持や教義の真理は要求しない。',
    '候補内の受け手は、基準時に固定した同じ本人の生徒・会衆の和集合から非空に選ぶ。一回の発言で全生徒・会衆へ必ず同時に伝える条件は追加しない。元の職務・教会・主題と同じであることはr4wへ結ぶ。',
    '旧twは仮定上一人称とwerden ... schonの確信、fl/hzv2は経験学習に特有の候補である。今回の三人称による発言例をそれらと同一視せず、候補の一般関係h247zを明示する。将来への関係txと段階1の伝達h234gは既存の意味を再利用する。',
    '全記述域を原定義に保持する。有限診断では一部の量化を明示的に候補列へ展開し、境界を記録する。通過を意味同値性の自動証明や第五段落全体の判断へ変換しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)


def definitions():
    extra=' '.join(n+' '+s for n,s in DETAILS);values=' '.join('v '+n for n,s in DETAILS)
    office='v person v role v church v subject v utterance v churchname v judgment v message v reasons v audience'
    audience='f recipient a[y[c[v audience][v recipient]][x[k h6t[v students v recipient v reference]][k h6t[v members v recipient v reference]]]]'
    text='d r4x['+FIELDS+' '+extra+'] e[b point['+both('t[k r4w['+office+']][v point]',
        'k h252a[v utterance v person v reasons v reference v point]',audience)+']].\n'
    action='t[k r4x['+ARGS+' '+values+']][v point]'
    for name,sort in reversed(DETAILS):action='g '+name+' '+sort+'['+action+']'
    text+='d r4y[bindings j[a] reference d] e[b point['+bind(NAMES,action)+']].\n'
    seq='l[a]['+' '.join('v '+n for n in NAMES)+']'
    selected='k h247z[k wa[] r c[p r4y] '+seq+' v reference v point v candidate]'
    text+='d r4z['+FIELDS+'] e[b point['+both('g candidate d['+selected+']',
        'f candidate d[y['+selected+']['+both('k tx[v point v candidate]','t[k r4y['+seq+' v reference]][v candidate]')+']]')+']].\n'
    fixed=' '.join('v '+n for n in NAMES)+' k h232v[]'
    text+='d r42a[] e[b point['+quantify(NAMES,'y[k r35t['+fixed+']][t[k r4z['+fixed+']][v point]]')+']].\n'
    text+='d r42b[] c['+both('k h236i[k h252b[] k wa[] r d[k r42a[]] k h232o[]]',
        'k h252c[k h252b[] k wa[] k h247t[] r d[k r4l[]] k h252b[] r d[k r42a[]] k h232o[]]',
        'k ue[k h247t[] k h252b[] k h232o[]]','u[e[k h247t[]][k h252b[]]]')+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r42b',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='prospective_clerical_reports_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings,primitives=prims,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-explanation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
