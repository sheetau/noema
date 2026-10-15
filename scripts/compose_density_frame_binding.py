"""Bind the density formula to the previously introduced ordered frame pair."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,both,op
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_boost import CUT,FRAMES
from scripts.compose_density_units import INDEX,FIELDS,BINDINGS as PREVIOUS_BINDINGS

PARENT='examples/v014/einstein-density-units.noema'
FULL='examples/v014/einstein-density-frame-binding.noema'
CORE='examples/v014/density-frame-binding-manuscript.noema'
LIBRARY='examples/v014/ordered-value-binding.noema'
REVIEW='data/density-formula-review-v7.json'
BINDINGS={**PREVIOUS_BINDINGS,'frames':'sewz'}
BOUND=[('expectedfirst','a'),('expectedsecond','a'),('expectedvalue',CUT),
    ('first','a'),('second','a'),('value',CUT),('context','d'),
    ('valid','h['+CUT+'] c'),('same','h['+CUT+' '+CUT+'] c'),('relation',FRAMES)]


def definitions():
    text=definition('sewy',params(BOUND),both(
        op('e',v('first'),v('expectedfirst')),op('e',v('second'),v('expectedsecond')),
        app(v('valid'),v('expectedvalue')),app(v('valid'),v('value')),
        app(v('same'),v('value'),v('expectedvalue')),
        app(v('relation'),v('first'),v('second'),v('value'),v('context'))))
    bound=dict(expectedfirst=k('ra'),expectedsecond=k('zbm'),expectedvalue=k('zb7'),
        valid='p ba',same='p sca',relation=k('zqf'))
    text+=definition('sewz','','i[first a second a value '+CUT+' context d]['+both(
        op('u',op('e',k('ra'),k('zbm'))),k('sewy',*args(BOUND,**bound)))+']',FRAMES)
    return text


MEANINGS={
    'sewy':'同じ順序付き二参照と有効な値を、指定した比較規約で固定値へ結び、元の関係も同じ引数・文脈で要求する。参照の一致から元の関係の成立を補わず、逆順や逆符号への変換も推定しない。',
    'sewz':'本文で先に導入した異なる静止系ra・移動系zbmと符号付き速度zb7に、同じ文脈の標準配置関係zqfを結ぶ。値の一致は実切断の比較sca、妥当性はbaで確認する。配置の物理的な条件はzqfに残す。',
}
LIMITS=[
    'M0390の新旧二系と速度を、先行する設定のra・zbm・zb7へ固定する改訂読解である。個々のNoema解釈で選ぶ値を固定するもので、言語全体で数値速度を定数化する規則ではない。',
    'zqfの物理的な標準配置は保持し、二系と速度の参照一致だけで成立したとしない。平行と正の向きの一致、共通原点・時計原点、慣性系、配置・測定の構成説明は引き続き必要である。',
    '元の関係が別の系・速度にも真なら、新しい関係はその場合を除外する。原文の二系を指す範囲を明示する修正であり、旧解釈との無条件の同義性を主張しない。式を満たす場合だけを選ぶ操作ではない。',
    '源の文脈を初期配置の状況zb4や運動段階zb6と同一化しない。元の配置関係には呼び出し時の同じ文脈を渡す。逆順にした二系へ速度の符号を反転してよいかは、別の物理的対応として検証する。',
    '物理内容は条件文であり、元の配置関係がない場合は適用する場合が失われ得る。関係の存在や対象範囲の完全性を、この参照の固定だけから認定しない。未知の入力を空範囲へ補完しない。',
    '電気的帰属・全実数の解析・単位校正・原文単位全体の意味一致は未完である。有限モデルの対照例を実際の配置や全空間の証明としない。',
]


def source_composed():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    quote=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    expected=dict(kind='call',symbol='seoz',arguments=[dict(kind='call',symbol=PREVIOUS_BINDINGS[n],arguments=[]) for n,_ in FIELDS])
    assert quote==expected
    quote['arguments']=[dict(kind='call',symbol=BINDINGS[n],arguments=[]) for n,_ in FIELDS]
    basis=json.loads((ROOT/'data/einstein-density-units-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-density-frame-binding-basis-v1',document=FULL)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    basis['interpretation_revision']=dict(parent=PARENT,statement_index=INDEX,changed_arguments=['frames'],
        previous_bindings=PREVIOUS_BINDINGS,fixed_bindings=BINDINGS,equivalence_to_parent_proven=False,
        new_primitives=0,configuration_relation_retained='zqf')
    audit_basis(doc,basis)
    return doc,basis


def review_packet():
    review=json.loads((ROOT/'data/density-formula-review-v6.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v7',supersedes='data/density-formula-review-v6.json',
        source_document=FULL,document=CORE,fixed_bindings=BINDINGS)
    for row in review['checks']:
        if row['id']=='source_context_bindings':
            row['evidence']='The quotation keeps its author, scope and coordinate units. Its frame relation is now sewz, binding ra, zbm and zb7 while retaining the original physical configuration predicate zqf.'
            row['limit']='Frame identity and signed speed are bound; physical alignment, origins, clocks and complete source-case coverage remain open.'
    review['checks'].insert(-1,dict(id='ordered_frame_reference_binding',status='connected_in_revised_reading',
        evidence='sewz uses the same ra/zbm pair and zb7 velocity as the earlier setup, requires their distinct identity, and passes the caller context unchanged to zqf. Tests separate reversed pairs, signs and missing configuration.',
        limit='The binding restricts the source pair; it does not replace zqf with a physical derivation or prove that every intended source case is present.'))
    review['integrated_symbols']+=['sewy','sewz']
    review['evidence_reports'].append('reports/density-frame-binding-v1.json')
    review['semantic_completion']=False
    return review


def build():
    doc,basis=source_composed()
    files={FULL:format_graph(doc,'compact')+'\n','data/einstein-density-frame-binding-basis-v1.json':basis,REVIEW:review_packet()}
    for path,roots,indices in ((CORE,[],[INDEX]),(LIBRARY,['sewy'],[])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
