"""Integrate the cleric's practical benefit sentence with shared scoped contents."""
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

PARENT='examples/v016/kant-clerical-report-forecast.noema'
PARENT_BASIS='data/clerical-report-forecast-basis-v1.json'
DEPENDENCIES=tuple('data/'+n+'-basis-v1.json' for n in ('practical-benefit-extraction','personal-endorsement-case','latent-truth-compatibility'))
FULL='examples/v016/kant-clerical-practical-benefit.noema'
CORE='examples/v016/clerical-practical-benefit-core.noema'
BASIS='data/clerical-practical-benefit-basis-v1.json'
ANNOTATIONS='data/clerical-practical-benefit-identifiers-v1.json'
CASE_NAMES=(*NAMES,'bundle','religion')
WITNESSES=(('bundle','a'),('religion','a'),('personname','i[a]'),('bundlename','i[a]'),('referencename','i[d]'))
FIELDS=' '.join(n+' a' for n in CASE_NAMES)+' personname i[a] bundlename i[a] referencename i[d] reference d'
ARGS=' '.join('v '+n for n in CASE_NAMES)+' v personname v bundlename v referencename v reference'
FAMILY='i c[h['+' '.join('a' for _ in CASE_NAMES)+' i[a] i[a] i[d] d] e]'
PAIR='[a a i d[e] '+FAMILY+' '+FAMILY+' d] c'
FOCUS='[a a i d[e] '+FAMILY+' d] c'
SCOPE='全体内容内の同じ束縛位置へ各内容関数を適用して読む。同じ個体・呼称・基準を共有し、別の存在証人を選び直さない。内容記述は実行せず、全体の量化の外で無条件の真理を主張しない。'
PRIMITIVES={
    'h252s':('[] a',[],'固定原文kant-1784:u0012[3899,4278)、Er zieht alsdannからangetroffen wird.まで、実益・本人の確信・説明の引受けとその理由を述べる一文。'),
    'h252t':(PAIR,['node','presenter','whole','acknowledged','maintained','context'],
        '提示者がこの箇所で、第一内容を認めても、それによって第二内容を退けるべきだという予想には従わず、第二内容をなお維持する譲歩として提示する。論理的矛盾や実際の読者の期待は要求しない。'+SCOPE),
    'h252u':(PAIR,['node','presenter','whole','grounds','claim','context'],
        '提示者がこの箇所で、第一内容を第二内容が成り立つとする理由として提示する。内容間の論理的含意、実際の因果作用、十分条件の客観的証明とは区別する。'+SCOPE),
    'h252v':(PAIR,['node','presenter','whole','first','second','context'],
        '提示者がこの箇所で、第一内容に対して第二内容を対照して続ける。両内容の矛盾・排他的選択・第一内容の撤回を要求しない。'+SCOPE),
    'h252w':(FOCUS,['node','presenter','whole','minimum','context'],
        '提示者がこの箇所で、より強い確保事項を留保しつつ、指定内容は最低限確保されるものとして位置付ける。数値の下限、唯一の真理、他の全ての内容の否定には置き換えない。'+SCOPE),
    'h252x':(FOCUS,['node','presenter','whole','emphasized','context'],
        '提示者がこの箇所で、指定内容を改めて押し出し、なお認めるべきこととして強調する。実際の読者の既知性や反対信念、新しい真理条件を要求しない。'+SCOPE),
    'h252y':('[a a a i d[e] a i d[e] i d[e] d] c',
        ['node','presenter','prior_node','prior_content','background_node','background_content','current_content','context'],
        '提示者がこの箇所で、直前の例示内容とその背景内容で示された場合を受け、その同じ場合ならそこで次に指定内容が成り立つ、という説明の継続として位置付ける。先行・背景・現在の内容に共通する事例の束縛を対応させる。厳密な時刻差、予告発話の実現済み、因果的含意、内容の現実の真理は要求せず、段階3の内容を実行しない。'),
}
MEANINGS={
    'r43c':'同じ十一個体・三呼称・固定基準の内容関数として、本人が同じ規定群からその会衆への全実益を得るr43bを保持する。他の枝と共通の引数を受け、実益には宗教基準や本人の確信を追加しない。',
    'r43d':'同じ束縛の本人・規定群・基準の閉じた呼称をr424へ渡し、本人自身の見解を問われる場合に十分な確信で賛同しないという仮定的内容を保持する。',
    'r43e':'同じ本人・職務・教会・対象者・規定群についてr42sの説明を責任をもって引き受けられる内容を保持する。実際の引受けや説明の履行を要求しない。',
    'r43f':'同じ本人・規定群・固定基準にr42wを適用し、隠れた真理の可能性を全排除できないという内容を保持する。',
    'r43g':'同じ本人・規定群・宗教主題・内面的宗教基準についてr42yの全検討場合での抵触不在を保持する。',
    'r43h':'同じ十五引数と評価点でr43fとr43gを連言する。理由節の内容であり、可能性と全場合の無抵触を論理和にしない。',
    'r43i':'同じ十五引数と評価点で、実益r43c・仮定的な十分な賛同の否定r43d・引受け可能性r43e・理由節r43hを連言する。枝ごとに規定群や呼称を選び直さない。',
    'r43j':'同じ基準の全聖職者事例r35tに対し、同じ規定群・内面的宗教基準・本人と規定群と基準の三閉じた呼称があり、r43iの全内容を満たす。Satzungenを関連する規定群の存在として読む。無名の任意個体のコードを捏造せず、必要な呼称の存在を明示する。',
    'r43k':'全文r43jを同じ著者と第五段落文脈へ段階3で帰属し、同じ内容の束縛内にgleichwohlの譲歩、weilの理由、aberの対照、wenigstensの最低限の保証、二つのdochの強調を位置付ける。alsdannの文脈継続と前文からの本文順序も保持する。内容の真理を帰属から実行しない。',
}
LIMITS=[
    '同じ聖職者が教会の代表として説明する場合の継続として全文を読む。alsdannをその場合そこで、という説明上の継続とし、予告された発話の実現済みや厳密な時間差は追加しない。現在形ziehtはこの代表的な場合で成立する実益として、著者帰属の内側に置く。',
    'Satzungenは同じ教会の関連する複数の規定の群。その固定した全成員の内容をr42j/r42h/r42iで共有する。教会の全歴史上の制定規定を一括して対象にする読みではない。各枝で別の規定群を使うことは許さない。',
    'allen praktischen Nutzenは固定した事情で得られる実益の全ての面を得る強い読み。範囲は達成済みの結果から逆算せず、同じ複合的でもよい活動へ結ぶ。会衆という共同の受益対象を保持し、全成員に同一の利益を要求しない。',
    'er selbst ... würdeは本人自身の賛同を問う機会の仮定を補う。否定は十分な確信で規定群全体に賛同することへ掛け、各規定の偽や現実の否定判断へ強めない。閉じた三呼称を同じ仮定前提へ渡す。',
    'gleichwohlは仮定的な十分な賛同の否定に対して説明引受けの可能性を維持する譲歩。weilの理由は隠れた真理の可能性と無抵触の連言からこの引受け可能性へ掛け、実益の発生への直接因果関係にはしない。',
    'nicht ganz unmöglich/verborgen läge/auf alle Fälle/innere Religion/angetroffen wirdはlatent-truth-compatibilityの明示読みを保持する。真理検討・本人の判断・実践可能性の三候補範囲を同一化しない。内面の宗教と両立するだけで良心上の許容や実践可能性を自動導出しない。',
    'aberは可能性と全場合の抵触不在を対照する。wenigstensは後者を最低限の保証として提示し、dochの二箇所はそれぞれの内容をなお認めるべきこととして強調する。談話上の位置付けは別条件であり、数値確率・実際の読者の信念・教義の真理を補わない。',
    '新しい談話関係は閉じた同じ型の内容関数を再利用する一般関係。十一個体・三呼称・固定基準の順序はこの統合でのインターフェースであり、原文一文を隠した基本述語ではない。全体内容内の同じ量化の下で読むことを意味規約に明示する。',
    '原刊487頁の前後を含め通読する。後続の抵触を認めた場合の辞職条件を打ち消さず、無条件の在職正当化にはしない。有限診断は接続の検査であり、全記述域の評価や意味同値性の自動証明ではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)


def definitions():
    ten=' '.join('v '+n for n in (*NAMES,'bundle'))+' v reference'
    bodies={
        'r43c':'k r43b['+ten+' v point]',
        'r43d':'k r424[v person v church v creed v subject v standard v bundle v reference v personname v bundlename v referencename v point]',
        'r43e':'k r42s['+ten+' v point]',
        'r43f':'k r42w[v person v bundle v reference v point]',
        'r43g':'k r42y[v person v bundle v subject v religion v reference v point]',
    }
    invoke=lambda name:'t[k '+name+'['+ARGS+']][v point]'
    bodies['r43h']=both(invoke('r43f'),invoke('r43g'))
    bodies['r43i']=both(*(invoke(n) for n in ('r43c','r43d','r43e','r43h')))
    text=''.join('d '+n+'['+FIELDS+'] e[b point['+body+']].\n' for n,body in bodies.items())
    fixed=' '.join('v '+n for n in NAMES)+' k h232v[]'
    case_args=' '.join('v '+n for n in CASE_NAMES)+' v personname v bundlename v referencename k h232v[]'
    case='t[k r43i['+case_args+']][v point]'
    for name,sort in reversed(WITNESSES):case='g '+name+' '+sort+'['+case+']'
    text+='d r43j[] e[b point['+quantify(NAMES,'y[k r35t['+fixed+']]['+case+']')+']].\n'
    prefix='k h252s[] k wa[] r d[k r43j[]] '
    pair=lambda relation,first,second:'k '+relation+'['+prefix+'r c[p '+first+'] r c[p '+second+'] k h232o[]]'
    focus=lambda relation,content:'k '+relation+'['+prefix+'r c[p '+content+'] k h232o[]]'
    text+='d r43k[] c['+both('k h236i['+prefix+'k h232o[]]',
        pair('h252t','r43d','r43e'),pair('h252u','r43h','r43e'),pair('h252v','r43f','r43g'),
        focus('h252w','r43g'),focus('h252x','r43f'),focus('h252x','r43g'),
        'k h252y[k h252s[] k wa[] k h252b[] r d[k r42a[]] k h247t[] r d[k r4l[]] r d[k r43j[]] k h232o[]]',
        'k ue[k h252b[] k h252s[] k h232o[]]','u[e[k h252b[]][k h252s[]]]')+'].\n'
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
    new=dict(kind='assert',body=dict(kind='call',symbol='r43k',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='clerical_practical_benefit_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/clerical-report-forecast-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
