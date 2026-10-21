"""Compose normative possibility over complete hypothetical self-enactment histories."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_law_enactment import NAMES,FIELDS,ARGS

PARENTS=('data/posterity-rights-basis-v1.json','data/law-enactment-basis-v1.json')
LIBRARY='examples/v016/rational-self-imposition.noema'
BASIS='data/rational-self-imposition-basis-v1.json'
REF='k h26b7[]'
THREE='l[a]['+ARGS+']'
PRIMITIVES={
 'h26cf':('[a a a d d] c',list(NAMES)+['reference','candidate'],'固定した人民・政治的共同体・法案と評価基準について検討する反事実的な制度配置・採択経過の完全な範囲。この三対象の同一性・全成員・全条項の内容を保ち、経過の事実条件が相互に矛盾しない配置を含める。現在の統治形態、現実の立法権限、現在の賛否や心理的傾向を固定条件にせず、人民を公的採択の主体に置く制度配置も検討する。許可・自己賦課の成功・正当性を見て候補を選別しない。検討範囲を実際に列挙した成功例だけへ狭めず、不成功・不許可の経過も含む。履歴の順序整合性と自己賦課の生起は別に構成する。'),
 'h26cg':('[] a',[],'人民が自らに公的な法を課す資格を、理性的に正当化できる公的規律という観点から評価する規範の出所。現行法の権能付与者、君主、事実上の承認や多数の好みと区別する。人間の啓蒙・進展を後代も含めて放棄できないという周辺文脈と整合する評価を採用するが、具体的な許可・反対要求はh245c/h237zで同じ内容に別々に与える。この定数だけから特定法の正当性や倫理学全体を導かない。'),
 'h26ch':('[] a',[],'同じ人民が共同の公的規律を自ら定める側としての立場。個々人の私的な契約者の役割、特定国の現職、全員の直接投票や現実の同意と区別する。人民の共同主体性は同じ集団への採択帰属として構成し、立場の参照だけで正当な資格を認めない。'),
}
MEANINGS={
 'r5ep':'同じ人民・共同体・法のr5eiと固定基準h26b7について、結論から選別しない全仮定経過h26cfに属し、その経過の全履歴h257z/icが整合した厳密全順序をなす。自己賦課や許可の真偽は候補の条件に使わない。',
 'r5eq':'同じ人民・共同体・法の正確な三対象列を持つ段階1の自己賦課内容r5enに、h26cgの評価規範からh26chの人民自身の立場への正極性の積極的許可があり、反対極性の要求と衝突しないr37c。候補経過を同じ規範評価状況に置き、採択内容を引用したまま保持する。制度上の権能や実行だけでこの資格を代用しない。',
 'r5er':'同じ三対象・同じ一つの仮定経過でr5epの候補枠組み、r5eqの規範的資格、r5emの実際の自己賦課内容がともに成立する。仮定内で採択を成立させるが、現実の経過の採択を断言せず、別候補の資格と実行可能な採択を寄せ集めない。',
 'r5es':'同じ人民・共同体・法についてr5erの仮定経過が少なくとも一つある。原文のkönnteを、人民自身の公的な自己賦課が規範的に許容される仮定を置き得ることとして読む。全候補で成功する必然性、現実の出来事、現在の制度的権能、単なる禁止不在とは異なる。候補が空なら偽。',
 'r5et':'正確な人民・共同体・法の三個体列からr5esの規範的な自己賦課可能性を返す閉じた内容族。外側の評価点が変わっても、固定した評価基準h26b7と同じ全候補範囲を保持する。特定国や特定法だけへ一般的な問いを限定しない。',
 'r5eu':'同じ三対象のr5etが成立するかを既存rijで問う正極性の質問。肯定も否定も未回答のまま保持し、問いの記述を引用して提示するだけでr5esや採択・資格を実行しない。wohlの談話上の提示と問いの著者帰属は別に接続する。',
}
LIMITS=[
 'u0013第六文[1265,1436)のkönnteに向けた規範的可能性の依存群。全文の試金石・kann・wohl・一般量化・著者帰属は未接続。第六文の確認文字数は加算しない。',
 'この文の前後では権力による承認があっても無効な合意、暫定的に可能な秩序、決して許されない啓蒙の放棄を区別する。その文脈から、単なる物理的実行能力でなく理性的に正当な自己賦課の可能性と読む。理性的な共同意思を、ここでは同じ全人民へ帰属する公的採択が同じ内容について規範的に許容されることとして操作化する。',
 'この読みは全員の心理的賛同・実際の投票・独立した熟慮行為の列・現行制度での立法資格を追加しない。1793年の原始契約論は可能な同意と実際の同意を区別する比較資料であり、その学説全体・市民権区分・臣民の服従義務を1784年の本文へ輸入しない。',
 '候補範囲は結論独立の入力であり、対象の同一性・全成員・全条項を保った相互に矛盾しない仮定の制度配置を全て扱う。現在の制度で人民が立法できないという一点で空範囲にせず、不成功・不許可の候補も含む。有限モデルによる検査はこの入力の全現実的網羅性の証明ではない。',
 '許可と反対要求は同じ規範源・人民・立場・閉じた内容・三対象列・同じ候補に結ぶ。積極的許可なし、反対要求あり、未知の入力を成功扱いしない。自己賦課内容は同じ候補の完全な履歴と同じ活動・全条項の制度的成立で実評価する。',
 '評価規範は外部入力として意味を明示する。正当な法の一覧や理性の一般的決定手続を導いたとはしない。後続文の暫定的秩序や恒久的な宗教体制の禁止は、それぞれ本文でこの問いへの適用として接続する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    history='i[point d][k h257z['+REF+' v candidate v point]]'
    order='i[before d after d][k ic[v before v after v candidate]]'
    text='d r5ep['+FIELDS+' candidate d] c['+both('k r5ei['+ARGS+' '+REF+']','k h26cf['+ARGS+' '+REF+' v candidate]','k ta['+history+' '+order+']')+'].\n'
    text+='d r5eq['+FIELDS+' candidate d] c[k r37c[k h26cg[] v people k h26ch[] r b[p r5en] '+THREE+' '+REF+' v candidate]].\n'
    text+='d r5er['+FIELDS+' candidate d] c['+both('k r5ep['+ARGS+' v candidate]','k r5eq['+ARGS+' v candidate]','k r5em['+ARGS+' '+REF+' v candidate]')+'].\n'
    text+='d r5es['+FIELDS+'] c[g candidate d[k r5er['+ARGS+' v candidate]]].\n'
    text+='d r5et[bindings j[a]] e[b point['+bind(NAMES,'k r5es['+ARGS+']')+']].\n'
    text+='d r5eu[bindings j[a]] f[k rij[k r5et[v bindings] '+TRUE+']].\n'
    return text
def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r37c','rij'],['r5ei','r5em','r5en','h26b7'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='normatively_permitted_hypothetical_self_imposition',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
