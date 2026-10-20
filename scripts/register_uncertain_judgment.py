"""Preserve registered judgments while adding an unasserted uncertain-judgment conditional."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes
from scripts.compose_uncertain_judgment import ROOT, FULL, BASIS, ANNOTATIONS
from scripts.check_uncertain_judgment import INDEX as PREVIOUS, REPORT, AUDIT, DOC

INDEX = 'data/semantic-review-index-v108.json'
REVALIDATION = 'Ten definitions and seven interpretation inputs add an unasserted uncertain-judgment consequence and bind it to the prior abandonment antecedent. All 54 authored statements and inherited declarations and meanings remain unchanged. Twelve unit judgments and the first three sentence judgments of 408 nonblank characters are preserved. No new source coverage or semantic completion is claimed.'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
def encoded(value): return json.dumps(value, ensure_ascii=False, indent=2)+'\n'


def build():
    load_reviews(ROOT, PREVIOUS)
    index=read(PREVIOUS);active=index['works']['kant-1784']
    old,new=load_catalog(ROOT,active['meaning_basis']),load_catalog(ROOT,BASIS)
    report,reading=read(REPORT),read(AUDIT)
    for r in (report,reading):validate_hashes(ROOT,r['source_sha256'])
    assert report['structure']['preserved_review_selections']==12
    assert len(old.document['statements'])==len(new.document['statements'])==54
    assert old.document['statements']==new.document['statements']
    assert new.document['statements'][10]==old.document['statements'][10]
    assert new.document['statements'][52]==old.document['statements'][52]
    assert not report['whole_sentence_semantically_verified'] and report['new_verified_sentence_characters']==0
    assert not report['whole_unit_semantically_verified'] and report['new_covered_characters']==0
    paths=set(new.source_sha256)|set(report['source_sha256'])|set(reading['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,REPORT,AUDIT,DOC,'scripts/register_uncertain_judgment.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)}
    outputs={};migrated=[]
    for path in active['reviews']:
        review=read(path);ids=[r['index'] for r in review['selection']['statements']]
        assert review['selection']==selection_binding(old,ids)==selection_binding(new,ids)
        revised=deepcopy(review)
        revised.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,revalidated_from=path,revalidation=REVALIDATION)
        revised['evidence']['formal_checks'].append(REPORT);revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins);revised['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/uncertain-judgment-inherited-'+review['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(revised);migrated.append(name)
    index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,reviews=migrated)
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(s.encode('utf-8')) for p,s in outputs.items()})
    outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    before,after=load_reviews(ROOT,PREVIOUS),load_reviews(ROOT,INDEX)
    a,b=before['works']['kant-1784'],after['works']['kant-1784']
    assert [r['unit'] for r in a]==[r['unit'] for r in b] and len(b)==12
    assert sum(r['source_nonblank_characters'] for r in b)==2212
    assert before['works']['einstein-1905']==after['works']['einstein-1905']==[]
    for first,last in zip(a,b):
        old,new=read(first['review']),read(last['review'])
        assert all(old[k]==new[k] for k in ('source','selection','decision','reviewer','interpretation','limits','requirements','unresolved'))
        assert new['revalidated_from']==first['review'] and new['revalidation']==REVALIDATION
    return dict(previous_reviews_preserved=12,reviewed_nonblank_characters=2212,new_whole_unit_reviews=0,
                new_verified_sentence_characters=0,preserved_reviewed_sentence_characters=408,new_aligned_candidate_characters=0,
                automatic_equivalence_proof=False)


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)
