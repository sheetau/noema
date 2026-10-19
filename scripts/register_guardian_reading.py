"""Adopt the reviewed guardian sentence without adding a whole-unit review."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_guardian_reading import ROOT,FULL,BASIS,ANNOTATIONS
from scripts.check_guardian_reading import REPORT,AUDIT,DOC,INDEX as PREVIOUS

INDEX='data/semantic-review-index-v67.json'
STATUS='data/guardian-reading-status-v1.json'


def encoded(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'


def build():
    load_reviews(ROOT,PREVIOUS)
    index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));active=index['works']['kant-1784']
    old,new=load_catalog(ROOT,active['meaning_basis']),load_catalog(ROOT,BASIS)
    report=json.loads((ROOT/REPORT).read_text(encoding='utf-8'));reading=json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))
    for record in (report,reading):validate_hashes(ROOT,record['source_sha256'])
    assert report['structure']['preserved_review_selections']==11 and report['structure']['new_statements']==[45]
    assert report['whole_sentence_semantically_verified'] and reading['whole_sentence_semantically_verified']
    assert reading['selection']==selection_binding(new,[7,8,44,45])
    count=reading['source']['nonblank_characters'];assert report['new_verified_sentence_characters']==count
    paths=set(new.source_sha256)|set(report['source_sha256'])|set(reading['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,REPORT,AUDIT,DOC,'scripts/register_guardian_reading.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};outputs={};migrated=[]
    for path in active['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        before,after=selection_binding(old,indices),selection_binding(new,indices)
        assert before==review['selection']==after and 45 not in indices
        revised=deepcopy(review)
        revised.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,selection=after,
            revalidated_from=path,revalidation='The existing 45 statements, all prior declarations and their meaning conventions remain unchanged, including inherited provenance. Added statement 45 presents focused assurance and ordered addition outside these eleven reviews. The whole guardian sentence has a separate stated-reading judgment; it is not added as a whole-unit review.')
        revised['evidence']['formal_checks'].append(REPORT);revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins);revised['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/guardian-reading-inherited-'+review['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(revised);migrated.append((review['unit'],name))
    outputs[STATUS]=encoded(dict(status='guardian_sentence_reviewed_under_stated_reading',document=FULL,source_reading=AUDIT,
        changed_definitions=[],changed_meanings=[],new_statements=[45],whole_sentence_semantically_verified=True,
        new_verified_sentence_characters=count,inherited_review_count=11,new_whole_unit_reviews=0,new_covered_characters=0,
        purpose_reading='Existing distributive same-act purpose; directed participation remains a comparison, not an adopted claim.',
        resolved=['確言の焦点と、負担の背景から危険判断への追加を区別した','後見人の一文全体を明示した読解の下で照合した'],
        remaining=['第二段落後半と段落全体','二作品全文','基本関係の構成的説明の拡充'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (REPORT,AUDIT,DOC)}))
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
        assert all(a[k]==b[k] for k in ('source','decision','reviewer','interpretation','requirements','unresolved','selection'))
        assert b['revalidated_from']==row['review']
    assert not new['semantic_equivalence_automatically_proved']
    r=json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))
    return dict(previous_reviews_preserved=11,new_whole_unit_reviews=0,reviewed_nonblank_characters=1001,
        new_statements=[45],new_verified_sentence_characters=r['new_verified_sentence_characters'],automatic_equivalence_proof=False)


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
