"""Integrate the cleric's private-use conclusion and its two explanations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import NAMES,MESSAGE
from scripts.compose_representative_teaching import TASK_FIELDS,TASK_ARGS

PARENT='examples/v016/kant-clerical-resignation-condition.noema'
PARENT_BASIS='data/clerical-resignation-condition-basis-v1.json'
DEPENDENCY='data/delegated-teaching-freedom-basis-v1.json'
FULL='examples/v016/kant-clerical-private-conclusion.noema'
CORE='examples/v016/clerical-private-conclusion-core.noema'
BASIS='data/clerical-private-conclusion-basis-v1.json'
ANNOTATIONS='data/clerical-private-conclusion-identifiers-v1.json'
FAMILY='i c[h['+' '.join('a' for _ in NAMES)+' d a a '+MESSAGE+'] e]'
PAIR='[a a i d[e] '+FAMILY+' '+FAMILY+' d] c'
SCOPE='全体内容の同じ聖職者・職務・教会・会衆・宛先範囲・信条・主題・採用基準・固定基準・担当機会・活動・発話の束縛の下で両内容を読む。無関係な別の事例を選び直さず、内容記述を実行しない。'
PRIMITIVES={
    'h253g':('[] a',[],'固定原文kant-1784:u0012[4408,4734)、Der Gebrauch alsoからAuftrag ausrichtet.までの、会衆の前での私的使用と職務上の非自由を理由とともに述べる一文全体の箇所。'),
    'h253h':(PAIR,['node','presenter','whole','grounds','claim','context'],
        '提示者がこの箇所で、第一内容を第二内容が成り立つとする理由として提示する。客観的な論理的含意、十分条件の証明、実際の因果作用とは区別する。'+SCOPE),
    'h253i':(PAIR,['node','presenter','whole','respect','claim','context'],
        '提示者がこの箇所の第二内容を、第一内容で指定する活動・立場という点に関するものとして限定して述べる。他の活動・立場にまで無条件に一般化すること、時間的な後続や第一内容からの自動的な因果とは区別する。'+SCOPE),
    'h253j':(PAIR,['node','presenter','whole','first','additional','context'],
        '提示者がこの箇所で第一内容に加えて第二内容も成り立つと述べ、同じ論点に関する追加として位置付ける。第一内容だけから第二内容が導けるとはせず、単なる語順や数値の増加とも区別する。'+SCOPE),
    'h253k':('[a a i d[e] '+FAMILY+' d] c',['node','presenter','whole','maintained','context'],
        '提示者がこの箇所で、対象の規模がいかに大きくなる候補を考えても指定内容を維持する譲歩として提示し、規模を理由にその内容を退けるという予想を認めない。対象と全候補の範囲は同じ全体内の指定内容族で固定する。現実の巨大な対象の存在、具体的な人数上限や実際の読者の反対信念を要求しない。全体と同じ束縛の下で読み、内容記述を実行しない。'),
}
MEANINGS={
    'r44m':'同じ教示事例の内容族として、同じ会衆・教会・主題・固定基準についてr44eの全関連機会・規模での家内的性格を保持する。第一のweilで私的分類を説明する内容。',
    'r44n':'同じ教示事例の教会・本人・職務・主題・発話・固定基準をr44iへ渡し、自由な教示決定権限の現実の否定を保持する。',
    'r44o':'同じ教示事例の同じ六引数をr44jへ渡し、同じ自由内容を認めない負の規範的要求を保持する。',
    'r44p':'同じ教示事例と評価点のr44nとr44oを連言する。第二のweilが説明する、現実の非自由と同じ自由への規範的否定の内容。',
    'r44q':'第五段落の固定基準で、全聖職者事例・全担当機会・全活動・全型適合発話について、同じ会衆の前での実際の教示・理性使用r44aならr44lの私的分類・家内的性格・委託遂行・非自由と負の要求を満たすという一般内容。現に自由や許可のある例だけを量化対象にせず、特定の実行例の存在も追加しない。',
    'r44r':'一文全体r44qを同じ著者・第五段落文脈へ段階3で帰属する。家内的性格から私的分類への第一の理由、委託遂行から非自由と負の要求への第二の理由、同じ職務上の使用への限定、規範的否定の追加、規模への譲歩を同じ束縛内に結ぶ。alsoを先行の私的定義・代表教示・実益と辞職条件からの説明上の帰結提示とし、直前文からの順序も保持する。',
}
LIMITS=[
    'u0012[4408,4734)275非空白文字の一文全体を、原刊487頁の前後と照合する。任用されたLehrerは文脈上の同じ聖職者、seiner Gemeinde/dieseは同じ会衆、als Priesterは同じ職務の立場、einen fremden Auftragは本人と異なる同じ教会の受託業務を指す。',
    'Der Gebrauch ... machtは職務上の会衆への実際の教示・理性使用に関する一般文として読む。全該当事例・機会・活動・閉じた発話を量化し、該当使用なら全文の内容が成り立つという形にする。生徒だけへの活動や別の学識者としての使用を混ぜず、一つの実在する教師や発話例の存在を追加しない。',
    'bloßは同じ使用の同じ職務の立場で私的分類を満たし公的分類を満たさないという読み。私的分類そのものは既存r2zjを使い、公的分類の単なる否定で再定義しない。',
    'häusliche/Versammlung/immer/obzwar noch so großeはcongregational-private-useの明示読みを保持する。家の共同の用事になぞらえた組織内部の集会であり、同居家族や物理的家屋の事実は補わない。関連する全機会・規模で内部的性格を保ち、実際の巨大集会を断言しない。',
    'nicht freiとdarf es auch nicht seinはdelegated-teaching-freedomの同じ自由内容に対する現実の否定と負の規範要求。自由は当該教示の内容・扱いを本人の判断で決める職務上の権限。発話の実行そのものの禁止、思考不能や学識者としての公的自由の否定は加えない。規範源は同じ委託職務の責任を評価する枠組みとする。',
    '第一のweilは規模・機会によらない家内的性格から私的使用への説明、第二のweilは他者の委託の遂行から当該立場の非自由と規範的否定への説明として読む。両方とも理由の提示であり、自動的な論理的証明・因果法則・委託元の命令の正当化にはしない。',
    'in Ansehung dessenは同じ職務上の私的使用という点への限定、auchは現実の非自由に加える規範的否定の追加。obzwarは規模によって内部的性格を否定する予想への譲歩。alsoは先行説明と私的定義を受けた結論の提示とし、直前の辞職条件だけから結論を形式的に導くものとはしない。',
    '新しい談話関係は閉じた内容族を受ける一般関係で、語彙と真理条件は引用した既存合成にある。全内容は同じ十三引数の束縛内に置き、型が違う過去の談話関係の意味・検査を変更しない。',
    '原刊のPrivatgebrauch後はセミコロン、比較したAA08/038ではコロン。固定原文と原刊を保持し、句読点の版差を理由に文を分割し直さない。有限の接続検査を原文との意味同値性の自動証明とせず、全文通読の判断を別に記録する。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def definitions():
    text='d r44m['+TASK_FIELDS+'] e[b point[k r44e[v congregation v church v subject v reference v point]]].\n'
    six='v church v person v role v subject v message v reference'
    for name,target in (('r44n','r44i'),('r44o','r44j')):text+='d '+name+'['+TASK_FIELDS+'] e[k '+target+'['+six+']].\n'
    text+='d r44p['+TASK_FIELDS+'] e[b point['+both('t[k r44n['+TASK_ARGS+']][v point]','t[k r44o['+TASK_ARGS+']][v point]')+']].\n'
    args=' '.join('v '+n for n in NAMES)+' k h232v[] v occasion v activity v message'
    condition='y[t[k r44a['+args+']][v point]][t[k r44l['+args+']][v point]]'
    for n,sort in reversed([*((n,'a') for n in NAMES),('occasion','a'),('activity','a'),('message',MESSAGE)]):condition='f '+n+' '+sort+'['+condition+']'
    text+='d r44q[] e[b point['+condition+']].\n'
    prefix='k h253g[] k wa[] r d[k r44q[]] '
    pair=lambda relation,a,b:'k '+relation+'['+prefix+'r c[p '+a+'] r c[p '+b+'] k h232o[]]'
    grounds='i[node a][x[e[v node][k h236s[]]][x[e[v node][k h247t[]]][e[v node][k h2527[]]]]]'
    text+='d r44r[] c['+both('k h236i['+prefix+'k h232o[]]',
        pair('h253h','r44m','r44b'),pair('h253h','r44c','r44p'),pair('h253i','r44b','r44p'),pair('h253j','r44n','r44o'),
        'k h253k['+prefix+'r c[p r44m] k h232o[]]',
        'k ud[k wa[] '+grounds+' k h253g[] k h232o[]]',
        'k ue[k h2526[] k h253g[] k h232o[]]','u[e[k h2526[]][k h253g[]]]')+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r44r',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='clerical_private_use_conclusion_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-resignation-condition-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
