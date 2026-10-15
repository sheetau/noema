"""Reconnect local density's units to the earlier coordinate/light basis."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT
from scripts.compose_density_interpretation import INDEX,BINDINGS as PREVIOUS_BINDINGS
from scripts.compose_additive_charge import SOURCE as FIELDS

PARENT='examples/v014/einstein-sustained-assistance.noema'
FULL='examples/v014/einstein-density-units.noema'
CORE='examples/v014/density-units-manuscript.noema'
REVIEW='data/density-formula-review-v6.json'
BINDINGS={**PREVIOUS_BINDINGS,'lengthunit':'ta','timeunit':'rb'}
LIMITS=[
    '密度解釈の長さ・時間単位を、先行する光速度tcの評価で用いたta・rbへ結ぶ。旧zqi・zqjを独立に解釈したままtcの読みを無換算で使うことを、この本文の改訂読解では許さない。',
    'これは本文の固定単位を揃える修正であり、異なる単位での表現を禁止する一般規則ではない。別の単位を使う場合は光速度・系の速度・物質の速度・座標と場の値を整合して換算する必要がある。',
    '新旧の内容が同じになるには、旧zqiとta、旧zqjとrbの解釈がそれぞれ一致するなどの追加条件が必要である。異なる引用記述に対する著者の態度を、値の一致だけで移さない。',
    '電荷単位・電気的帰属・二系配置の構成説明、単位の実現、定義域の完全性と全文の意味一致は残る。今回の有理数の倍率検査を全実切断の解析や実際の校正の証明としない。',
]


def source_composed():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old)
    quote=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    expected=dict(kind='call',symbol='seoz',arguments=[dict(kind='call',symbol=PREVIOUS_BINDINGS[n],arguments=[]) for n,_ in FIELDS])
    assert quote==expected,'Unexpected current density quotation'
    quote['arguments']=[dict(kind='call',symbol=BINDINGS[n],arguments=[]) for n,_ in FIELDS]
    basis=json.loads((ROOT/'data/einstein-sustained-assistance-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-density-units-basis-v1',document=FULL)
    basis['unresolved']+=LIMITS
    basis['interpretation_revision']=dict(parent=PARENT,statement_index=INDEX,
        correction='Use the same length/time units as the preceding coordinate and light-speed readings',
        previous_bindings=PREVIOUS_BINDINGS,fixed_bindings=BINDINGS,equivalence_to_parent_proven=False,
        changed_arguments=['lengthunit','timeunit'],definitions_changed=False)
    audit_basis(doc,basis)
    return doc,basis


def review_packet():
    review=json.loads((ROOT/'data/density-formula-review-v5.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v6',supersedes='data/density-formula-review-v5.json',
        source_document=FULL,document=CORE,fixed_bindings=BINDINGS)
    for row in review['checks']:
        if row['id']=='source_context_bindings':
            row['evidence']='The authored quotation retains seoz and the same twelve other arguments, while lengthunit/timeunit now refer to ta/rb already used for the light-speed reading tc.'
            row['limit']='Electrical meaning, frame placement and calibration remain incomplete; independent new unit referents are no longer used by this quotation.'
        if row['id']=='concept_grounding':
            row['evidence']='Compositional density, velocity and signed totals use the same earlier coordinate length/time units. Charge, field and frame conventions still need explanation.'
        if row['id']=='whole_unit_decision':
            row['evidence']='The coordinate unit basis is now linked to the earlier light-speed basis; source-case coverage, added conditions and remaining basic meanings still need review.'
    review['checks'].insert(-1,dict(id='coordinate_unit_basis',status='connected_in_revised_reading',
        evidence='Only two arguments in statement 174 change: zqi/zqj become ta/rb. Actual seoz calls route rb to seou and ta/rb to seoy. Rational scaling contrasts expose the effect of mixing speed bases.',
        limit='Routing uses declared boundary abstractions. Finite cut probes and rational identities do not prove the full density law, source equivalence or physical calibration.'))
    review['evidence_reports'].append('reports/density-units-v1.json')
    review['semantic_completion']=False
    return review


def build():
    doc,basis=source_composed()
    selected=extract_document(doc,statement_indices=[INDEX])
    core_basis=extract_basis(doc,basis,selected,version='density-units-manuscript-basis-v1',document_path=CORE)
    files={FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(selected.document,'compact')+'\n',
        'data/einstein-density-units-basis-v1.json':basis,'data/density-units-manuscript-basis-v1.json':core_basis,
        REVIEW:review_packet()}
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
