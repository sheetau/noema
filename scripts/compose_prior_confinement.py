"""Bind an onset and its continuing state to the selected prior stage."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT='examples/v016/kant-insistent-framing.noema'
PARENT_BASIS='data/insistent-framing-basis-v1.json'
FULL='examples/v016/kant-prior-confinement.noema'
CORE='examples/v016/prior-confinement-core.noema'
LIBRARY='examples/v016/stage-bound-persistence.noema'
BASIS='data/prior-confinement-basis-v1.json'
ANNOTATIONS='data/prior-confinement-identifiers-v1.json'
MEANINGS={
 'r2ad':'同じ履歴の指定局面までに一つの過程による不成立から成立への変化があり、その成立端から指定終点まで評価が整った同じ状態が途切れず続く。指定局面と終点は履歴に属し、局面は終点以前。変化の前端も評価が整っている。過程と前後端を一つの存在量化の内部で保持し、終点だけの状態や後の別の成立過程を代用しない。局面と終点が同じなら、その局面までの成立・継続だけを要求する。',
 'r2ae':'r2adの同じ対象・装置・制限・履歴を既存の閉じ込めの成立zbd、状態zbb、評価zbcに固定する。後見人が参加する同じ適用過程の成立端は指定局面以前で、そこから終点まで同じ制限が続く。対象・装置・制限を途中で取り替えない。',
 'r2af':'同じ複文の本人・先行局面・後の基準時点について、先行局面までに成立してその局面へ続く閉じ込めを描く。本人の家畜像と対応する歩行訓練装置の指示は基準時点のまま保持し、制限の履歴と終点は先行局面に置く。警告時点までの継続は追加しない。',
 'r2ag':'同じ複文hztr(db)の同じ本人・先行局面・基準時点について、阻止と許容欠如rqzwを先行局面での閉じ込めr2afとして非字義的に描写する。旧hztuの独立した過去の存在条件を、この型付きの局面対応へ置き換える。世界の内容の真理や同値性を主張しない。',
}
LIMITS=[
 '原文darin sie sie einsperretenを、その装置外への試みを許さなかった局面に成立していた閉じ込めとして読む。この文脈上の結合は解釈判断であり、ドイツ語の時制だけから唯一の時間構造を証明したとはしない。',
 '警告まで継続した読みはr2aeの終点を後の基準時点へ置けば別に記述できる。本文はその追加の継続を要求しない。閉じ込めの行為と、知的活動を阻止した原因行為を同一の出来事にはしない。',
 '履歴は意味上の完全な評価範囲を引数で指定する。有限観測の欠落を状態の継続とみなさず、taは現実の履歴の網羅性までは証明しない。',
 '旧宣言と意味規約は保持し、本文の第36文（ゼロ始まり）の描写対応を改訂する。残り49文と既存十一単位の判断は保持する。一文全体・段落全体・二作品全文の意味確認は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def conjunction(*parts):
    return parts[0] if len(parts)==1 else 'w['+parts[0]+']['+conjunction(*parts[1:])+']'


def build():
    old=parent();doc=deepcopy(old.document);assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    le=lambda a,b:'x[e[v '+a+'][v '+b+']][c[v before][v '+a+' v '+b+']]'
    selected=conjunction('c[v history][v point]',le('end','point'),le('point','endpoint'))
    sustained='f point d[y['+selected+']['+conjunction('c[v valid][v point]','t[v state][v point]')+']]'
    witness=conjunction('k th[v history v before v process v first v end v onset v state]',
        'c[v valid][v first]',le('end','stage'),sustained)
    body=conjunction('c[v history][v stage]','c[v history][v endpoint]',le('stage','endpoint'),
        'g process a[g first d[g end d['+witness+']]]')
    text='d r2ad[history h[d] c before h[d d] c stage d endpoint d onset h[a d d] c state e valid h[d] c] c['+body+'].\n'+'''
d r2ae[person a carrier a restriction a stage d endpoint d] c[
 k r2ad[i[point d][k zba[v restriction v person v carrier v endpoint v point]] p dd v stage v endpoint
  i[process a first d end d][k zbd[v person v carrier v restriction v process v first v end v endpoint]]
  k zbb[v person v carrier v restriction] i[point d][k zbc[v person v carrier v restriction v point]]]
].
d r2af[person a prior d anchor d] c[
 w[k dd[v prior v anchor]][w[t[k qk[v person]][v anchor]][w[t[k zam[k qs[v person v anchor]]][v anchor]][
  g restriction a[k r2ae[v person k qs[v person v anchor] v restriction v prior v prior]]]]]
].
d r2ag[] c[k rqzv[k hzsq[] k wa[] r[k hztr[k db[]]] r[p rqzw] r[p r2af] k wh[]]].
s[k r2ag[]].
'''
    doc=parse(format_graph(doc,'compact')+text);replacement=doc['statements'][0]
    assert statements[36]==dict(kind='assert',body=dict(kind='call',symbol='hztu',arguments=[]))
    statements[36]=replacement;doc['statements']=statements
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (9,35,36,46,47,48,49)]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['r2ad']),statements=[])
    added=doc['declarations'][size:]
    basis=dict(status='confinement_bound_to_prevention_stage_without_later_persistence_assumption',
        document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/insistent-framing-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print('Four definitions, no new primitives; statement 36 revised, other 49 statements retained',flush=True)


if __name__=='__main__':main()
