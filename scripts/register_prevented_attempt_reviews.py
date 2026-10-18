"""Carry nine unchanged whole-unit judgments to the extended manuscript."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_prevented_attempt import ROOT,FULL,BASIS,ANNOTATIONS

PREVIOUS='data/semantic-review-index-v26.json'
INDEX='data/semantic-review-index-v27.json'
FORMAL='reports/prevented-attempt-v1.json'
READING='docs/prevented-attempt-v1.md'


def encoded(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'


def build():
    old_index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));load_reviews(ROOT,PREVIOUS)
    active=old_index['works']['kant-1784'];old_cat=load_catalog(ROOT,active['meaning_basis']);cat=load_catalog(ROOT,BASIS)
    formal=json.loads((ROOT/FORMAL).read_text(encoding='utf-8'));validate_hashes(ROOT,formal['source_sha256'])
    assert formal['structure']['nine_review_bindings_preserved'] and formal['structure']['previous_statements_preserved']==35
    paths=set(cat.source_sha256)|set(formal['source_sha256'])|{FULL,BASIS,ANNOTATIONS,FORMAL,READING,'scripts/register_prevented_attempt_reviews.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};outputs={};migrated=[]
    for path in active['reviews']:
        old=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[x['index'] for x in old['selection']['statements']]
        assert selection_binding(old_cat,indices)==old['selection']==selection_binding(cat,indices)
        new=deepcopy(old);new.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
            revalidated_from=path,revalidation='Selected statements, transitive definitions and meaning conventions are unchanged; no whole-unit judgment is added for the second paragraph.')
        new['evidence']['formal_checks'].append(FORMAL);new['evidence']['semantic_reading'].append(READING)
        new['source_sha256'].update(pins);new['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/prevented-attempt-inherited-'+old['unit'].split(':')[-1]+'-review-v1.json';outputs[name]=encoded(new);migrated.append(name)
    assert len(migrated)==9
    index=deepcopy(old_index);index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,reviews=migrated)
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(body.encode('utf-8')) for p,body in outputs.items()});outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    old=load_reviews(ROOT,PREVIOUS);new=load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']};after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(after)==set(before) and len(after)==9 and 'kant-1784:u0009' not in after
    assert sum(r['source_nonblank_characters'] for r in after.values())==587
    assert new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        a=json.loads((ROOT/row['review']).read_text(encoding='utf-8'));b=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k]==b[k] for k in ('selection','source','decision','reviewer','interpretation','requirements','unresolved'))
        assert b['revalidated_from']==row['review']
    assert not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=9,reviewed_nonblank_characters=587,new_whole_unit_judgments=0,second_paragraph_unreviewed=True)


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
