"""Adopt actual guardian causation, preserving all eleven whole-unit reviews."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_guardian_causation import ROOT,FULL,BASIS,ANNOTATIONS
from scripts.check_guardian_causation import REPORT,AUDIT,DOC,INDEX as PREVIOUS,substantive

INDEX='data/semantic-review-index-v62.json'
STATUS='data/guardian-causation-status-v1.json'

def encoded(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'

def build():
    load_reviews(ROOT,PREVIOUS)
    index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'))
    active=index['works']['kant-1784']
    old,new=load_catalog(ROOT,active['meaning_basis']),load_catalog(ROOT,BASIS)
    report=json.loads((ROOT/REPORT).read_text(encoding='utf-8'))
    reading=json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))
    for record in (report,reading):validate_hashes(ROOT,record['source_sha256'])
    assert report['structure']['preserved_review_meanings']==11
    assert report['structure']['affected_statements']==[7]
    paths=set(new.source_sha256)|set(report['source_sha256'])|set(reading['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,REPORT,AUDIT,DOC,'scripts/register_guardian_causation.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)}
    outputs={};migrated=[]
    for path in active['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'))
        indices=[r['index'] for r in review['selection']['statements']]
        before,after=selection_binding(old,indices),selection_binding(new,indices)
        assert before==review['selection'] and before['statements']==after['statements']
        assert before['dependencies']==after['dependencies'] and 7 not in indices
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in before['dependencies'])
        revised=deepcopy(review)
        revised.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,selection=after,
            revalidated_from=path,revalidation='Selected statements and their complete transitive declaration and meaning dependencies are unchanged, excluding only meaning_basis and declaration_document provenance. The revised do and added rqyb, rqyc and rqyd affect only statement 7, outside these eleven reviews. Selection hashes are rebound to the new full snapshot.')
        revised['evidence']['formal_checks'].append(REPORT)
        revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins)
        revised['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/guardian-causation-inherited-'+review['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(revised);migrated.append((review['unit'],name))
    outputs[STATUS]=encoded(dict(status='actual_contribution_to_judgments_adopted',document=FULL,source_reading=AUDIT,
        changed_definitions=['do'],changed_meanings=['do'],affected_statements=[7],
        resolved=['実際の因果的寄与を説明への採用から分けた',
            '危険判断だけの分布を因果結果とし、負担の挿入説明を分けた'],
        remaining=['目的的な働きかけとの接続、監督の語義とgütigst・schon・auchの働き',
            '第二段落全体の読解','後続本文とアインシュタイン全文'],
        inherited_review_count=11,new_whole_unit_reviews=0,new_covered_characters=0,
        first_cause_sentence_meanings_unchanged=True,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (REPORT,AUDIT,DOC)}))
    index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        reviews=[p for _,p in sorted(migrated)])
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(s.encode('utf-8')) for p,s in outputs.items()})
    outputs[INDEX]=encoded(index)
    return outputs

def audit_registration():
    old,new=load_reviews(ROOT,PREVIOUS),load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']}
    after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(before)==set(after) and len(after)==11
    assert sum(r['source_nonblank_characters'] for r in after.values())==1001
    assert new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        a=json.loads((ROOT/row['review']).read_text(encoding='utf-8'))
        b=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k]==b[k] for k in ('source','decision','reviewer','interpretation','requirements','unresolved'))
        assert a['selection']['statements']==b['selection']['statements']
        assert a['selection']['dependencies']==b['selection']['dependencies']
        assert a['selection']!=b['selection'] and b['revalidated_from']==row['review']
    assert not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=11,new_whole_unit_reviews=0,reviewed_nonblank_characters=1001,
        changed_definitions=['do'],affected_statements=[7],automatic_equivalence_proof=False)

def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
