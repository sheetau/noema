"""Integrate the final civic conditional, figurative premise and discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='examples/v016/kant-civic-spirit-sentence.noema';PARENT_BASIS='data/civic-spirit-sentence-basis-v1.json'
DEPENDENCIES=('data/government-causal-extension-basis-v1.json','data/germ-figurative-connection-basis-v1.json')
FULL='examples/v016/kant-collective-return-sentence.noema';CORE='examples/v016/collective-return-sentence-core.noema'
BASIS='data/collective-return-sentence-basis-v1.json';ANNOTATIONS='data/collective-return-sentence-identifiers-v1.json'
REF='k h26zj[]';CTX='k h27aw[]';AUTHOR='k wa[]'
FIELDS='community a lowerorder a higherorder a';ARGS='v community v lowerorder v higherorder'
SIX=FIELDS+' start d end d late d';SARGS=ARGS+' v start v end v late'
F6='i e[h[a a a d d d] e]';F4='i e[h[a a a a] e]';F2='i e[h[a a] e]';C5='i f[e]'
SHARED='同じ全体の条件量化内の同じ共同体・二制度・始点・中間終点・政治的終点へ適用する。別事例や現実の無条件の真理へ取り替えず、渡した内容の引用を実行しない。'
PRIMITIVES={
 'h27d2':('[a a a d d] c',['community','lowerorder','higherorder','reference','start'],'同じ固定した制度比較について、第四文の条件的な説明を適用する全事例の評価起点。前件の成立や後件の成功によって事後選別しない。基準は第三文と共用し、世界中の全時代への無条件の法則とはしない。範囲の非空と全事例の条件は合成側で確認する。'),
 'h27d3':('[a a '+C5+' '+F6+' '+F6+' '+F6+' d] c',['node','author','whole','matrix','supplement','combined','context'],'著者がこの箇所で、主たる説明に同じ事例の補足内容を括弧又は関係節として加え、両者を含む指定内容を提示する。補足を独立の無条件主張に移さない。'+SHARED),
 'h27d4':('[a a '+C5+' a '+C5+' d] c',['node','author','whole','antecedent','prior','context'],'著者が先行する同じ内容を受け、後続の条件的な経過をその説明の継続として提示する。論理的含意の証明、現実の因果関係や既成事実をこの談話関係だけから導かない。'),
 'h27d5':('[a a '+C5+' a '+F6+' a '+F6+' d] c',['node','author','whole','prior_node','prior','added_node','added','context'],'著者が先に述べた作用先に対し、後の作用先にも及ぶ内容を追加して提示する。二内容を択一にせず、一方の取り消しとしない。'+SHARED),
 'h27d6':('[a a '+C5+' '+F6+' '+F6+' d] c',['node','author','whole','background','focus','context'],'著者が先の内容を背景に、後の内容をそこまで及ぶとは予想しにくい追加として強調する。実際の全読者の心理、数値確率、論理的な不可能性は要求しない。'+SHARED),
 'h27d7':('[a a '+C5+' a '+F4+' d] c',['node','author','whole','antecedent','referent','context'],'この照応が、先行箇所の同じ共同体・二制度・本人に属する二性向の性質を指す。植物描写と対象側を結ぶ既存の同格・比喩対応を保ち、別人の性質や別の原因へ交換しない。'),
 'h27ea':('[a a '+C5+' a '+F2+' d] c',['node','author','whole','antecedent','referent','context'],'この照応が、先行する同じ共同体と本人の性質によって指定する民衆を指す。後件の能力成績で対象者を選び直さず、同じ人間成員範囲を保つ。'),
 'h27eb':('[a a '+C5+' '+F6+' d] c',['node','author','whole','focus','context'],'著者がこの自己言及の強調で、指定利益判断の受益対象も判断を持つ同じ政府自身であることを押し出す。他者の利益の不存在や政府の利益だけが唯一の理由であることは含意しない。'+SHARED),
 'h27ec':('[a a '+C5+' a a a d] c',['node','author','whole','marker','note','document','context'],'同じ論説のこの全文の終端に指定標識が置かれ、既存の同じ著者注への構造的参照として読む。注の論点を直前の一文だけへの説明・証明に限定せず、注内容をこの文の命題へ重複して加えない。注そのものと標識の表示は既存hzlzで別に確認する。'),
}
NODE_INFO={
 'h27ed':([716,1174],'第四文全体。'),
 'h27ef':([721,725],'dennの先行説明への継続。'),
 'h27eg':([871,931],'同じ二性向から民衆の心的傾向への反作用。'),
 'h27eh':([880,886],'dieserの同じ芽・二性向への照応。'),
 'h27ei':([931,1000],'wodurchで結ばれる能力増加の括弧。'),
 'h27ej':([940,946],'diesesの同じ民衆への照応。'),
 'h27ek':([1000,1057],'後の政府原則への作用。'),
 'h27el':([1012,1016],'auchの作用先の追加。'),
 'h27em':([1017,1022],'sogarの期待上の強調。'),
 'h27en':([1057,1094],'同じ政府自身への利益の判断。'),
 'h27eo':([1068,1074],'selbstの同じ政府自身への強調。'),
 'h27ep':([1094,1139],'人間の総称と今や機械以上であるという関係節。'),
 'h27er':([1139,1172],'同じ本人の尊厳に応じた扱い。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0017['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r6mb':'同じ比較組で固定した原因側の全成員について、同じ起点にr6jdの二性向の発達が完了しているという条件前件。原因側の完全性・非空と同じ民衆への所属はr6mfのr6kbで保持する。',
 'r6mc':'同じ比較組・起点・中間終点・政治的終点と固定基準について、同じ共同体の政府h27c6をr6l7へ渡した後件全体。枝ごとに政府・対象・時点を選び直さない。',
 'r6md':'同じ比較組と前件起点について、中間終点とそれより後の政治的終点が存在してr6mcを満たす。先の発達の開始点と後続反作用の始点を混同しない。',
 'r6me':'同じ比較組と第三文の固定基準における、第四文の全適用事例の起点範囲。前件の成立又は後件の成功を範囲条件へ追加しない。',
 'r6mf':'同じ比較組で原因側・民衆の範囲r6kbを固定し、非空の全事例r6meについて、r6mbならr6mdという条件を述べる。前件が成り立つ事例の存在、現実の後件の成立は別に断言しない。',
 'r6mg':'第三文と同じ非空の全比較組にr6mfの条件説明を適用する第四文全体の内容。対象範囲・固定基準を保ち、条件文を現実に全員が発達したという主張へ替えない。',
 'r6mh':'同じ六引数・基準によるr6keの心的反作用を取り出す内容族。',
 'r6mi':'同じ六引数・政府・基準によるr6l6の後の政府原則への作用を取り出す内容族。',
 'r6mj':'同じ六引数の後件全体r6mcを、談話上の位置付けへ渡す内容族。',
 'r6mk':'同じ人口・基準・始点・中間終点のr6krの能力増加を取り出す内容族。集団増加から各人の能力は導かない。',
 'r6ml':'同じ六引数でr6kzの心的反作用とそれを介した能力増加を取り出す。括弧の因果を単なる同時成立へ縮めない。',
 'r6mn':'同じ比較組と本人について、同じ共同体・基準のr6jaの二性向の組を返す。dieserは先行の芽とその性質の説明を受け、後件の原因側の同じ人へ適用される。',
 'r6mo':'同じ共同体・固定基準の人間成員の性質を返す。diesesが受ける民衆と能力増加・処遇の対象人口を保つ。',
 'r6mp':'同じ政治的終点で、同じ政府が同じ全人間成員への尊厳方針を政府自身に有益と判断するr6lyの内容族。',
 'r6mq':'同じ政治的終点で同じ全人間成員にr6ldを適用する内容族。nunはこの後件の段階へ結び、以前の理性・尊厳の不存在を主張しない。',
 'r6mr':'同じ政治的終点でr6mpの政府の利益判断とr6mqの人間の能力の追加内容を合わせる。利益判断の内部へ人間の能力を押し込めず、能力の成立を政府の誤認だけにしない。',
 'r6ms':'第四文全体r6mgを同じ著者へ帰属し、既存r6jwの前件の比喩・覆い照応・芽の同格を保つ。denn、能力の括弧、政府の関係節の補足、auch/sogar、dieser/dieses、selbst、著者注参照と本文順序を結び、引用された内容は実行しない。',
}
LIMITS=[
 'u0017第四文[716,1174)を、先行第三文の同じ制度比較に関する条件的な経過の説明として読む。同じ非空の全比較組ごとに、結果を見て選ばない非空の全事例を取り、前件が成り立てば後の二終点があるという条件にする。前件の実在を別に追加しない。',
 '芽は同じ民衆に属する固定された非空の原因側の人々の二性向を指す集合的な描写とする。原因側は民衆の全員とは限らない。全員に前件がそろうという連言を共通起点で評価し、各人の発達の開始時点は別でもよい。原文の唯一の集合解釈を証明したとはしない。',
 '前件はr6jdの低い市民的自由の下での二性向の発達、描写はr6joの自然・芽・硬い覆い・最も優しい世話である。r6jwの比喩提示を保ち、植物描写や自然の感情を現実の事実として条件に加えない。前件の完了は共通起点までの発達で、実際の思考行為や永続を要求しない。',
 '後件には同じ民衆の全心的特徴の漸次変化、その作用を介した行為能力得点の増加、同じ原因による後の政府原則の採用変化を用いる。因果モデルの非空の全介入解と内容照合を維持し、完全媒介、各人の不可欠性、偽側での全変化の消失を追加しない。',
 'endlichは民衆の変化を確認する中間点より後の政治的評価点とする。民衆の変化の完全終了や政府作用の初発は主張しない。auchは作用先の追加、sogarはそこまで及ぶことの期待上の強調で、因果・時刻条件とは別に提示する。',
 'wodurchは心的変化を介する能力増加で、同じr6kzのモデルを使う。diesesは同じ民衆を、dieserは同格で説明した同じ芽・二性向を指す。追加内容は同じ条件の中に保ち、現実の無条件の事実に移さない。',
 '政府の自己利益判断は非事実的であり、尊厳方針の実際の利益・採用・履行を導かない。人間の機械以上という能力内容は同じ政治的終点の追加主張で、政府の信念内だけに置かない。尊厳の全対象を能力のある者だけに絞らない。',
 '有益さの有限の加法的な見込み比較、尊厳の肯定的で非代替な価値、思考への好意と内的促し、漸次変化の尺度と比較範囲は各依存群の明示解釈を継承する。原文へ具体的な数値や目標を補わず、一般的な倫理・心理・社会因果理論の証明とはしない。',
 'dennは先行する低い側の発展機会についての説明を続ける談話として読む。先行文からの論理的演繹の証明にはしない。末尾標識は既存の著者注u0020へ構造的に結び、注をこの一文だけの説明に限定したり、内容を本文へ重複加算したりしない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def node(n):return 'k '+n+'[]'
def code(n):return 'r f[k '+n+'[]]'
def profile(n):return 'r e[p '+n+']'

ORDER=(('h26zq','h27ed'),('h27av','h27eg'),('h27at','h27eh'),('h27eg','h27ei'),('h27eg','h27ek'),('h27ek','h27en'),('h27en','h27ep'),('h27ep','h27er'),('h27er','hzlv'))
def definitions():
    government='k h27c6[v community '+REF+']';context=ARGS+' '+REF+' v start v end'
    text='d r6mb['+FIELDS+' start d] c[f person a[y[k h27cl['+ARGS+' '+REF+' v person]][t[k r6jd['+ARGS+' v person]][v start]]]].\n'
    text+='d r6mc['+SIX+'] c[k r6l7['+context+' '+government+' v late]].\n'
    text+='d r6md['+FIELDS+' start d] c[g end d[g late d[k r6mc['+SARGS+']]]].\n'
    text+='d r6me['+FIELDS+' start d] c[k h27d2['+ARGS+' '+REF+' v start]].\n'
    text+='d r6mf['+FIELDS+'] e[b outer['+both('k r6kb['+ARGS+' '+REF+']','g start d[k r6me['+ARGS+' v start]]',
      'f start d[y[k r6me['+ARGS+' v start]][y[k r6mb['+ARGS+' v start]][k r6md['+ARGS+' v start]]]]')+']].\n'
    selected='k r6ii['+ARGS+']'
    text+='d r6mg[] e[b outer['+both('g community a[g lowerorder a[g higherorder a['+selected+']]]',
      'f community a[f lowerorder a[f higherorder a[y['+selected+'][t[k r6mf['+ARGS+']][v outer]]]]]')+']].\n'
    targets={'r6mh':'k r6ke['+context+']','r6mi':'k r6l6['+context+' '+government+' v late]',
      'r6mj':'k r6mc['+SARGS+']','r6mk':'k r6kr[v community '+REF+' v start v end]','r6ml':'k r6kz['+context+']',
      'r6mp':'k r6ly['+government+' v community '+REF+' v late]','r6mq':'k r6ld[v community '+REF+' v late]'}
    for n,b in targets.items():text+='d '+n+'['+SIX+'] e[b outer['+b+']].\n'
    text+='d r6mr['+SIX+'] e[b outer['+both('t[k r6mp['+SARGS+']][v outer]','t[k r6mq['+SARGS+']][v outer]')+']].\n'
    text+='d r6mn['+FIELDS+' person a] e[c[k r6ja[v community '+REF+']][v person]].\n'
    text+='d r6mo[community a person a] e[b point[k r6hd[v person v community '+REF+']]].\n'
    whole=code('r6mg');parts=['k r6jw[]','k hzlz[]','k h26ub['+node('h27ed')+' '+AUTHOR+' '+whole+' '+CTX+']',
      'k h27d4['+node('h27ef')+' '+AUTHOR+' '+whole+' '+node('h26zq')+' '+code('r6ih')+' '+CTX+']',
      'k h27d3['+node('h27ei')+' '+AUTHOR+' '+whole+' '+profile('r6mh')+' '+profile('r6mk')+' '+profile('r6ml')+' '+CTX+']',
      'k h27d3['+node('h27ep')+' '+AUTHOR+' '+whole+' '+profile('r6mp')+' '+profile('r6mq')+' '+profile('r6mr')+' '+CTX+']',
      'k h27d5['+node('h27el')+' '+AUTHOR+' '+whole+' '+node('h27eg')+' '+profile('r6ml')+' '+node('h27ek')+' '+profile('r6mi')+' '+CTX+']',
      'k h27d6['+node('h27em')+' '+AUTHOR+' '+whole+' '+profile('r6ml')+' '+profile('r6mi')+' '+CTX+']',
      'k h27d7['+node('h27eh')+' '+AUTHOR+' '+whole+' '+node('h27at')+' '+profile('r6mn')+' '+CTX+']',
      'k h27ea['+node('h27ej')+' '+AUTHOR+' '+whole+' '+node('h27eg')+' '+profile('r6mo')+' '+CTX+']',
      'k h27eb['+node('h27eo')+' '+AUTHOR+' '+whole+' '+profile('r6mp')+' '+CTX+']',
      'k h27ec['+node('h27ed')+' '+AUTHOR+' '+whole+' '+node('hzlv')+' '+node('hzlu')+' '+node('hzik')+' '+CTX+']']
    for a,b in ORDER:parts += ['u[e['+node(a)+']['+node(b)+']]','k ue['+node(a)+' '+node(b)+' '+CTX+']','u[k ue['+node(b)+' '+node(a)+' '+CTX+']]']
    return text+'d r6ms[] c['+both(*parts)+'].\n'

def build():
    old=parent();libs=dependencies();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={};all_entries=dict(old.entries)
    for lib,roots in zip(libs,(('r6l7','r6kb','r6ke','r6kr','r6kz','r6l6','r6ld','r6ly'),('r6jw','r6ja','r6jd'))):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in all_entries:assert d==all_entries[n]['declaration'] and e['meaning_ja']==all_entries[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e;all_entries[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(all_entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):];by={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6ms',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in libs))
    basis=dict(status='collective_return_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
      new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/civic-spirit-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
