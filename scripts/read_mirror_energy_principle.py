"""Collate the moving mirror energy paragraph and pressure formula on p. 915."""
from functools import lru_cache
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.read_mirror_wave_quantities import shape
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-mirror-energy-principle.noema';BASIS='data/mirror-energy-principle-basis-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILES='data/mirror-reflection-facsimile-v1.json'
DOC='docs/mirror-energy-principle-v1.md';READING='data/einstein-mirror-energy-principle-reading-v1.json'
PRIOR='data/einstein-reflected-return-quantities-u0221-review-v1.json'
EXPECTED={'M0377':'pow(A,2)/8π(Vcosφ−v)','M0378':'pow(A,‴)pow(,2)/8π(−Vcospow(φ,‴)+v)','M0379':'P.v','M0380':'P','M0381':'P=2frac(pow(A,2),8π)frac(pow((cosφ−frac(v,V)),2),1−pow((frac(v,V)),2)).'}
@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));catalog=load_catalog(ROOT,BASIS);basis=json.loads(read(BASIS));math={m['id']:m for m in inv['math']};collated={}
    for n,expected in EXPECTED.items():
        m=math[n];assert digest(m['mathml'].encode())==m['sha256'];actual=shape(ET.fromstring(m['mathml']));assert actual==expected,(n,actual)
        collated[n]=dict(sha256=m['sha256'],structure=actual,facsimile_matches=True)
    image=json.loads(read(FACSIMILES))['images'][1];assert image['printed_page']==915 and digest((ROOT/image['path']).read_bytes())==image['sha256']
    segments=[]
    for index,u,count in zip((402,403),inv['units'][221:223],(359,0)):
        assert digest(u['text'].encode())==u['text_sha256']
        assert len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',u['text'])))==count
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],reviewed_prose_characters=count,math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']],statements=[index],definitions=list(basis['definitions']),selection=selection_binding(catalog,[index]),status='explicit_interpretive_annotation'))
    paths=[INVENTORY,FACSIMILES,DOC,PRIOR,image['path'],'docs/mirror-energy-work-v1.md','scripts/read_mirror_wave_quantities.py','scripts/read_mirror_energy_principle.py']
    return dict(schema_version='noema-source-reading-1',status='four_energy_sentences_and_pressure_display_collated',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=segments,math_collation=collated,reviewed_prose_characters=359,reviewed_math_elements=5,interpretation_limits=basis['limitations'],prime_square_reading='M0378の空基底msup平方は原刊のA‴全体の平方に対応する。',whole_unit_judgments_separate=True,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
