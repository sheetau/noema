"""Collate the return introduction and all six equalities against pp. 914–915."""
from functools import lru_cache
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.read_mirror_wave_quantities import shape
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-reflected-return-quantities.noema';BASIS='data/reflected-return-quantities-basis-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILES='data/mirror-reflection-facsimile-v1.json'
DOC='docs/reflected-return-quantities-v1.md';READING='data/einstein-reflected-return-quantities-reading-v1.json'
PRIOR='data/einstein-mirror-wave-quantities-u0219-review-v1.json'
EXPECTED={'M0375':'K','M0376':[
 'pow(A,‴)=pow(A,″)frac(1+frac(v,V)cospow(φ,″),sqrt(1−pow((frac(v,V)),2)))=Afrac(1−2frac(v,V)cosφ+pow((frac(v,V)),2),1−pow((frac(v,V)),2)),',
 'cospow(φ,‴)=frac(cospow(φ,″)+frac(v,V),1+frac(v,V)cospow(φ,″))=−frac((1+pow((frac(v,V)),2))cosφ−2frac(v,V),1−2frac(v,V)cosφ+pow((frac(v,V)),2)),',
 'pow(ν,‴)=pow(ν,″)frac(1+frac(v,V)cospow(φ,″),sqrt(1−pow((frac(v,V)),2)))=νfrac(1−2frac(v,V)cosφ+pow((frac(v,V)),2),pow((1−frac(v,V)),2)).',
]}
@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));catalog=load_catalog(ROOT,BASIS);basis=json.loads(read(BASIS));math={m['id']:m for m in inv['math']};collated={}
    for n,expected in EXPECTED.items():
        m=math[n];assert digest(m['mathml'].encode())==m['sha256'];root=ET.fromstring(m['mathml']);rows=root.findall('.//{*}mtr');actual=[shape(row) for row in rows] if rows else shape(root)
        assert actual==expected,(n,actual);collated[n]=dict(sha256=m['sha256'],structure=actual,facsimile_matches=True)
    images=json.loads(read(FACSIMILES))['images'];assert [x['printed_page'] for x in images]==[914,915]
    for im in images:assert digest((ROOT/im['path']).read_bytes())==im['sha256']
    segments=[]
    for index,u,count in zip(INDICES:=[400,401],inv['units'][219:221],(80,0)):
        assert digest(u['text'].encode())==u['text_sha256']
        assert len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',u['text'])))==count
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],reviewed_prose_characters=count,math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']],statements=[index],definitions=list(basis['definitions']),selection=selection_binding(catalog,[index]),status='explicit_interpretive_annotation'))
    paths=[INVENTORY,FACSIMILES,DOC,PRIOR,*[im['path'] for im in images],'docs/mirror-wave-quantities-v1.md','scripts/read_mirror_wave_quantities.py','scripts/read_reflected_return_quantities.py']
    return dict(schema_version='noema-source-reading-1',status='return_introduction_and_six_equalities_collated_without_correcting_source',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=segments,math_collation=collated,reviewed_prose_characters=80,reviewed_math_elements=2,interpretation_limits=basis['limitations'],frequency_disagreement=dict(light=5,speed=3,old_cosine=1,old_frequency=2,physical_and_middle='1/2',printed_rightmost='2',printed_denominator='(1-v/V)^2',not_transcription_correction=True),whole_unit_judgments_separate=True,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
