"""Carry unchanged meanings across the removal of a superseded statement."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_defeasible_learning import ROOT,FULL,BASIS,ANNOTATIONS,new_index,reindex_binding
from scripts.check_defeasible_learning import INDEX as PREVIOUS,REPORT,AUDIT,DOC

INDEX='data/semantic-review-index-v86.json'
REVALIDATION='The learning prospect now separates hypothetical trial backgrounds from epistemic plausibility and outcome. Old statements 37 and 50 are revised; superseded old statement 39 is removed. The other 49 statements and all previous declarations and meaning conventions remain unchanged. Seven definitions and two contextual relations are added. All eleven reviewed units and the six reviewed opening sentences retain their statement hashes and dependency meanings; indices after old statement 39 decrease by one. No new whole-sentence or whole-unit completion is added.'


def encoded(value):return json.dumps(value,ensure_ascii=False,indent=2)+'\n'


def build():
    load_reviews(ROOT,PREVIOUS)
    index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));active=index['works']['kant-1784']
    old,new=load_catalog(ROOT,active['meaning_basis']),load_catalog(ROOT,BASIS)
    report=json.loads((ROOT/REPORT).read_text(encoding='utf-8'));reading=json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))
    for record in (report,reading):validate_hashes(ROOT,record['source_sha256'])
    assert report['structure']['preserved_review_selections']==11 and report['structure']['preserved_statements']==49
    assert len(old.document['statements'])==52 and len(new.document['statements'])==51
    assert [i for i,s in enumerate(old.document['statements']) if i!=39 and s!=new.document['statements'][new_index(i)]]==[37,50]
    assert report['structure']['preserved_reviewed_sentence_characters']==1021
    assert not report['whole_sentence_semantically_verified'] and not reading['whole_sentence_semantically_verified']
    assert reading['selection']==selection_binding(new,[37,49]) and report['new_verified_sentence_characters']==0
    paths=set(new.source_sha256)|set(report['source_sha256'])|set(reading['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,REPORT,AUDIT,DOC,'scripts/register_defeasible_learning.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};outputs={};migrated=[]
    for path in active['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        assert not set(indices)&{37,39,50} and selection_binding(old,indices)==review['selection']
        binding=selection_binding(new,[new_index(i) for i in indices]);assert binding==reindex_binding(review['selection'])
        revised=deepcopy(review)
        revised.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,selection=binding,
            revalidated_from=path,revalidation=REVALIDATION)
        revised['evidence']['formal_checks'].append(REPORT);revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins);revised['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/defeasible-learning-inherited-'+review['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(revised);migrated.append((review['unit'],name))
    index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        reviews=[p for _,p in sorted(migrated)])
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(s.encode('utf-8')) for p,s in outputs.items()})
    outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    old,new=load_reviews(ROOT,PREVIOUS),load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']};after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(before)==set(after) and len(after)==11
    assert sum(r['source_nonblank_characters'] for r in after.values())==1001
    assert new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        a=json.loads((ROOT/row['review']).read_text(encoding='utf-8'));b=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k]==b[k] for k in ('source','decision','reviewer','interpretation','requirements','unresolved'))
        assert b['selection']==reindex_binding(a['selection'])
        assert b['revalidated_from']==row['review'] and b['revalidation']==REVALIDATION
    assert not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=11,new_whole_unit_reviews=0,reviewed_nonblank_characters=1001,
        revised_statements=[37,49],removed_old_statement=39,new_verified_sentence_characters=0,automatic_equivalence_proof=False)


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
