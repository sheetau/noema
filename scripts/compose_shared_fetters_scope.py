"""Keep the third sentence's case participants in the preceding person scope."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-generic-fetters.noema'
PARENT_BASIS = 'data/generic-fetters-basis-v1.json'
FULL = 'examples/v016/kant-shared-fetters-scope.noema'
CORE = 'examples/v016/shared-fetters-scope-core.noema'
LIBRARY = 'examples/v016/referential-range.noema'
BASIS = 'data/shared-fetters-scope-basis-v1.json'
ANNOTATIONS = 'data/shared-fetters-scope-identifiers-v1.json'
MEANINGS = {
    'r2fx': '非空の事例範囲の全てについて、その事例から役割写像で選ぶ対象が、同じ指定された参照範囲に属する。範囲外の役割対象を持つ事例を除外してから検査しない。写像の単射性や参照範囲への全射性は要求しない。',
    'r2fy': '第三文の提示文脈で選ぶ全比較事例の利用者を、第一文の箇所hzzqに属する同じ提示文脈の人物範囲hzznへ結ぶ。各利用者が人であることも要求する。事例の使用基準hzzzeを談話の基準に代用しない。',
    'r2fz': '第三文の比較事例の人物参照r2fyが整合し、その同じ文脈で既存r2fuの二種類への一般化が成立する内容。参照範囲外の事例を落として一般化を成立させない。',
    'r2g3': '足枷の比喩に渡す対象・本人の二位置を保ち、本人が人で、第一文からの人物範囲に属することと、同じ本人へのr2fsの条件付き作用を合わせる。人物範囲は提示文脈whで固定し、作用の基準点は別に保つ。',
    'r2g2': '第三文の主張内容を人物参照付きr2fzへ、比喩の対象関係を同じ人物範囲付きr2g3へ更新する。同格、言い直し、前後文との順序は保持する。引用された内容の実在や真理を帰属だけから主張しない。',
}
LIMITS = [
    'seinerは第一文の各人について続ける説明として読む。第三文の利用者はその同じ人物範囲に属する。これは採用する読解であり、ドイツ語のあらゆる文脈における人称解決の規則ではない。',
    '全比較事例の利用者を参照範囲へ結ぶが、全ての先行人物を比較事例へ登場させることや、一人につき一事例だけであることは要求しない。一般化の例外を範囲外人物へ移すことも許さない。',
    '人物範囲は提示文脈に固定する。仮定の使用時点・継続履歴の時点で人物範囲を選び直さず、未指定の人物を著者や特定の実在人へ補完しない。',
    '第三文の語義・持続の強さ、第四文のsieが受ける除去対象と知的活動への比喩対応は未完。今回の人物接続で文全体の意味一致を完了したとはしない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''d r2fx[cases h[a] c role h[a] a referents h[a] c] c[w[g item a[c[v cases][v item]]][f item a[y[c[v cases][v item]][c[v referents][c[v role][v item]]]]]].
d r2fy[scope d] c[k r2fx[i[item a][k hzzzb[v scope v item]] i[item a][k hzzzd[v scope v item]] i[person a][w[k aa[v person]][k hzzn[k hzzq[] v person v scope]]]]].
d r2fz[] e[b scope[w[k r2fy[v scope]][t[k r2fu[]][v scope]]]].
d r2g3[participants j[a]] e[k rbv[i[object a person a][b anchor[w[k aa[v person]][w[k hzzn[k hzzq[] v person k wh[]]][k r2fs[k wh[] v object v person v anchor]]]]] v participants]].
'''


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not set(MEANINGS)&set(old.entries)
    doc=parse(format_graph(doc,'compact')+definitions())
    row=deepcopy(old.entries['r2fv']['declaration']);row['name']='r2g2'
    def replace(node):
        if isinstance(node,dict):
            if node.get('symbol') in ('r2fu','r2ft'):node['symbol']={'r2fu':'r2fz','r2ft':'r2g3'}[node['symbol']]
            for value in node.values():replace(value)
        elif isinstance(node,list):
            for value in node:replace(value)
    replace(row);doc['declarations'].append(row)
    assert len(statements)==54 and statements[52]['body']['symbol']=='r2fv'
    statements[52]=dict(kind='assert',body=dict(kind='call',symbol='r2g2',arguments=[]))
    doc['statements']=statements;doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core.update(declarations=closure(doc,['r2g2']),statements=statements[52:53])
    library=deepcopy(doc);library.update(declarations=closure(doc,['r2fx']),statements=[])
    added=doc['declarations'][len(old.document['declarations']):];assert len(added)==5
    basis=dict(status='shared_third_sentence_person_scope_candidate',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/generic-fetters-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print('Third-sentence participants bound to preceding person scope; no new primitives',flush=True)
