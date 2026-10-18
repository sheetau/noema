"""Carry eight unchanged judgments forward; add no opening-paragraph judgment."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_courageous_undertaking import ROOT,FULL,BASIS,ANNOTATIONS

PREVIOUS='data/semantic-review-index-v23.json'
INDEX='data/semantic-review-index-v24.json'
FORMAL='reports/courageous-undertaking-v1.json'
READING='docs/courageous-undertaking-v1.md'


def encoded(value):return json.dumps(value,ensure_ascii=False,indent=2)+'\n'


def build():
    old_index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));load_reviews(ROOT,PREVIOUS)
    old_active=old_index['works']['kant-1784'];old_cat=load_catalog(ROOT,old_active['meaning_basis']);cat=load_catalog(ROOT,BASIS)
    formal=json.loads((ROOT/FORMAL).read_text(encoding='utf-8'));validate_hashes(ROOT,formal['source_sha256'])
    assert formal['structure']['eight_review_bindings_preserved'] and formal['structure']['changed_statement_indices']==[1]
    paths=set(cat.source_sha256)|set(formal['source_sha256'])|{FULL,BASIS,ANNOTATIONS,FORMAL,READING,
        'scripts/register_courageous_undertaking_reviews.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};outputs={};migrated=[]
    for path in old_active['reviews']:
        old=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in old['selection']['statements']]
        assert 1 not in indices and selection_binding(old_cat,indices)==old['selection']==selection_binding(cat,indices)
        new=deepcopy(old);new.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
            revalidated_from=path,revalidation='Selected statements, transitive definitions and meaning conventions are unchanged; no review of the changed opening paragraph is added.')
        new['evidence']['formal_checks'].append(FORMAL);new['evidence']['semantic_reading'].append(READING)
        new['source_sha256'].update(pins);new['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/courageous-undertaking-inherited-'+old['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(new);migrated.append(name)
    assert len(migrated)==8
    index=deepcopy(old_index);index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,
        identifier_annotations=ANNOTATIONS,reviews=migrated)
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(body.encode('utf-8')) for p,body in outputs.items()})
    outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    old=load_reviews(ROOT,PREVIOUS);new=load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']};after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(after)==set(before) and len(after)==8
    assert sum(r['source_nonblank_characters'] for r in after.values())==166
    assert 'kant-1784:u0008' not in after and new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        prior=json.loads((ROOT/row['review']).read_text(encoding='utf-8'));current=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        for key in ('selection','source','decision','reviewer','interpretation','requirements','unresolved'):
            assert current[key]==prior[key],(unit,key)
        assert current['revalidated_from']==row['review']
    assert new['semantic_equivalence_automatically_proved'] is False
    return dict(previous_reviews_preserved=8,reviewed_nonblank_characters=166,new_whole_unit_judgments=0,
        opening_paragraph_still_unreviewed=True)


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
