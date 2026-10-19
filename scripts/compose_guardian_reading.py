"""Bind focused assurance and additive framing to the existing guardian claim."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-benevolent-framing.noema'
PARENT_BASIS='data/benevolent-framing-basis-v1.json'
FULL='examples/v016/kant-guardian-reading.noema'
CORE='examples/v016/guardian-reading-core.noema'
LIBRARY='examples/v016/assured-addition.noema'
BASIS='data/guardian-reading-basis-v1.json'
ANNOTATIONS='data/guardian-reading-identifiers-v1.json'
PRIMITIVES={
    'hzxu':(['node','presenter','claim_description','focused_content_description','context'],
        '提示者が同じ箇所・文脈の指定主張の中で、指定した焦点内容を確かなものとして確言しているという提示態度。焦点内容と基礎主張を別々に結び、同じ箇所の別の主張や別の焦点へ流用しない。実際の知識・内心の確信度・真理・必然性・成功保証・未来性・既に生じたことは含意しない。'),
    'hzxv':(['node','presenter','claim_description','background_description','addition_description','context'],
        '提示者が同じ箇所・文脈の指定主張の中で、指定した背景の性質記述を既に置いた内容として扱い、それに加えて指定した追加の性質記述を提示する。二つの人物引数は主張内の同じ人物位置へ対応する。単なる無順序の連言と、背景と追加の順序を区別する。引用内容の現実の真理、聞き手の既知・同意、時間的な先後、因果、全ての可能な追加項目を尽くすことは含意しない。'),
}
MEANINGS={
    'rqyx':'現在のdoのうち、同じ母集団の危険判断分布が成立し、同じ後見人群の目的を持つ生起行為がその分布へ実際に寄与する部分だけを内容として取り出す。監督の立場と負担の挿入説明は含めない。do本体の対応する部分式と構文が一致する。',
    'rqyy':'同じ箇所・提示者・主張記述・文脈の主張帰属と、その主張内の指定焦点内容への確言を結ぶ。基礎主張と焦点内容は実行評価しない。',
    'rqyz':'同じ箇所・提示者・主張記述・文脈の主張帰属に、異なる二つの性質記述の背景から追加への提示順序を結ぶ。二記述の人物位置は同じで、現実の真理や聞き手の既知性は別である。',
    'rqy2':'同じ後見人の箇所dq・著者wa・主張dp・提示文脈whに、同じ後見人群dbの働きかけrqyxへの確言と、負担uyの挿入説明へ危険判断uxを付け加える提示を結ぶ。schonを確言、auchを追加として読むこの一文の接続であり、実際の危険性uwを追加の事実主張にしない。',
}
LIMITS=[
    'schonはこの文の因果的な働きかけを確言する用法として読み、時間の既了、唯一の原因、全可能世界での保証へは置き換えない。',
    'außer dem daßとauchは、著者の負担の挿入説明に人々の危険判断を追加する読み。負担自体を後見人が生じさせた結果へ含めない。',
    '後見人の目的は現行rqygの分配的な読みを採る。記述対象の参加者たちが同じ活動で同じ目的を目指すという読解であり、現実の全後見人、相互承認・合意・指揮階層まで主張しない。',
    '意味の確認は明示したこの一文の読みと公開した基本関係に依存する。全ての解釈の同時保存、独立査読、自動的な同義証明、基本関係の全内部構造の説明ではない。',
    '既存45文と全ての既存定義は保持する。新しい文45の提示条件を加え、第二段落全体や二作品全文を完了扱いにしない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def focus_declaration():
    original=parent().entries['do']['declaration'];found=[]
    def walk(node):
        if isinstance(node,list):
            for x in node:walk(x)
        elif isinstance(node,dict):
            if node.get('kind')=='and':
                first=node['arguments'][0]
                if first.get('kind')=='evaluate' and first['content'].get('symbol')=='rqyd':found.append(node)
            for value in node.values():walk(value)
    walk(original['body']);assert len(found)==1
    result=deepcopy(original);result['name']='rqyx';result['body']['body']=deepcopy(found[0])
    return result


def build():
    old=parent();doc=deepcopy(old.document);assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc['declarations'].append(focus_declaration())
    text='''
r hzxu[a a i[e] i[e] d] c.
r hzxv[a a i[e] i[h[a] e] i[h[a] e] d] c.
d rqyy[node a presenter a claim i[e] focus i[e] context d claims h[a a i[e] d] c assures h[a a i[e] i[e] d] c] c[
 w[c[v claims][v node v presenter v claim v context]][c[v assures][v node v presenter v claim v focus v context]]
].
d rqyz[node a presenter a claim i[e] background i[h[a] e] addition i[h[a] e] context d claims h[a a i[e] d] c adds h[a a i[e] i[h[a] e] i[h[a] e] d] c] c[
 w[u[e[v background][v addition]]][w[c[v claims][v node v presenter v claim v context]][c[v adds][v node v presenter v claim v background v addition v context]]]
].
d rqy2[] c[w[k rqyy[k dq[] k wa[] r[k dp[]] r[k rqyx[k db[]]] k wh[] p uc p hzxu]][
 k rqyz[k dq[] k wa[] r[k dp[]] r[p uy] r[p ux] k wh[] p uc p hzxv]
]].
s[k rqy2[]].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],
        meaning_ja=PRIMITIVES[d['name']][1]) for d in doc['declarations'][size:] if d['kind']=='primitive'}
    basis=dict(status='guardian_sentence_with_focused_assurance_and_addition',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (7,8,44,45)]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqyy','rqyz']),statements=[])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/benevolent-framing-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    encoded=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:encoded(basis),ANNOTATIONS:encoded(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Focused assurance and additive presentation composed',flush=True)


if __name__=='__main__':main()
