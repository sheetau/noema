"""Pin and collate all three optical-method sentences on original p. 915."""
from functools import lru_cache
from pathlib import Path
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-optical-problem-method.noema';BASIS='data/optical-problem-method-basis-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILES='data/mirror-reflection-facsimile-v1.json'
DOC='docs/optical-problem-method-v1.md';READING='data/einstein-optical-problem-method-reading-v1.json'
SOURCE='Nach der hier benutzten Methode können alle Probleme der Optik bewegter Körper gelöst werden. Das Wesentliche ist, daß die elektrische und magnetische Kraft des Lichtes, welches durch einen bewegten Körper beeinflußt wird, auf ein relativ zu dem Körper ruhendes Koordinatensystem transformiert werden. Dadurch wird jedes Problem der Optik bewegter Körper auf eine Reihe von Problemen der Optik ruhender Körper zurückgeführt.'

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));u=inv['units'][225];basis=json.loads(read(BASIS));catalog=load_catalog(ROOT,BASIS)
    assert u['text']==SOURCE and u['text_sha256']==digest(SOURCE.encode())=='50832023f8c9e811f8309365da2a81f33b710a6cdcf69d2d1d308d5ce35758ac'
    image=json.loads(read(FACSIMILES))['images'][1]
    assert image['printed_page']==915 and digest((ROOT/image['path']).read_bytes())==image['sha256']=='c2707543f7ee76f371f78c58ddf3410536810ab1c0568c5a5ee64d164ba96e60'
    sentences=SOURCE.split('. ');clauses=[];start=0
    for i,s in enumerate(sentences):
        if not s.endswith('.'):s+='.'
        clauses.append(dict(range=[start,start+len(s)],text=s,statements=[406],definitions=[('ekwz','ekw2','ekw3')[i]]));start+=len(s)+1
    count=len(re.sub(r'\s','',SOURCE));assert not u['math_ids'] and len(clauses)==3
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(SOURCE)],source=SOURCE,reviewed_prose_characters=count,math=[],statements=[406],definitions=list(basis['definitions']),selection=selection_binding(catalog,[406]),status='explicit_interpretive_annotation')
    paths=[INVENTORY,FACSIMILES,image['path'],DOC,'scripts/read_optical_problem_method.py']
    return dict(schema_version='noema-source-reading-1',status='three_optical_method_sentences_collated',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=[segment],clauses=clauses,reviewed_prose_characters=count,reviewed_math_elements=0,interpretation_limits=basis['limitations'],whole_unit_judgments_separate=True,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
