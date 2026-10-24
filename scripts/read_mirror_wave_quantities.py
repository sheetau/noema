"""Collate every row and sign of the incident/reflected k-frame display group."""
from functools import lru_cache
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-mirror-wave-quantities.noema';BASIS='data/mirror-wave-quantities-basis-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILES='data/light-complex-facsimile-v1.json'
DOC='docs/mirror-wave-quantities-v1.md';READING='data/einstein-mirror-wave-quantities-reading-v1.json'
PRIOR='data/einstein-reflected-light-inquiry-u0215-review-v1.json'
EXPECTED={
 'M0369':'A,cosφ,ν','M0370':'K','M0371':'k',
 'M0372':['pow(A,′)=Afrac(1−frac(v,V)cosφ,sqrt(1−pow((frac(v,V)),2))),','cospow(φ,′)=frac(cosφ−v/V,1−frac(v,V)cosφ),','pow(ν,′)=νfrac(1−frac(v,V)cosφ,sqrt(1−pow((frac(v,V)),2))).'],
 'M0373':'k','M0374':['pow(A,″)=pow(A,′),','cospow(φ,″)=−cospow(φ,′),','pow(ν,″)=pow(ν,′).'],
}
def shape(e):
    tag=e.tag.split('}')[-1];children=list(e)
    if tag=='mfrac':return 'frac('+shape(children[0])+','+shape(children[1])+')'
    if tag=='msqrt':return 'sqrt('+''.join(map(shape,children))+')'
    if tag=='msup':return 'pow('+shape(children[0])+','+shape(children[1])+')'
    return (e.text or '').replace('\u2061','')+''.join(map(shape,children))

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));catalog=load_catalog(ROOT,BASIS);basis=json.loads(read(BASIS));math={m['id']:m for m in inv['math']};collated={}
    for n,expected in EXPECTED.items():
        m=math[n];assert digest(m['mathml'].encode())==m['sha256'];root=ET.fromstring(m['mathml']);rows=root.findall('.//{*}mtr');actual=[shape(row) for row in rows] if rows else shape(root)
        assert actual==expected,(n,actual);collated[n]=dict(sha256=m['sha256'],structure=actual,facsimile_matches=True)
    image=json.loads(read(FACSIMILES))['images'][1];assert image['printed_page']==914 and digest((ROOT/image['path']).read_bytes())==image['sha256']
    segments=[]
    for index,u,count in zip(range(396,400),inv['units'][215:219],(111,0,73,0)):
        assert digest(u['text'].encode())==u['text_sha256']
        assert len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',u['text'])))==count
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],reviewed_prose_characters=count,math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']],statements=[index],definitions=list(basis['definitions']),selection=selection_binding(catalog,[index]),status='explicit_interpretive_annotation'))
    paths=[INVENTORY,FACSIMILES,DOC,PRIOR,image['path'],'docs/aberration-line-v1.md','scripts/read_mirror_wave_quantities.py']
    return dict(schema_version='noema-source-reading-1',status='incident_and_reflected_k_quantities_collated_under_inherited_line_angle_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=segments,math_collation=collated,reviewed_prose_characters=184,reviewed_math_elements=6,interpretation_limits=basis['limitations'],angle_disagreement=dict(light='5',speed='3',old_normal=['111/145','48/145','80/145'],moving_normal=['15/49','24/49','40/49'],moving_line=['111/161','60/161','100/161'],moving_cosine='145/161',printed_moving_cosine='15/49',reflected_cosine='3775/7889',printed_reflected_cosine='-145/161',printed_equations_preserved=True,not_added_to_premise=True),whole_unit_judgments_separate=True,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
