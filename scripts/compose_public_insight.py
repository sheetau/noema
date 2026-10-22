"""Bind grasped cognition, public grounds and corroboration of the same content."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE

PARENTS=('data/legislative-touchstone-basis-v1.json','data/institutional-outlook-basis-v1.json')
LIBRARY='examples/v016/public-insight.noema'
BASIS='data/public-insight-basis-v1.json'
FRAME='community a regime a field a audience a reference d assessment d candidate d'
FRAME_ARGS='v community v regime v field v audience v reference v assessment v candidate'
PRIMITIVES={
 'h26c5':('[a a d] c',['item','field','reference'],'固定した代表認識項目が、その同じ検討領域の事柄のあり方・構造・条件・相互関係を明らかにする対象範囲に属する。宗教制度については教え・実践・運営とその根拠や問題の関係を含み、単なる同音語や無関係な話題ではない。成功した認識や公表済み項目だけへ絞らず、内容はh26aeで別に明示する。'),
 'h26c6':('[a a a a d d d] c',['audience','person','judgment','item','reference','candidate','point'],'同じ本人が保持するこの同じ判断と代表項目の内容が、この候補のこの点で同じ公衆へ公的に提示され、検討に供されている。限定された私的な仲間だけへの伝達、項目名のみの掲示、別判断の発表とは区別する。全員の閲覧・理解・賛同や内容の正しさは含意しない。'),
 'h26c7':('[a a a d d d] c',['audience','reason','judgment','reference','candidate','point'],'この同じ理由が、この同じ判断を支える理由として、同じ公衆によって内容を検討可能な形で公に利用できる。理由の名前だけの公示や別判断の根拠の開示ではなく、関連する内容・条件・適用をたどれる。同じ判断は元の見解又はそれを検証する確認判断であり、使用・支持・真理・全員の受容は別に検査する。'),
 'h26da':('[a a d d d] c',['review','judgment','reference','candidate','point'],'この検討行為は、この同じ保持判断の内容を、根拠・反例・経験又は適用に照らして成り立つか確かめる検証である。単なる反復、人気投票、別内容の検証とは区別する。検証の生起、用いた根拠、支持、肯定的な結論、公開性は別に結ぶ。別人の権威による追認や特定の実験形式だけへ限定しない。'),
}
MEANINGS={
 'r5fq':'同じ政治的共同体の宗教上の制度h26csと同じ検討領域h26ctを固定し、項目が完全な認識範囲h26adに属し、その代表項目が同じ領域の事柄のあり方h26c5を扱う。公開・成功した認識だけを前件で選別しない。',
 'r5fr':'同じ人が保持する肯定判断と代表内容について、同じ使用理由が支持し現在の受容の十分な根拠として働き、その判断・内容と同じ理由が同じ公衆に開かれている。判断内容は引用したまま扱い、真理・把握はr5ftのr5clで別に検査する。',
 'r5fs':'同じ保持判断を対象とする検証行為が生起し、同じ代表項目を肯定する結論を持ち、そこで用いた同じ証拠が検証判断を支持し、その証拠が同じ公衆に検討可能である。検証対象・肯定内容・理由の取り違えを拒み、検証したという分類だけで確証としない。',
 'r5ft':'同じ人・項目・制度・検討領域・公衆・固定基準・真偽評価・候補点について、r5fqの対象範囲とr5clの把握された根拠ある認識を持ち、同じ保持判断へのr5frの公開とr5fsの公的な検証がある。理解せず掲示しただけ、真だが無根拠、私的な理解だけとは区別する。',
 'r5fu':'同じ項目・制度・検討領域・公衆について、r5ftを満たす人が少なくとも一人いる。公的な認識として検討可能になっていることを表し、全市民の内心の一致・同じ人による全項目の理解・聖職者だけへの限定を追加しない。',
 'r5fv':'同じ有効な全履歴の前後点で、同じ固定対象・真偽評価・公衆について、以前はr5fuがなく後にはある項目が一つ以上ある。既知の内容の新たな把握・根拠・公開された検証も含め、項目の別名だけでは増加にしない。共同提案に十分な程度に達したことは、この一つの進展からは導かない。',
}
LIMITS=[
 'u0013第七文のEinsicht in die Beschaffenheit dieser Sachenとöffentlich ... bewähretへの依存群。制度に関わる事柄の関係を把握し、根拠を持って保持する認識が、その判断と理由について公に検討でき、同じ内容への支持を伴う検証を受けるという明示読解を採る。',
 '既存r5clの受容・把握・十分な認識根拠・固定評価での真理を保持する。旧rknの意味内容集合の厳密な縮小を、そのまま洞察の発達と同一化しない。既知の結論の新しい説明を理解する場合には、その説明関係の内容を別に記述する既存規約を使える。',
 '認識と公開を同じ保持判断へ結び、さらにその判断を対象にする検証の肯定内容・使用根拠・支持・公開を結ぶ。元の理由と検証の証拠が別でも同じでもよいが、対応先は混ぜない。検証の科学的方法を一種類へ固定せず、検証者が必ず別人であるという条件も補わない。',
 '公的であることを、全市民が同時に理解・賛同していることへ強めない。r5fuは公衆に開かれた認識を持つ人の存在であり、一人の単なる私見や秘密の根拠だけでは満たさない。書面による批評の自由は既存の別条件に保持し、この認識の成立を刊行だけへ限定しない。',
 'r5fvは公に検討でき確証を持つ認識内容の新たな成立を測る部品である。既存の私的認識が初めて公になる場合も公的な進展に含み、同じ水準の担い手の交代や名前の変更だけは含めない。他の全認識の無損失や項目数の閾値を要求しない。',
 '認識対象・別名・内容・根拠・公開・検証の具体的解釈は入力の責任である。有限検査は現実の根拠の妥当性や全対象の網羅を証明しない。so weitの共同提案に足りる条件、声の結合、保護・非妨害、同じ期間の到達内容、可能性と著者帰属は残る。全文の確認文字数は増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def positive(judgment):return 'k h245q[v '+judgment+' k h26ag[v item v reference] r[p h26ae] v reference '+TRUE+' v point]'
def definitions():
    text='d r5fq[item a community a regime a field a reference d] c['+both('k h26cs[v regime v community v reference]',
        'k h26ct[v field v regime v reference]','k h26ad[v item v reference]','k h26c5[k h26ag[v item v reference] v field v reference]')+'].\n'
    text+='d r5fr[person a item a judgment a reason a audience a reference d candidate d point d] c['+both(
        'k h26ai[v person v judgment v reference v point]',positive('judgment'),
        'k fc[v judgment v reason v point]','k fd[v reason v judgment v point]','k h26aj[v reason v judgment v reference v point]',
        'k h26c6[v audience v person v judgment k h26ag[v item v reference] v reference v candidate v point]',
        'k h26c7[v audience v reason v judgment v reference v candidate v point]')+'].\n'
    text+='d r5fs[item a judgment a review a evidence a audience a reference d candidate d point d] c['+both(
        'k h26da[v review v judgment v reference v candidate v point]','k dg[v review v point]',positive('review'),
        'k fc[v review v evidence v point]','k fd[v evidence v review v point]',
        'k h26c7[v audience v evidence v review v reference v candidate v point]')+'].\n'
    joined=both('k r5fr[v person v item v judgment v reason v audience v reference v candidate v point]',
        'k r5fs[v item v judgment v review v evidence v audience v reference v candidate v point]')
    for n in reversed(('judgment','reason','review','evidence')):joined='g '+n+' a['+joined+']'
    text+='d r5ft[person a item a '+FRAME+' point d] c['+both('k r5fq[v item v community v regime v field v reference]',
        'k r5cl[v person v item v reference v assessment v point]',joined)+'].\n'
    text+='d r5fu[item a '+FRAME+' point d] c[g person a[k r5ft[v person v item '+FRAME_ARGS+' v point]]].\n'
    timeline='k ta[i[at d][k h257z[v reference v candidate v at]] i[before d after d][k ic[v before v after v candidate]]]'
    text+='d r5fv['+FRAME+' first d last d] c['+both(timeline,'k h257z[v reference v candidate v first]',
        'k h257z[v reference v candidate v last]','k ic[v first v last v candidate]',
        'g item a['+both('u[k r5fu[v item '+FRAME_ARGS+' v first]]','k r5fu[v item '+FRAME_ARGS+' v last]')+']')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5cl','h26ag','h26ae','h245q','fc','fd','dg','ta','h257z','ic'],['h26cs','h26ct'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='publicly_grasped_grounded_and_corroborated_insight',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
