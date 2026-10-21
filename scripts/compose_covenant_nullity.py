"""Integrate the hypothetical covenant's categorical nullity and concession."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='examples/v016/kant-covenant-question.noema'
PARENT_BASIS='data/covenant-question-basis-v1.json'
DEPENDENCIES=('data/human-enlightenment-block-basis-v1.json','data/normative-nullity-basis-v1.json','data/peace-conclusion-basis-v1.json')
FULL='examples/v016/kant-covenant-nullity.noema'
CORE='examples/v016/covenant-nullity-core.noema'
BASIS='data/covenant-nullity-basis-v1.json'
ANNOTATIONS='data/covenant-nullity-identifiers-v1.json'
FAMILY='i[h[j[a]] e]'
NAMES=('body','agreement','creed','subject','community')
PRIMITIVES={
 'h257l':('[a d d] c',['agreement','reference','candidate'],'同じ合意と固定した評価基準について、その契約の同一性、当事者・条項・目的・仮定した形成を保って、公的な承認の有無を考える全候補の一つである。現実の承認例だけ、既に正当とされた場合だけ、結論に都合のよい例だけへ狭めない。候補の実在や実現可能性、承認の成立は含意せず、具体的な承認と正当な効力は別に評価する。'),
 'h257m':('[a a a i d[e] '+FAMILY+' '+FAMILY+' d] c',['node','author','prior_node','whole','prior_kind','current_kind','context'],
    '著者がこの箇所で先行箇所の形成の種類を受け、同じ当事者・合意などの引数を持つ現在の形成内容にその種類を保持しているという照応を提示する。現在の内容に追加された限定は保ち、二種類が完全に同義だとはせず、唯一の現実の契約への個体指示にも変えない。内容関数は全体と同じ束縛の下で読む。'),
 'h257n':('[a a i d[e] '+FAMILY+' '+FAMILY+' d] c',['node','author','whole','antecedent','consequent','context'],
    '著者が指定した全体の同じ引数束縛の下で、第一内容を仮定し、その場合の第二内容を述べる提示。第一内容の実在・可能性・成功は断言せず、第二内容を仮定した種類の外まで一般化しない。仮定と帰結の論理的内容はそれぞれ閉じた内容関数で別に指定する。'),
 'h257o':('[a a i d[e] '+FAMILY+' d] c',['node','author','whole','content','context'],
    '著者が同じ全体の同じ束縛と仮定の範囲で、指定内容を部分的な例外や留保を付けない全面的な判断として提示する。内容自体の量化・否定の範囲を保ち、別の物理的不可能性や現行権力の強制不在を強調だけから追加しない。'),
 'h257p':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',['node','author','whole','supposition','maintained','strengthened','context'],
    '著者が同じ全体の同じ束縛・仮定内で、第一内容が成立する場合まで反対考慮として認めても、第二内容を撤回しないという譲歩を追加する。第一内容を結論を覆し得るものとして挙げた上で、それでも第二内容を維持する。強化内容はこの仮定上の検討を含む構成であり、第一内容の実在・可能性や数値確率、実際の読者の信念を要求しない。'),
 'h257q':('[a a i d[e] j['+FAMILY+'] '+FAMILY+' d] c',['node','author','whole','members','aggregate','context'],
    '著者が同じ全体・束縛内で、指定された順序の内容の列を一つの反対考慮の列挙として提示する。集約は同じ引数での構成内容を指定し、列外の全種類の網羅や列内の排他性、順番に沿う数値的な権威の厳しい序列を主張しない。各内容の実在を列挙から導かない。'),
 'h257r':('[] a',[],'kant-1784:u0013[444,712)のEin solcher Kontraktからbestätigt sein.まで、同種契約の無効性と承認への譲歩を述べる一文全体。'),
 'h257s':('[] a',[],'同原文[444,466)のEin solcher Kontrakt,という先の種類を受ける仮定的な契約。'),
 'h257t':('[] a',[],'同原文[466,558)のderからgeschlossen würde,まで、人類の今後の啓蒙を永久に妨げるための仮定形成。'),
 'h257u':('[] a',[],'同原文[558,596)のist schlechterdings null und nichtig;という全面的な無効性の判断。'),
 'h257v':('[] a',[],'同原文[596,712)のund sollte er auchからbestätigt sein.まで、承認の場合を仮に認める譲歩の節。'),
 'h257w':('[] a',[],'同原文[615,641)のdurch die oberste Gewalt,という最高権力による確認の種類。'),
 'h257x':('[] a',[],'同原文[641,662)のdurch Reichstäge undという帝国身分会議による確認と列挙の継続。'),
 'h257y':('[] a',[],'同原文[662,697)のdie feierlichsten Friedensschlüsseという最も厳粛な和平締結。'),
}
MEANINGS={
 'r5bk':'同じ契約・政治的共同体・固定基準からh255pの正当性の規範を供給し、r475の全規範的帰結についてその契約が効力の根拠にならない内容を作る。確認者自身の規範へ評価者を替えない。',
 'r5bl':'同じ契約・共同体・固定基準に対するr5bjの、最高権力・帝国身分会議・最も厳粛な和平合意のいずれかによる確認内容。',
 'r5bm':'評価点の同じr5bkに加え、固定基準の全候補で、同じ契約へのr5blの確認があっても同じr5bkが成立する内容。確認・候補の存在は断言せず、基準を候補点や権力者の立場へ動かさない。',
 'r5bn':'正確な五個体の形成引数から、同じ契約・政治的共同体と第六段落の固定基準でr5bkの無効性を作る内容族。',
 'r5bo':'同じ五個体の形成引数からr5blの三種類の確認を作る内容族。erの対象は同じ合意位置の契約とし、承認者や和平文書へ取り替えない。',
 'r5bp':'同じ五個体の形成引数からr5bmの確認の仮定を含む無効性を作る内容族。',
 'r5bq':'同じ正確な五個体について、先の種類・信条・相互宣誓・後見目的と、人類の今後の啓蒙を永久に妨げる共同目的を持つr5akの形成を仮定し、その同じ契約についてr5bmを帰結とする。目的の成功や契約の実在を前提の外で肯定しない。',
 'r5br':'第六段落の同じ政治的共同体を固定し、全ての団体・合意・信条・主題についてr5bqの条件を述べる一文の内容。einを単一の実在契約の存在主張にせず、条件に当てはまらない全契約の無効性まで追加しない。',
 'r5bs':'同じ五個体の形成引数と同じ評価点で、同じ共同体の最高権力の保持者が同じ契約を承認するr5avの内容族。',
 'r5bt':'同じ五個体と評価点で、帝国身分会議が同じ契約を承認するr5awの内容族。',
 'r5bu':'同じ五個体と評価点で、第六段落の固定した方式比較基準の下で最も厳粛な和平合意が同じ契約を確認するr5biの内容族。',
 'r5bv':'一文全体r5brを同じ著者・第六段落の提示文脈へ帰属し、先の問いの形成種類へのsolcherの照応、würdeの仮定形成、schlechterdingsの全面性、sollte auchの仮定上の確認への譲歩と三種類の列挙を同じ束縛内に結ぶ。前回答からの本文順序と各箇所の同一性を保持する。',
}
LIMITS=[
 '原文[444,712)を一文として読む。Ein solcher Kontraktは先の形成の種類を保持した一般的な条件であり、特定の現実の契約の存在主張ではない。追加の目的はr5akで同じ契約へ結ぶ。',
 'auf immer alle weitere Aufklärung vom Menschengeschlechte abzuhaltenは、全人類の理由ある自己判断が新たな対象へ広がる進展を、同じ合意の制度的実施で終点なしに妨げる目的という先行の明示読解を保持する。目的の実現や物理的可能性は形成の外で要求しない。',
 'null und nichtigは正当な規範上の効力を持たないという一まとまりの強調。全ての規範的帰結に同じ規範・契約・固定基準を用い、要求と許可だけに狭めない。事実上の強制や別の独立した根拠から生じる救済まで否定しない。',
 'schlechterdingsは指定した種類の契約に関する判断の全面性を強調する。全世界・全時代の任意の契約や物理的不能に広げない。',
 'und sollte er auch ... bestätigt seinは、同じ契約への確認を結論を覆し得る反対考慮として仮に持ち出し、それでも無効という判断を維持する譲歩。確認や確認可能な候補の存在を断言せず、客観的な確率や義務の過去形として扱わない。',
 '最高権力・帝国身分会議・最も厳粛な和平締結の列挙は、各種類の確認を許す包含的な反対考慮として読む。複数種類の確認が重なる場合も含み、全歴史的議会・全条約の同時承認や種類間の厳しい序列を補わない。確認する主体と、確認を含む和平合意の条項を区別する。',
 '候補範囲・全規範的帰結・制度的資格・全当事者・将来履歴などは公開した意味規約を持つ解釈入力。有限検査がその現実的な完全性、原著者の主張の真理、言語の万能性を証明するわけではない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

REF='k h255o[]';CTX='k h255n[]'
WHOLE='r d[k r5br[]]'

def definitions():
    text='d r5bk[agreement a community a reference d] e[k r475[v agreement k h255p[v community v reference] v reference]].\n'
    text+='d r5bl[agreement a community a reference d] e[k r5bj[v agreement v community v reference]].\n'
    null=lambda point:'t[k r5bk[v agreement v community v reference]][v '+point+']'
    confirmed='t[k r5bl[v agreement v community v reference]][v candidate]'
    concession='f candidate d[y[k h257l[v agreement v reference v candidate]][y['+confirmed+']['+null('candidate')+']]]'
    text+='d r5bm[agreement a community a reference d] e[b point['+both(null('point'),concession)+']].\n'
    for name,body in (
        ('r5bn','t[k r5bk[v agreement v community '+REF+']][v point]'),
        ('r5bo','t[k r5bl[v agreement v community '+REF+']][v point]'),
        ('r5bp','t[k r5bm[v agreement v community '+REF+']][v point]'),
        ('r5bs','k r5av[v agreement v community v point]'),
        ('r5bt','k r5aw[v agreement v point]'),
        ('r5bu','k r5bi[v agreement '+REF+' v point]')):
        text+='d '+name+'[bindings j[a]] e[b point['+bind(NAMES,body)+']].\n'
    args=' '.join('v '+n for n in NAMES)
    conditional='y[k r5ak['+args+' k h254z[v agreement]]][t[k r5bm[v agreement v community '+REF+']][v point]]'
    text+='d r5bq[bindings j[a]] e[b point['+bind(NAMES,conditional)+']].\n'
    scoped='t[k r5bq[l[a][v body v agreement v creed v subject k h255r[]]]][v point]'
    for n in reversed(NAMES[:-1]):scoped='f '+n+' a['+scoped+']'
    text+='d r5br[] e[b point['+scoped+']].\n'
    author='k wa[]';node='k h257r[]'
    clauses=[
        'k h236i['+node+' '+author+' '+WHOLE+' '+CTX+']',
        'k h257m[k h257s[] '+author+' k h255s[] '+WHOLE+' r[p r47f] r[p r5al] '+CTX+']',
        'k h257n[k h257t[] '+author+' '+WHOLE+' r[p r5al] r[p r5bp] '+CTX+']',
        'k h257o[k h257u[] '+author+' '+WHOLE+' r[p r5bn] '+CTX+']',
        'k h257p[k h257v[] '+author+' '+WHOLE+' r[p r5bo] r[p r5bn] r[p r5bp] '+CTX+']',
        'k h257q[k h257v[] '+author+' '+WHOLE+' l['+FAMILY+'][r[p r5bs] r[p r5bt] r[p r5bu]] r[p r5bo] '+CTX+']',
    ]
    for left,right in (('h255t','h257r'),('h257s','h257t'),('h257t','h257u'),('h257u','h257v'),('h257w','h257x'),('h257x','h257y')):
        clauses.append('k ue[k '+left+'[] k '+right+'[] '+CTX+']')
    nodes=('h255s','h255t','h257r','h257s','h257t','h257u','h257v','h257w','h257x','h257y')
    clauses+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r5bv[] c['+both(*clauses)+'].\n'
    return text

def build():
    old=parent();libs=dependencies();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n) or imported.get(n)
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5bv',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(lib.source_sha256 for lib in libs))
    basis=dict(status='covenant_nullity_and_hypothetical_confirmation_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/covenant-question-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
