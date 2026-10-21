"""Compose an original human vocation and a hypothetical grave violation of it."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_cohort_covenant_purpose import NAMES,FIELDS,ARGS,SIX,REF

PARENT='data/cohort-covenant-denial-basis-v1.json'
LIBRARY='examples/v016/human-vocation-offense.noema'
BASIS='data/human-vocation-offense-basis-v1.json'
FAMILY='i[h[j[a]] e]'
CHANGE='i[h[a d d] e]'
PRIMITIVES={
 'h26bo':('[a i[h[a] c] d] c',['nature','kind','reference'],'この本性は、閉じた種別述語で指定した存在者を、その種の存在者として特徴づける基本的なあり方として捉えられている。個人の一時的気分や経験で獲得した習慣とは区別する。種別の実例の存在、全個体の同一の行動、生物学的機構、特定の使命内容は別である。'),
 'h26bp':('[a a d] c',['nature','vocation','reference'],'この課題は、指定した本性に固有の能力・あり方が展開すべき方向を表す使命として位置付けられている。外部から命じられた職務や本人の私的な希望に還元しない。使命の具体的な内容・本来的な由来・達成の事実は別に記述する。'),
 'h26bq':('[a a d] c',['nature','vocation','reference'],'この同じ本性と使命の関係は、後の社会的取り決めや習慣によって初めて作られたものではなく、その本性に元来属するものとして位置付く。歴史上最初の出来事の日付、出生時の完成、神による命令や達成の必然性を含意しない。'),
 'h26br':('[a '+CHANGE+' d] c',['vocation','development','reference'],'この使命を成す内容は、閉じた変化内容関数が対象集団と前後点へ同じ順序で適用する、その展開である。単に使命を果たす一つの手段や偶然併存する結果として結ばず、何に使命が存するかという内容上の同定を表す。同時点の真偽一致で別の記述へ置換せず、その展開の現実の達成は要求しない。'),
 'h26bs':('[a a d] c',['nature','source','reference'],'同じ評価基準の下で、この規範の出所は、指定された本性のあり方とその展開を尊重すべきものとして規範的評価の根拠に置く。単に同じ名で呼ばれること、現行法や当事者の合意の存在とは区別する。個別の要求・許可や本性の具体的内容は別に確認する。'),
 'h26bt':('[a a a a '+FAMILY+' j[a] d d] c',['source','protected','bearer','role','conduct','bindings','reference','point'],'同じ規範の出所と評価基準で、指定した担い手・立場の、閉じた行為内容関数と同じ対象列により記述された企てを、保護される同じ対象への重大な侵害として性格づける評価。単なる不利益や軽微な不適合に弱めない。評価対象の現実の実行、刑法上の罪名・裁判・制裁、故意や成功をこの評価だけから導かない。禁止要求の存在は別に結ぶ。'),
}
MEANINGS={
 'r5dw':'対象集団と前後点から、固定基準h26av・同じ候補経過での啓蒙全般の進展r5crを返す。直前のr5dnが六対象中の後続集団へ適用するのと同じ関係であり、認識量の増加だけや三進展の同時達成へ替えない。',
 'r5dx':'同じ本性が人aaという種別の本性であり、同じ使命がその本性の展開の方向であり元来その本性に属し、その使命の内容がr5dwの同じ啓蒙進展に存することを結ぶ。使命を述べる際に進展の現実の達成を評価しない。',
 'r5dy':'同じ本性・使命のr5dxを規範h26axの根拠h26bsへ結び、同じ六対象の先行集団・h26ayの立場に、r5dbの目的付き相互宣誓形成を禁ずるh7kと、同じ本性への重大な侵害としてのh26btを結ぶ。単なる許可欠如ではなく禁止と重大な評価を保持し、現実の形成や目的達成は要求しない。',
 'r5dz':'正確な六対象列から、その同じ企てがr5dyの人間本性への重大な規範違反に当たるという内容を返す。本性と使命は存在量化するが、別の行為や別の保護対象への評価を借りない。',
 'r5d2':'正確な六対象列について、同じr5dbの企てが形成されるなら同じr5dzの重大な規範違反に当たるという仮定的内容。現実に形成されたと断言せず、達成成功も条件にしない。',
 'r5d3':'同じr5dcの全候補についてr5d2の仮定的評価を述べる。Dasが受ける先行文の同じ六対象・共同目的付き相互宣誓を保持し、一つの実例や刑事事件の断言へ替えない。',
 'r5d4':'人間本性とその本来的使命がr5dxを満たすという相対節の補足内容。主たる仮定に該当する合意がない場合でも補足を消さず、引用される啓蒙進展の実行を要求しない。',
}
LIMITS=[
 'derenは同じ人間本性を受ける。人間本性を、経験でほとんど本性となった未成熟の性向や、特定国民・職業の性質へ置換しない。aaで指定される人としてのあり方を、本性と使命の別々の関係へ結ぶ。',
 'ursprüngliche Bestimmungは、人のあり方に元来属する展開の課題という目的論的・規範的な読みを採る。後から定められた職務、事実上の必然的な進歩、全員の出生時の完成、神学上の特定の計画を追加しない。原文はこの本性論の実証や一般理論を述べていない。',
 'in diesem Fortschreiten bestehtは、直前の啓蒙全般の進展r5crに使命が存するという内容の同定。認識獲得r5coや訂正r5ciは先行する例示として保持するが、それらの成功から理由ある自己判断の進展を自動的に導かない。geradeの焦点提示は全文接続で別に扱う。',
 'Verbrechen wider die menschliche Naturは、その本性を規範の根拠にして、同じ企てへの禁止と本性への重大な侵害という評価を結ぶ。前文の資格欠如だけで犯罪を演繹する規則は追加しない。刑法上の犯罪、裁判や処罰、既遂の結果を要求しない。',
 'Das wäreは前文の同じ目的付き相互宣誓形成を受ける仮定。新しい実例や成功を主張しない。候補経過ごとの条件文で表し、形成された候補だけを候補範囲として選ばない。文自体の提示は後に引用して著者へ帰属する。',
 '本文100主張と確認済み文字数は保つ。後代の拒否資格r5dvは別依存群に構成済み。次に両群を接続し、gerade・also・vollkommen、同じ決議の採択へのunbefugter/frevelhafterの二評価、著者帰属・全文通読を行う。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    text='d r5dw[group a first d last d] e[b candidate[k r5cr[v group '+REF+' v candidate v first v last]]].\n'
    text+='d r5dx[nature a vocation a] c['+both('k h26bo[v nature r[p aa] '+REF+']',
        'k h26bp[v nature v vocation '+REF+']','k h26bq[v nature v vocation '+REF+']',
        'k h26br[v vocation r[p r5dw] '+REF+']')+'].\n'
    norm='k h26ax[] v firstgroup k h26ay[] r[p r5db] '+SIX
    text+='d r5dy[nature a vocation a '+FIELDS+' candidate d] c['+both('k r5dx[v nature v vocation]',
        'k h26bs[v nature k h26ax[] '+REF+']','k h7k['+norm+' '+FALSE+' v candidate]',
        'k h26bt[k h26ax[] v nature v firstgroup k h26ay[] r[p r5db] '+SIX+' '+REF+' v candidate]')+'].\n'
    text+='d r5dz[bindings j[a]] e[b candidate['+bind(NAMES,
        'g nature a[g vocation a[k r5dy[v nature v vocation '+ARGS+' v candidate]]]')+']].\n'
    text+='d r5d2[bindings j[a]] e[b candidate['+bind(NAMES,
        'y[t[k r5db['+SIX+']][v candidate]][t[k r5dz['+SIX+']][v candidate]]')+']].\n'
    body='y[k r5dc['+ARGS+' v candidate]][t[k r5d2['+SIX+']][v candidate]]'
    for n in reversed(NAMES):body='f '+n+' a['+body+']'
    text+='d r5d3[] e[b candidate['+body+']].\n'
    text+='d r5d4[] e[b candidate[g nature a[g vocation a[k r5dx[v nature v vocation]]]]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r5cr','r5db','r5dc','h26ax','h26ay','h7k']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='human_original_vocation_and_hypothetical_grave_offense',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
