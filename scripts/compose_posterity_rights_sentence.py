"""Integrate human vocation, wrongful adoption and posterity's repudiation rights."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_cohort_covenant_purpose import NAMES,FIELDS,ARGS,SIX,REF

PARENT='examples/v016/kant-cohort-covenant-denial.noema'
PARENT_BASIS='data/cohort-covenant-denial-basis-v1.json'
DEPENDENCIES=('data/human-vocation-offense-basis-v1.json','data/posterity-repudiation-basis-v1.json')
FULL='examples/v016/kant-posterity-rights.noema'
CORE='examples/v016/posterity-rights-core.noema'
BASIS='data/posterity-rights-basis-v1.json'
ANNOTATIONS='data/posterity-rights-identifiers-v1.json'
FAMILY='i[h[j[a]] e]'
TRIPLE='l[a][v firstgroup v agreement v resolution]'
PRIMITIVES={
 'h26bu':('[a a a a d d d] c',['activity','group','agreement','resolution','reference','candidate','point'],'この行為は、同じ候補経過の同じ評価点に、同じ集団による同じ合意の同じ決定事項の採択として帰属され、その決定事項を集団の拘束方針として定める内容を持つ。行為の生起はdgで別に結ぶ。全成員による投票、満場一致、代表者名、正当な資格・効力・履行は要求しない。'),
 'h26bv':('[a a a a '+FAMILY+' j[a] d d] c',['source','protected','bearer','role','conduct','bindings','reference','point'],'同じ規範・保護対象・担い手・立場について、記述された同じ企てを、尊重すべき対象を意図的で不遜な仕方で顧みないものとして評価する。単なる手続上の資格不足、偶然の損害、無知による誤りだけとは区別する。評価として述べるもので、全当事者の内心や悪事との自覚、快楽目的、刑法上の故意を独立の事実として証明したとはしない。'),
 'h26bw':('[a a i d[e] i[h[a d d] e] d] c',['node','author','whole','development','context'],'著者が同じ全体内容において、指定した閉じた変化内容こそが使命を成すものだとして、その内容の同定を焦点化する提示。単に重要という程度や唯一の実際の成功に替えず、同定関係は全体内で別に構成する。焦点の真理をこの提示だけで実行しない。'),
 'h26b6':('[a a a d] c',['node','author','main_node','context'],'同じ著者がこの箇所を、同じ主たる叙述の対象を説明・性格づける挿入的補足として提示する。丸括弧の印字に限定せず、制限条件による対象範囲の縮小、別対象への独立した話題転換とは区別する。補足内容の真理と根拠の役割は別に結ぶ。'),
 'h26bx':('[] a',[],'kant-1784:u0013[1005,1264)のDas wäreからzu verwerfen.までの第五文全体。'),
 'h26by':('[] a',[],'同じ第五文のDas wäre ein Verbrechen wider die menschliche Naturという前半の仮定的評価。'),
 'h26bz':('[] a',[],'同じ第五文のderen ursprüngliche Bestimmung gerade in diesem Fortschreiten bestehtという人間本性の使命の相対節。'),
 'h26b2':('[] a',[],'同じ第五文のund die Nachkommenからzu verwerfen.まで、後代の拒否資格を述べる後半。'),
 'h26b3':('[] a',[],'同じ第五文のals unbefugter und frevelhafter Weise genommenという同じ決議の採択への評価。'),
 'h26b4':('[] a',[],'同じ第五文のgerade in diesem Fortschreitenという使命内容の同定を焦点化する箇所。'),
 'h26b5':('[] a',[],'同じ第五文のvollkommen dazu berechtigtという同じ拒否資格の全面性を述べる箇所。'),
}
MEANINGS={
 'r5d5':'先行集団・合意・決議の正確な三対象列から、同じ合意の固定形成点h254zで同じ決議h26bkを採択する行為の存在を返す。行為の生起dgと同じ集団への採択帰属h26buを結び、正当性や履行は要求しない。',
 'r5d6':'同じ先行集団・合意・決議の採択内容r5d5について、h26ax/h26ayからrduの積極的許可と反対要求の不在を結ぶ正当な資格。採択の実行や成功を評価しない。',
 'r5d7':'同じ決議の採択について資格r5d6がなく、同じ規範から禁止h7kがあり、同じ人間本性への重大な侵害h26btと意図的で不遜な軽視h26bvとして評価される。資格欠如と侵害の評価を一つのフラグへ縮めない。',
 'r5ea':'同じ六対象と候補で、一つの同じ人間本性・使命r5dxを規範h26axの根拠へ結び、非空の全採択決議h26bkについて採択の実行r5d5と二評価r5d7を要求する。評価が成功した決議だけへ範囲を選別しない。',
 'r5eb':'正確な六対象列から、同じ決議が採択されておりその採択に二評価があるr5eaの内容を返す。',
 'r5ec':'正確な六対象列について、同じ企てr5dbが形成された場合に、同じ後代の全員・全決議への拒否資格r5dvがあるという条件内容。拒否の実行、全手段への許可、実際の形成は外側に要求しない。',
 'r5ed':'同じr5dcの全候補へのr5ecの拒否資格の条件文。直後より先の後代も含み、現実に拒否した人だけへ範囲を狭めない。',
 'r5ee':'正確な六対象列について、同じ企てr5dbが形成された場合に、同じ全決議についてr5ebの採択と二評価があるという補足の条件内容。',
 'r5ef':'同じr5dcの全候補へのr5eeの採択評価の補足。これを資格の対象範囲の選別条件にせず、同じ仮定の下の全決議について述べる。',
 'r5eg':'同じ候補範囲における人間本性への仮定的違反r5d3、後代の拒否資格r5ed、同じ決議の採択への二評価r5efを合わせた第五文の中心内容。使命の相対節r5d4は補足として別に帰属する。',
 'r5eh':'第五文全体・前半・相対節・後半・採択評価を同じ著者と第六段落文脈へ帰属する。前文へのDasの照応、同じ形成の仮定、geradeの同定焦点、vollkommenの全面性、alsoとalsの理由提示、補足と本文順序を結ぶ。引用内容の真理・形成・拒否を実行しない。',
}
LIMITS=[
 'Dasは直前の同じ目的付き相互宣誓形成を受け、wäreはそれがなされた場合の評価として読む。後代の拒否資格と決議の採択評価も同じ仮定の下へ結び、実在する特定の契約を補わない。',
 '人間本性の本来的使命が同じ啓蒙進展に存するという相対節を、対象を絞る条件でなく補足として保持する。geradeはまさにその内容という同定の焦点。進展の事実、全員の同時成功、神学上の計画は追加しない。',
 'Nachkommenは先行時代後の人々であり、さらに後の時代と先行時代からの生存者を含む。jene Beschlüsseは同じ合意の非空の全採択決議。固定した個数・血縁・相続資格へ限定しない。',
 'unbefugterは同じ決議を採択する正当な資格の欠如、frevelhafterは同じ人間本性を尊重せず侵害する意図的で不遜なあり方という評価として読む。h7kの禁止・h26btの重大な侵害とh26bvの軽視を保持し、単なる手続違反へ弱めない。刑法上の故意・裁判・制裁や全員の内心を追加しない。',
 'genommenは同じ集団による採択の生起を、先行合意の固定形成点へ結ぶ。採択の実在は形成の仮定内でのみ述べる。正当性・効力・履行と区別し、同じ決議の拒否資格の内容へ接続する。',
 'verwerfenは同じ決議を拘束の根拠として受け入れない実践的な応答。資格は拒否という選択への衝突のない積極的許可であり、あらゆる手段の許可や実際の拒否ではない。vollkommenはこの同じ範囲で留保しない全面的な資格の提示。',
 'alsoは前半の違反評価と使命の補足から後代の資格を帰結として提示する関係。alsの採択評価も同じ拒否資格の理由に位置付ける。著者の論述を記述し、論理的導出の妥当性や規範の客観的真理を証明するものではない。',
 '原刊488頁と固定原文、AA VIII39を照合する。AdelungのFrevelhaftとFrevelの歴史的語義は軽視・侵害という読みの補助であり、全語義の連言や作者の唯一の意図の証明にはしない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def quant(body):
    for n in reversed(NAMES):body='f '+n+' a['+body+']'
    return body
CTX='k h255n[]'
WHOLE='r d[k r5eg[]]'
NODES=('h26bd','h26bx','h26by','h26bz','h26b2','h26b3','h26b4','h26b5')
def definitions():
    decisions='k h26bk[v agreement v resolution k h254z[v agreement]]'
    adoption=both(decisions,'g activity a['+both('k dg[v activity k h254z[v agreement]]',
        'k h26bu[v activity v firstgroup v agreement v resolution '+REF+' v candidate k h254z[v agreement]]')+']')
    text='d r5d5[bindings j[a]] e[b candidate['+bind(('firstgroup','agreement','resolution'),adoption)+']].\n'
    norm='k h26ax[] v firstgroup k h26ay[] r[p r5d5] '+TRIPLE
    fields='firstgroup a agreement a resolution a candidate d';args='v firstgroup v agreement v resolution v candidate'
    text+='d r5d6['+fields+'] c[k rdu['+norm+' '+TRUE+' v candidate i[items j[a]][e[v items]['+TRIPLE+']] p h7k p h7l]].\n'
    appraisal='k h26ax[] v nature v firstgroup k h26ay[] r[p r5d5] '+TRIPLE+' '+REF+' v candidate'
    text+='d r5d7[nature a '+fields+'] c['+both('u[k r5d6['+args+']]','k h7k['+norm+' '+FALSE+' v candidate]',
        'k h26bt['+appraisal+']','k h26bv['+appraisal+']')+'].\n'
    each=both('t[k r5d5['+TRIPLE+']][v candidate]','k r5d7[v nature '+args+']')
    text+='d r5ea['+FIELDS+' candidate d] c[g nature a[g vocation a['+both('k r5dx[v nature v vocation]',
        'k h26bs[v nature k h26ax[] '+REF+']','g resolution a['+decisions+']','f resolution a[y['+decisions+']['+each+']]')+']]].\n'
    text+='d r5eb[bindings j[a]] e[b candidate['+bind(NAMES,'k r5ea['+ARGS+' v candidate]')+']].\n'
    for root,target,universal in (('r5ec','r5dv','r5ed'),('r5ee','r5eb','r5ef')):
        text+='d '+root+'[bindings j[a]] e[b candidate['+bind(NAMES,'y[t[k r5db['+SIX+']][v candidate]][t[k '+target+'['+SIX+']][v candidate]]')+']].\n'
        text+='d '+universal+'[] e[b candidate['+quant('y[k r5dc['+ARGS+' v candidate]][t[k '+root+'['+SIX+']][v candidate]]')+']].\n'
    text+='d r5eg[] e[b candidate['+both(*( 't[k '+n+'[]][v candidate]' for n in ('r5d3','r5ed','r5ef')))+']].\n'
    author='k wa[]';q=lambda n:'r d[k '+n+'[]]'
    clauses=['k h236i[k '+node+'[] '+author+' '+q(content)+' '+CTX+']' for node,content in (
        ('h26bx','r5eg'),('h26by','r5d3'),('h26bz','r5d4'),('h26b2','r5ed'),('h26b3','r5ef'))]
    clauses+=['k h257m[k h26by[] '+author+' k h26bd[] '+WHOLE+' r[p r5db] r[p r5db] '+CTX+']']
    for node,target in (('h26by','r5dz'),('h26b2','r5dv'),('h26b3','r5eb')):
        clauses.append('k h257n[k '+node+'[] '+author+' '+WHOLE+' r[p r5db] r[p '+target+'] '+CTX+']')
    clauses+=['k h26bw[k h26b4[] '+author+' '+q('r5d4')+' r[p r5dw] '+CTX+']',
        'k h257o[k h26b5[] '+author+' '+WHOLE+' r[p r5dv] '+CTX+']',
        'k h26b6[k h26bz[] '+author+' k h26by[] '+CTX+']','k h26b6[k h26b3[] '+author+' k h26b2[] '+CTX+']',
        'k ud['+author+' i[node a][x[e[v node][k h26by[]]][e[v node][k h26bz[]]]] k h26b2[] '+CTX+']',
        'k ud['+author+' i[node a][e[v node][k h26b3[]]] k h26b2[] '+CTX+']']
    clauses+=['k ue[k '+l+'[] k '+r+'[] '+CTX+']' for l,r in (('h26bd','h26bx'),('h26by','h26bz'),('h26bz','h26b2'),('h26b5','h26b3'))]
    clauses+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(NODES) for b in NODES[i+1:]]
    text+='d r5eh[] c['+both(*clauses)+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5eh',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='posterity_rights_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/cohort-covenant-denial-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
