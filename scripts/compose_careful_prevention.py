"""Bind distributed goal-directed attention to the same causal event."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_unpermitted_undertaking import ROOT,closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT='examples/v016/kant-unpermitted-undertaking.noema'
PARENT_BASIS='data/unpermitted-undertaking-basis-v1.json'
FULL='examples/v016/kant-careful-prevention.noema'
CORE='examples/v016/careful-prevention-core.noema'
LIBRARY='examples/v016/careful-action.noema'
BASIS='data/careful-prevention-basis-v1.json'
ANNOTATIONS='data/careful-prevention-identifiers-v1.json'
PRIMITIVES={
 'hztj':(['actor','act','goal_description','bindings','aspect','context'],'同じ行為者が、その行為を進める中で、指定した目標記述と順序付き引数について、その事項へ継続して認知的な注意を配る。単に知覚したこと、結果の成功、感情的な好意とは区別する。事項の関連性、目的としての採用、実際の行為参加は別条件。'),
 'hztk':(['group','act','goal_description','bindings','aspect','context'],'同じ行為者群・行為・目標記述・順序付き引数・文脈について、遂行上考慮すべき事項の範囲に属する。現に注意を払った事項だけを範囲にしない。文脈上の関連範囲を解釈として固定し、注意や成功から逆算しない。'),
 'hztl':(['actor','act','goal_description','bindings','context'],'同じ行為者が、その行為の計画・遂行で、閉じた内容関数に同じ順序の引数を渡した目標を目指す。既存のparameterized-goalsのAIMS規約を具体化する。目標を実行評価せず、達成・実現可能性・道徳的な是認を含意しない。'),
}
MEANINGS={
 'rqvp':'同じ実際の行為について、非空の関連事項の全てへ、行為者群のうちその行為に参加し同じ目標を目指す者の注意が向いている。事項ごとに担当者が異なってよい。別行為・別目標・別引数への注意を流用せず、目標の達成は要求しない。',
 'hztm':'一個体だけの引数列から同じ本人を取り、試みの不成立hzsmを返す目標関数。過不足の引数を切り捨てない。',
 'hztn':'同じ後見人群の成員、同じ行為、同じ本人の非試行という目標とその関連事項をrqvpへ渡す。注意と目的を担う者は同じ行為に参加している。',
 'hzto':'既存hzsnの実際の結果・行為・集団参加・因果関係に、同じ原因行為のhztnを加える。成功しただけの妨害や、別行為の注意では満たさない。',
 'hztp':'旧hzsoの先行二段階を、慎重さの候補を同じ原因行為に結んだhztoへ更新する。対象者は提示時点で固定する。',
 'hztq':'同じ先行段階hztpの第二時点へ、従来と同じ許容欠如hztcを結ぶ。許容欠如と慎重さを同一視しない。',
 'hztr':'同じ危険提示と、更新した先行段階hztqを結ぶ。先行二段階相互の厳密な順序は増やさない。',
 'hzts':'更新した複文の部分記述hztrを著者に帰属させ、先行する監督の文との順序を保持する。引用した注意や目的を実行しない。',
 'hztt':'比喩の対象となる同じ本人への先行する阻止をhztoに更新し、同じ時点の許容欠如を保持する。',
 'hztu':'更新した対象側hzttと既存の閉じ込め描写zbfを、同じ関係節の非字義的な提示へ結ぶ。',
}
MAPPING={'hzsn':'hzto','hzso':'hztp','hzte':'hztq','hztf':'hztr','hztg':'hzts','hzth':'hztt','hzti':'hztu'}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+'''
d rqvp[agents h[a] c act a goal i[h[j[a]] e] bindings j[a] relevant h[a] c attention h[a a i[h[j[a]] e] j[a] a d] c aims h[a a i[h[j[a]] e] j[a] d] c occurs h[a d] c performs h[a a d] c scene d] c[
 w[c[v occurs][v act v scene]][w[g aspect a[c[v relevant][v aspect]]][
  f aspect a[y[c[v relevant][v aspect]][g actor a[w[c[v agents][v actor]][w[c[v performs][v actor v act v scene]][w[
   c[v aims][v actor v act v goal v bindings v scene]
  ][c[v attention][v actor v act v goal v bindings v aspect v scene]]]]]]
 ]]]
].
r hztj[a a i[h[j[a]] e] j[a] a d] c.
r hztk[a a i[h[j[a]] e] j[a] a d] c.
r hztl[a a i[h[j[a]] e] j[a] d] c.
d hztm[bindings j[a]] e[b scene[w[k hztb[v bindings]][g person a[w[a[v bindings][n p a b][v person]][t[k hzsm[v person]][v scene]]]]]].
d hztn[group a act a person a scene d] c[k rqvp[
 i[actor a][k hg[k mp[v group] v actor]] v act r[p hztm] l[a][v person]
 i[aspect a][k hztk[v group v act r[p hztm] l[a][v person] v aspect v scene]]
 p hztj p hztl p dg p df v scene
]].
d hzto[group a person a] e[b scene[w[k aa[v person]][w[k hi[k mp[v group] p aa]][
 k raa[i[actor a][k hg[k mp[v group] v actor]] v person k hzsm[v person] r[p hzsm] v scene
 i[act a point d][w[k dg[v act v point]][k hztn[v group v act v person v point]]] p df p g3]
]]]].
''')
    lookup={d['name']:d for d in old.document['declarations']}
    for name in ('hzso','hzte','hztf','hztg','hzth','hzti'):
        row=replace_symbols(deepcopy(lookup[name]),MAPPING);row['name']=MAPPING[name];doc['declarations'].append(row)
    doc['statements']=deepcopy(statements)
    for i in (35,36):doc['statements'][i]=replace_symbols(doc['statements'][i],MAPPING)
    doc=parse(format_graph(doc,'compact'));core=deepcopy(doc);core['declarations']=closure(doc,['hzts','hztu']);core['statements']=doc['statements'][35:]
    library=deepcopy(doc);library['declarations']=closure(doc,['rqvp']);library['statements']=[]
    added=doc['declarations'][size:];by_name={d['name']:d for d in added}
    basis=dict(status='goal_directed_distributed_attention_bound_to_causal_event',document=FULL,library=LIBRARY,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning) for n,(args,meaning) in PRIMITIVES.items()},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        limitations=['sorgfältigを、目的に沿った遂行上の関連事項へ注意を配るものとして読む候補。気遣いの感情や道徳的善さ、完全な成功と同一視しない。',
            '関連事項を原文が列挙しているとはしない。解釈で固定する範囲の全称条件であり、検査器の有限領域を現実の全事項だと認定しない。',
            '共同の遂行で注意を分担する読みを許す。全員が全事項へ注意を払うことは要求しないが、各担当者の参加・目的・注意は同じ行為へ固定する。',
            '注意の認知的機構や持続時間の測定方法は基本関係の解釈に残る。原語一語を新しいcareful述語へ置換したものではなく、注意・関連性・目的の関係を分ける。',
            '本文二文を更新し、他の35文と既存九単位の意味判断を保持する。穏順さ、強調、身体的描写、皮肉、学習と萎縮、第二段落全体の確認は残る。'])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/unpermitted-undertaking-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Goal-directed attention bound to the same prevention event',flush=True)


if __name__=='__main__':main()
