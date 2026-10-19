"""Put permission absence, rather than nonperformance, under causal prevention."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT='examples/v016/kant-prior-confinement.noema'
PARENT_BASIS='data/prior-confinement-basis-v1.json'
FULL='examples/v016/kant-modal-prevention.noema'
CORE='examples/v016/modal-prevention-core.noema'
BASIS='data/modal-prevention-basis-v1.json'
ANNOTATIONS='data/modal-prevention-identifiers-v1.json'
MEANINGS={
 'r2ah':'同じ本人について、後見人群dbを出所、hztdを立場とする、自ら判断する目標bbへ勇気を伴って取り組むことの積極的許容がない。既存hztcをこの用例の出所と目標に固定した結果状態。実際に取り組まなかったこと、明示的禁止、能力の欠如、実行不能を含意しない。',
 'r2ai':'一個体だけの引数列の本人についてr2ahを返す閉じた目標関数。注意と目的に渡す内容を、非試行ではなく同じ本人への許容欠如に固定する。過不足の引数を切り捨てない。',
 'r2aj':'同じ行為者群・行為・本人について、許容欠如r2aiの目標に関係する事項へ、同じ行為に参加しその目標を目指す成員の注意が向く。既存rqvpの分担を保ち、非試行など別の目標への注意は借りない。',
 'r2ak':'同じ本人へのr2ahが実際に成立し、同じ行為者群が参加する原因行為がその許容欠如を生じさせ、その同じ行為がr2ajを満たす。行為者群は引数、許容の出所はこの用例のdbであり、本文では両方をdbに固定する。試みの不成立を結果として要求しない。',
 'r2al':'後の提示時点で選んだ対象者全員について、先行する理解不足の原因行為と、先行局面における許容欠如への慎重な原因行為r2akを結ぶ。先行二局面は後の提示より前だが相互の厳密な順序は指定しない。',
 'r2am':'同じ危険提示と、許容欠如の原因を対象とする先行段階r2alを結ぶ。危険内容の真理や、対象者が現実に試みなかったことは追加しない。',
 'r2an':'後の基準時点より前の同じ局面で、後見人群dbが同じ本人の許容欠如を慎重な原因行為によって生じさせる。閉じ込め・落ち着き・一歩の不許容へ対応させる対象側の局面記述。',
 'r2ao':'更新した複文r2am(db)を著者へ帰属させ、先行する監督の文との談話順序を保持する。',
 'r2ap':'更新した同じ複文の本人・先行局面・基準時点について、r2anを既存の身体側の一歩の不許容rqzxとして描く。',
 'r2aq':'更新した同じ複文の同じ局面について、r2anを既存の落ち着いた家畜像rqz7として描く。',
 'r2ar':'更新した同じ複文について、r2anからrqzxへの対応と、後見人側の緩めない姿勢による強調を結ぶ。世界の実行状況や禁止の追加とは分ける。',
 'r2as':'更新した同じ複文の同じ局面について、r2anを既存の先行局面での閉じ込めr2afとして描く。警告までの継続は追加しない。',
}
MAPPING={'hztm':'r2ai','hztn':'r2aj','hzto':'r2ak','hztp':'r2al','hztq':'r2al',
    'hztr':'r2am','rqzw':'r2an','hzts':'r2ao','rqzy':'r2ap','r2aa':'r2aq','r2ac':'r2ar','r2ag':'r2as','hzsm':'r2ah'}
LIMITS=[
 '採用済みの許容の読みを維持し、verhütetenが対象とする結果を「許されないこと」へ結び直す。否定された許容の内容から、実際の非試行を余分に断言しない。実行機会の読みなど全ての解釈を同時に採るものではない。',
 '結果の許容欠如、原因行為、同じ結果を目指す注意を分けて要求する。規範がたまたま存在しないだけでは原因を認定しない。許されずに試みた場合にも、許容を防いだという内容は成立し得る。',
 'r2ahはこの用例のdb・hztd・bbを固定する公開定義。r2akの行為者引数を変えれば、別の行為者がdbを出所とする許容欠如を生じさせた意味になる。任意の行為者自身の許容を自動的に指す一般略記ではない。',
 '本文の35・36・47・48・49文（ゼロ始まり）を改訂する。身体側の内容、既存の宣言と意味規約、他の45文と十一単位の判断は保持する。複文・段落・二作品全文の意味確認は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not set(MEANINGS)&set(old.entries)
    doc=parse(format_graph(doc,'compact')+'''
d r2ah[person a] e[b scene[t[k hztc[k db[] v person k hztd[] r[p bb]]][v scene]]].
d r2ai[bindings j[a]] e[b scene[w[k hztb[v bindings]][g person a[w[a[v bindings][n p a b][v person]][t[k r2ah[v person]][v scene]]]]]].
''')
    by_name={d['name']:d for d in old.document['declarations']}
    for name in ('hztn','hzto','hztp','hztr'):
        row=replace_symbols(deepcopy(by_name[name]),MAPPING);row['name']=MAPPING[name];doc['declarations'].append(row)
    doc=parse(format_graph(doc,'compact')+'''
d r2an[person a prior d anchor d] c[w[k dd[v prior v anchor]][t[k r2ak[k db[] v person]][v prior]]].
''')
    for name in ('hzts','rqzy','r2aa','r2ac','r2ag'):
        row=replace_symbols(deepcopy(by_name[name]),MAPPING);row['name']=MAPPING[name];doc['declarations'].append(row)
    doc['statements']=deepcopy(statements)
    for i in (35,36,47,48,49):doc['statements'][i]=replace_symbols(doc['statements'][i],MAPPING)
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (9,35,36,46,47,48,49)]
    core['declarations']=closure(doc,_references(core['statements']))
    added=doc['declarations'][size:];assert len(added)==12
    basis=dict(status='modal_permission_absence_is_the_careful_causal_result',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/prior-confinement-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print('Twelve definitions; no new primitives; five scope-dependent statements revised',flush=True)


if __name__=='__main__':main()
