"""Preserve unit judgments while adopting and reviewing the fourth sentence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes
from scripts.compose_fourth_sentence import ROOT, FULL, BASIS, ANNOTATIONS
from scripts.check_fourth_sentence import INDEX as PREVIOUS, REPORT, AUDIT, DOC

INDEX = 'data/semantic-review-index-v112.json'
REVALIDATION = 'Eleven definitions and no new primitives adopt the fourth sentence with six nonliteral correspondences and a fixed referenced activity kind. Only statements 13 and 53 change; the other 52 statements and all inherited declarations and meanings remain unchanged. Twelve unit judgments and the first three sentence judgments of 408 nonblank characters are preserved. The fourth sentence adds 136 characters of assistant review under an explicit reading, for 544 across the first four sentences. One previously uncovered comma is added to candidate coverage; no new whole-unit completion is claimed.'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
def encoded(value): return json.dumps(value, ensure_ascii=False, indent=2)+'\n'


@lru_cache(None)
def previous_reviews(): return load_reviews(ROOT, PREVIOUS)


def build():
    previous_reviews()
    index=read(PREVIOUS);active=index['works']['kant-1784']
    old,new=load_catalog(ROOT,active['meaning_basis']),load_catalog(ROOT,BASIS)
    report,reading=read(REPORT),read(AUDIT)
    for r in (report,reading):validate_hashes(ROOT,r['source_sha256'])
    assert report['structure']['preserved_review_selections']==12
    assert len(old.document['statements'])==len(new.document['statements'])==54
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[13,53]
    assert new.document['statements'][10]==old.document['statements'][10]
    assert new.document['statements'][52]==old.document['statements'][52]
    assert report['whole_sentence_semantically_verified'] and report['new_verified_sentence_characters']==136
    assert report['preserved_reviewed_sentence_characters']==408 and report['paragraph_reviewed_sentence_characters']==544
    assert not report['whole_unit_semantically_verified'] and report['new_covered_characters']==1
    paths=set(new.source_sha256)|set(report['source_sha256'])|set(reading['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,REPORT,AUDIT,DOC,'scripts/register_fourth_sentence.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)}
    outputs={};migrated=[]
    for path in active['reviews']:
        review=read(path);ids=[r['index'] for r in review['selection']['statements']]
        assert review['selection']==selection_binding(old,ids)==selection_binding(new,ids)
        revised=deepcopy(review)
        revised.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,revalidated_from=path,revalidation=REVALIDATION)
        revised['evidence']['formal_checks'].append(REPORT);revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins);revised['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/fourth-sentence-inherited-'+review['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(revised);migrated.append(name)
    index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,reviews=migrated)
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(s.encode('utf-8')) for p,s in outputs.items()})
    outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    before,after=previous_reviews(),load_reviews(ROOT,INDEX)
    a,b=before['works']['kant-1784'],after['works']['kant-1784']
    assert [r['unit'] for r in a]==[r['unit'] for r in b] and len(b)==12
    assert sum(r['source_nonblank_characters'] for r in b)==2212
    assert before['works']['einstein-1905']==after['works']['einstein-1905']==[]
    for first,last in zip(a,b):
        old,new=read(first['review']),read(last['review'])
        assert all(old[k]==new[k] for k in ('source','selection','decision','reviewer','interpretation','limits','requirements','unresolved'))
        assert new['revalidated_from']==first['review'] and new['revalidation']==REVALIDATION
    return dict(previous_reviews_preserved=12,reviewed_nonblank_characters=2212,new_whole_unit_reviews=0,
                new_verified_sentence_characters=136,preserved_reviewed_sentence_characters=408,paragraph_reviewed_sentence_characters=544,new_aligned_candidate_characters=1,
                automatic_equivalence_proof=False)


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)
