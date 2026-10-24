"""Collate the leading pressure approximation on original p. 915."""
from functools import lru_cache
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.read_mirror_wave_quantities import shape
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-pressure-leading-approximation.noema';BASIS='data/pressure-leading-approximation-basis-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILES='data/mirror-reflection-facsimile-v1.json'
DOC='docs/pressure-leading-approximation-v1.md';READING='data/einstein-pressure-leading-approximation-reading-v1.json'
PRIOR='data/einstein-mirror-energy-principle-u0223-review-v1.json'
@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));catalog=load_catalog(ROOT,BASIS);basis=json.loads(read(BASIS));math={m['id']:m for m in inv['math']};m=math['M0382']
    assert digest(m['mathml'].encode())==m['sha256'];actual=shape(ET.fromstring(m['mathml']));assert actual=='P=2frac(pow(A,2),8π)pow(cos,2)φ.'
    image=json.loads(read(FACSIMILES))['images'][1];assert image['printed_page']==915 and digest((ROOT/image['path']).read_bytes())==image['sha256']
    segments=[]
    for index,u,count in zip((404,405),inv['units'][223:225],(80,0)):
        assert digest(u['text'].encode())==u['text_sha256']
        assert len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',u['text'])))==count
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],reviewed_prose_characters=count,math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']],statements=[index],definitions=list(basis['definitions']),selection=selection_binding(catalog,[index]),status='explicit_interpretive_annotation'))
    assert not segments[0]['source'].endswith(':')
    paths=[INVENTORY,FACSIMILES,DOC,PRIOR,image['path'],'docs/mirror-energy-principle-v1.md','scripts/read_mirror_wave_quantities.py','scripts/read_pressure_leading_approximation.py']
    return dict(schema_version='noema-source-reading-1',status='leading_pressure_result_and_two_agreement_branches_collated',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=segments,math_collation={'M0382':dict(sha256=m['sha256'],structure=actual,facsimile_matches=True)},reviewed_prose_characters=80,reviewed_math_elements=1,interpretation_limits=basis['limitations'],approximation=dict(parameter='v/V',retained_order=0,fixed=['pi','A','V','cos(phi)'],not_linear_Taylor_approximation=True),whole_unit_judgments_separate=True,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
