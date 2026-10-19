"""Add an explicitly external, situation-local quietness depiction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure

PARENT='examples/v016/kant-scoped-quiet.noema'
PARENT_BASIS='data/scoped-quiet-basis-v1.json'
FULL='examples/v016/kant-quiet-depiction.noema'
CORE='examples/v016/quiet-depiction-core.noema'
LIBRARY='examples/v016/situated-episode-absence.noema'
BASIS='data/quiet-depiction-basis-v1.json'
ANNOTATIONS='data/quiet-depiction-identifiers-v1.json'
PRIMITIVES={
 'hzyc':(['body','episode','point'],'この生物の身体が、この状況の同じ出来事において自ら生じさせる外から現れる身体運動の主体である。意図した行為にも反射的・不随意の動きにも使える。別の身体の動きや、外から運ばれただけの移送と区別する。人の能動的な行為参加dfや、運動の実際の生起dgをこの関係だけから導かない。'),
 'hzyd':(['body','episode','reference','point'],'同じ身体の同じ運動がこの状況で、反復・速さ・急激な変化などの様式において、基準文脈で外面の動揺として目立つ水準にある。単に運動があることや高い移動速度だけでは決まらず、通常の落ち着いた身体動作との文脈上の比較を要する。尺度の数値や閾値は固定しない。内面的な感情、意図、抵抗、服従、能力、勇気、許容についての関係ではない。身体主体・生起は別条件。'),
}
MEANINGS={
 'rqz5':'指定した一状況について、同じ本人・出来事・状況のrqzzがないことを、rqz2の履歴と範囲をその一状況に固定して表す。単なる観測標本から他時点の不在へ一般化せず、持続的な性格や期間全体の不在は主張しない。',
 'rqz6':'同じ身体について、指定した先行状況で、実際に生起した自発的または不随意の身体運動のうち、基準文脈で外面の動揺として目立つものがない。hzyc・dg・hzydを同じ出来事へ結び、hzydの基準は指定した基準時点へ固定する。動いていないこと、内面の平静、非抵抗、服従と同一視しない。',
 'rqz7':'同じ本人を既存qkの家畜の描写として基準時点で再指示し、その基準時点より前の同じ先行状況でrqz6の外面の落ち着きがある。動物の分類・飼育・帰属はqkを継承し、神による創造や所有制度の正当性は付け加えない。',
 'r2aa':'同じ複文hztr(db)の同じ本人・先行時点・基準時点について、知的な阻止と許容欠如rqzwを、外面の落ち着いた家畜rqz7として非字義的に描写する。同じ人物位置へ先行する家畜像を引き継ぎ、現実にその人が動物であることや、内面が平静であることを主張しない。',
}
LIMITS=[
 'ruhigenを、同じ先行局面での外面の落ち着きとして読む部分解釈。内面の平静、非抵抗、従順な性格、他者への無害さの全てを語義へ詰め込まない。',
 'hzycは能動的な人の行為参加dfと異なり、動物や不随意の身体運動も扱う。hzydの文脈上の動揺判定は公開した知覚・評価上の基本関係であり、運動学や測定手順の全理論を構成したとはしない。',
 '一状況の不在として記述する。状況は記述する局面であって一点の観測値ではないが、別時点・生涯・恒常的な性格まで外挿しない。長期的な性向の読みを採る場合は別の構成を要する。',
 'Geschöpfeは先行の家畜像の同じ対象を指す呼び直しとして接続する。単語の全用法、神学的な創造論、修辞上の全含意を説明し終えたとはしない。',
 '本文へ一文追加するが、一文全体・段落全体の意味確認は増やさない。jaの強調、家畜と歩行の語義範囲、段落末尾、二作品全文の確認は残る。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='''
r hzyc[a a d] c.r hzyd[a a d d] c.
d rqz5[person a point d subject h[a a d] c occurs h[a d] c marked h[a d] c] c[
 k rqz2[v person i[s d][e[v s][v point]] i[s d][e[v s][v point]]
  i[a d b d][u[e[v a][v a]]] v subject v occurs v marked]
].
d rqz6[body a prior d anchor d] c[
 k rqz5[v body v prior p hzyc p dg i[episode a point d][k hzyd[v body v episode v anchor v point]]]
].
d rqz7[person a prior d anchor d] c[
 w[k dd[v prior v anchor]][w[t[k qk[v person]][v anchor]][k rqz6[v person v prior v anchor]]]
].
d r2aa[] c[k rqzv[k hzsq[] k wa[] r[k hztr[k db[]]] r[p rqzw] r[p rqz7] k wh[]]].
s[k r2aa[]].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (9,35,36,46,47,48)]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqz5']),statements=[])
    added=doc['declarations'][size:]
    basis=dict(status='external_quiet_livestock_depiction_at_shared_prior_point',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],
            meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/step-depiction-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Quiet external depiction appended; old 48 statements preserved',flush=True)


if __name__=='__main__':main()
