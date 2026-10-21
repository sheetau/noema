"""Integrate the opening covenant question and its categorical answer."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_covenant_entitlement import NAMES

PARENT='examples/v016/kant-guardian-irrationality.noema'
PARENT_BASIS='data/guardian-irrationality-basis-v1.json'
DEPENDENCY='data/covenant-entitlement-basis-v1.json'
FULL='examples/v016/kant-covenant-question.noema'
CORE='examples/v016/covenant-question-core.noema'
BASIS='data/covenant-question-basis-v1.json'
ANNOTATIONS='data/covenant-question-identifiers-v1.json'
FAMILY='i[h[j[a]] e]'
PROPERTY='i[h[a] e]'
PRIMITIVES={
 'h255n':('[] d',[],'第六段落kant-1784:u0013の著者による論述の提示文脈。内容を評価する基準や合意形成の時点とは区別する。'),
 'h255o':('[] d',[],'第六段落で検討する教会関係者の団体・信条・政治的共同体・正当な資格の解釈を固定する基準。各仮想合意の形成基準h254zや提示文脈とは区別する。'),
 'h255p':('[a d] a',['community','reference'],'同じ政治的共同体と固定基準について、この議論で合意形成の正当な資格を評価する規範上の出所。理性と人類の啓蒙に関わる正当性の観点であり、団体自身の規則や現行の権力者の許可へ代用しない。対象の許可・禁止は別に指定する。'),
 'h255q':('[] a',[],'団体が成員を相互に拘束する制度的な合意を形成する当事者としての立場。聖職者個人の説教の職務や国家の立法者の立場へ置換しない。'),
 'h255r':('[] a',[],'第六段落のVolkが属する政治的共同体。国名を補わず、読者世界や教区会衆と同一視しない。全人民の範囲はh237cで与える。'),
 'h255s':('[] a',[],'kant-1784:u0013[0,409)のAberからverewigen?までの問い全体。'),
 'h255t':('[] a',[],'同じ原文[410,443)のIch sage: das ist ganz unmöglich.という回答全体。'),
 'h255u':('[] a',[],'同じ原文[410,419)のIch sage:という回答者自身の明示。'),
 'h255v':('[] a',[],'同じ原文[53,111)のetwa eine Kirchenversammlung, oder eine ehrwürdige Klassisという二例の提示。'),
 'h255w':('[] a',[],'同じ原文[112,160)の(wie sie sich unter den Holländern selbst nennt)という自己呼称の括弧内説明。'),
 'h255x':('[] a',[],'同じ原文[264,377)のum soからzu führenまでの、中断しない上位後見と成員を介した人民への後見を目的とする箇所。'),
 'h255y':('[] a',[],'同じ原文[379,408)のund diese so gar zu verewigenという同じ後見の永続化まで目的とする箇所。'),
 'h255z':('[] a',[],'同じ原文[428,432)のganzという回答の全面的な拒否の強調。'),
 'h256a':('[] a',[],'同じ原文[5,17)のsollte nichtという仮の肯定的見込みを提示する否定疑問の箇所。'),
 'h256b':('[] a',[],'同じ原文[420,443)のdas ist ganz unmöglich.という回答内容の箇所。'),
 'h256c':('[a a i[f] '+PROPERTY+' '+PROPERTY+' '+PROPERTY+' '+PROPERTY+' d] c',
     ['node','author','question','scope','first','second','alternatives','context'],
     '著者が同じ問いの一般対象範囲について、第一または第二の性質を持つ対象を非網羅的な例として提示する。alternativesは同じ対象への二性質の包含的選言の記述。二例の両方の実在・排他性・範囲の二例への限定を主張しない。例の性質と一般範囲は閉じた記述に結ぶ。'),
 'h256d':('[a a i[f] '+PROPERTY+' '+PROPERTY+' d] c',
     ['node','author','question','kind','description','context'],
     '著者が問いの中の指定種類の同じ対象に説明の性質を結び付ける補足を提示する。別の対象への説明や一般範囲全体への説明ではない。対象の現実の存在はこの帰属から導かない。括弧による配置は別に示す。'),
 'h256e':('[a '+FAMILY+' '+FAMILY+' j[a] d] c',
     ['view','left','right','bindings','reference'],
     '指定観点・固定基準と同じ個体列の下で、左内容は右内容以上に予期されるという弱い順序。両内容関数へ同じ順序の引数列を渡す比較であり、内容の真理・数値確率・話者の私的な心理測定ではない。反対向きの不成立との連言で厳しい比較を構成する。'),
 'h256f':('[a a i[f] '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
     ['node','author','question','formation','goal','baseline','focus','background','context'],
     '同じ問いの形成対象の目的の内側で、著者が基準側に加えて焦点側までを目的とする取り立てを提示する。形成・全目的・二目的・期待背景の関数には同じ正確な個体列を渡し、全目的の二側への分解と厳しい期待比較を閉じた構成で指定する。問いの外側で形成やいずれの目的の実現も肯定しない。'),
 'h256g':('[a a i[f] i[e] d] c',['node','author','question','positive','context'],
     '著者が否定疑問の形で、同じ肯定内容は成立し得るのではないかという暫定的な見込みを検討に上げる。後の拒否に先立つ仮の反対考慮であり、著者の確定した賛同・事実信念・肯定回答ではない。過去の時点の義務も意味しない。'),
 'h256h':('[a a i d[e] i[e] d] c',['node','author','negative','positive','context'],
     '著者が同じ肯定内容への否定回答を、留保や部分的な例外を付さず全面的に提示する。否定内容の範囲は指定の内容構成に従い、別種の物理的な不可能性や制度的無効性を強調語だけから加えない。'),
 'h256i':('[a a a i d[e] i[f] d] c',['node','author','prior_node','prior','question','context'],
     '著者が先行する指定の主張を受けて、それでもこの問いはどうかという対照的な反対考慮を提示する。主張と問いの関係であり、論理的矛盾・前言撤回・問いへの肯定的な答えを含意しない。'),
}
MEANINGS={
 'r47m':'第六段落の固定した評価規範・当事者の立場・政治的共同体・基準の下でのr47iの肯定内容。',
 'r47n':'r47mと正確に同じ参照を供給したr47jの否定内容。dasの対象を形成の物理的可否や目的の成否へ移さない。',
 'r47o':'同じ参照を供給したr47kの否定疑問発話。',
 'r47p':'同じ参照を供給したr47lの否定回答発話。問いと同じ命題・極性でも発話の働きは異なる。',
 'r47q':'第六段落の固定基準におけるr47eの一般的な教会関係者団体の性質。',
 'r47r':'同じ基準での教会会議r46fの性質。',
 'r47s':'同じ基準でのClassisの制度的分類と敬称付き自己呼称r46oを併せた性質。',
 'r47t':'同じ基準でのClassisの制度的分類r46kの性質。',
 'r47u':'同じ団体が同じ名称・用法共同体において自称するr46nの性質。',
 'r47v':'同じ対象が教会会議r47rまたは自己呼称を備えるClassis r47sである包含的選言。両方の場合も排除しない。',
 'r47w':'正確な五個体の形成引数から、合意固有の固定基準における中断しない媒介的な上位後見r466の目的内容を作る。信条を目的の別の対象へ取り替えない。',
 'r47x':'同じ五個体と形成基準から、同じ合意による終点なしの後見の永続化r47bの目的内容を作る。',
 'r47y':'同じ五個体について、r47w/xの反射的な弱い期待比較と、基準側以上には焦点側を予期しない厳しい比較を結ぶ背景内容。目的の実際の成立を要求しない。',
 'r47z':'同じ五個体の形成引数を、同じ合意基準におけるr47cの団体・合意・共同体・主題の正確な四個体の目的へ射影する。r47wとr47xの連言と同じ目的を保つ。',
 'r472':'第六段落冒頭の否定疑問、非網羅的な二例、Classisの自己呼称の括弧内説明、同じ合意の目的の強調、仮の肯定的見込みと前文に対するAberの接続を、同じ著者と提示文脈へ帰属する。内容の事実性を帰属から導かない。',
 'r473':'同じ問いへのr47nの全面的な否定を著者に帰属し、Ich sageの回答者の明示、ganzの留保のない拒否、問いと回答の本文順序を結ぶ。問いの否定をさらに反転しない。',
}
LIMITS=[
 '問い[0,409)と回答[410,443)を一組として読む。etwaの二例は非網羅的であり、一般の団体範囲を教会会議かClassisだけへ限定しない。oderは包含的選言。',
 'Classisは長老も含み得る教会職務代表の団体。敬称は名称形式の属性であり、著者が道徳的に敬っている事実ではない。括弧のsie/sichは同じClassisを受け、Holländernは名称の用法共同体を指定する。',
 '不変信条への相互的な宗教上の宣誓、その固定当事者・同じ行為・共同目的・媒介関係は既存の構成を引き継ぐ。etwaや帰属を用いてそれらの意味条件を取り除かない。',
 'unaufhörlichは将来履歴全体で中断しない後見、verewigenは同じ合意による終点なしの成立・維持。sogarは後者まで目的にする強い取り立てで、目的の外で達成を断言しない。完全な履歴を解釈入力とする責任と有限モデルの限界は引き継ぐ。',
 'berechtigtは正当な規範の下で合意を形成してよい資格。回答はその例が一つもないという全面的な拒否であり、誓約を物理的に行えないという主張にしない。後続のnull und nichtigは別の文として残す。',
 'sollte nichtは仮の肯定的見込みを持つ否定疑問。Aberは先行する後見役の未成熟要求への不合理評価を受けて対照的な問いを出す。著者の確定した賛同や前言撤回を追加しない。',
 '第六段落の固定基準・提示文脈を新しく指定し、第五段落の参照を流用しない。前文への接続は同じ著者の明示した談話関係に限る。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)

REF='k h255o[]'
CTX='k h255n[]'
PARAMS='k h255p[k h255r[] '+REF+'] k h255q[] k h255r[] '+REF
QUESTION='r[k r47o[]]'
POSITIVE='r[k r47m[]]'
NEGATIVE='r d[k r47n[]]'

def definitions():
    text=''
    for n,source,sort in (('r47m','r47i','e'),('r47n','r47j','e'),('r47o','r47k','f'),('r47p','r47l','f')):
        text+='d '+n+'[] '+sort+'[k '+source+'['+PARAMS+']].\n'
    for n,source in (('r47q','r47e'),('r47r','r46f'),('r47s','r46o'),('r47t','r46k')):
        text+='d '+n+'[body a] e[b point[k '+source+'[v body '+REF+']]].\n'
    text+='d r47u[body a] e[b point[k r46n[v body k h254u[] k h254v[] '+REF+']]].\n'
    text+='d r47v[body a] e[b point[x[t[k r47r[v body]][v point]][t[k r47s[v body]][v point]]]].\n'
    anchor='k h254z[v agreement]'
    baseline='t[k r466[v body v community v subject '+anchor+']][v point]'
    focus='t[k r47b[v body v agreement v community v subject '+anchor+']][v point]'
    goal='t[k r47c[l[a][v body v agreement v community v subject] '+anchor+']][v point]'
    bindings='l[a]['+' '.join('v '+n for n in NAMES)+']'
    def compare(left,right):return 'k h256e[k wa[] r[p '+left+'] r[p '+right+'] '+bindings+' '+REF+']'
    background=both(compare('r47w','r47w'),compare('r47x','r47x'),compare('r47w','r47x'),'u['+compare('r47x','r47w')+']')
    for n,body in (('r47w',baseline),('r47x',focus),('r47y',background),('r47z',goal)):
        text+='d '+n+'[bindings j[a]] e[b point['+bind(NAMES,body)+']].\n'
    author='k wa[]';q='k h255s[]';answer='k h255t[]'
    question=[
        'k hzcr['+q+' '+author+' '+QUESTION+' '+CTX+']',
        'k h256c[k h255v[] '+author+' '+QUESTION+' r[p r47q] r[p r47r] r[p r47s] r[p r47v] '+CTX+']',
        'k h256d[k h255w[] '+author+' '+QUESTION+' r[p r47t] r[p r47u] '+CTX+']',
        'k h234k[k h255w[] '+author+' k h255v[] '+CTX+']',
        'k h256f[k h255y[] '+author+' '+QUESTION+' r[p r47f] r[p r47z] r[p r47w] r[p r47x] r[p r47y] '+CTX+']',
        'k h256g[k h256a[] '+author+' '+QUESTION+' '+POSITIVE+' '+CTX+']',
        'k h256i['+q+' '+author+' k h254d[] r d[k r45y[]] '+QUESTION+' '+CTX+']',
        'k ue[k h254d[] '+q+' '+CTX+']','k ue[k h255x[] k h255y[] '+CTX+']',
    ]
    response=[
        'k h236i['+answer+' '+author+' '+NEGATIVE+' '+CTX+']',
        'k h236m[k h255u[] '+author+' '+q+' '+answer+' '+NEGATIVE+' '+CTX+']',
        'k hzcs['+author+' '+q+' '+answer+' '+CTX+']',
        'k h256h[k h255z[] '+author+' '+NEGATIVE+' '+POSITIVE+' '+CTX+']',
        'k ue['+q+' '+answer+' '+CTX+']','k ue[k h255u[] k h256b[] '+CTX+']',
    ]
    for name,clauses,nodes in (('r472',question,('h254d','h255s','h255v','h255w','h255x','h255y','h256a')),
                               ('r473',response,('h255s','h255t','h255u','h255z','h256b'))):
        clauses+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
        text+='d '+name+'[] c['+both(*clauses)+'].\n'
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
    new=[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('r472','r473')]
    doc['statements']=statements+new;core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=new)
    ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='covenant_question_and_categorical_answer',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/guardian-irrationality-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
