"""Adopt agent-scoped effort, preserving eleven whole-unit reviews."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_effort_agents import ROOT,FULL,BASIS,ANNOTATIONS
from scripts.check_effort_agents import REPORT,AUDIT,DOC,INDEX as PREVIOUS,substantive

INDEX='data/semantic-review-index-v52.json'
STATUS='data/effort-agents-status-v1.json'

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
    assert report['structure']['affected_statements']==[4,42]
    paths=set(new.source_sha256)|set(report['source_sha256'])|set(reading['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,REPORT,AUDIT,DOC,'scripts/register_effort_agents.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)}
    outputs={};migrated=[]
    for path in active['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'))
        indices=[r['index'] for r in review['selection']['statements']]
        before,after=selection_binding(old,indices),selection_binding(new,indices)
        assert before==review['selection'] and before['statements']==after['statements']
        assert before['dependencies']==after['dependencies'] and not {4,42} & set(indices)
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in before['dependencies'])
        revised=deepcopy(review)
        revised.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,selection=after,
            revalidated_from=path,revalidation='Selected statements and their complete transitive declaration and meaning dependencies are unchanged, excluding only meaning_basis and declaration_document provenance. The former primitive sk is defined by identifying the effort agent with the person served by the method. This affects statements 4 and 42, outside these eleven reviews. Selection hashes are rebound to the new full snapshot.')
        revised['evidence']['formal_checks'].append(REPORT)
        revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins)
        revised['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/effort-agents-inherited-'+review['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(revised);migrated.append((review['unit'],name))
    outputs[STATUS]=encoded(dict(status='personal_effort_defined_by_agent_identity',document=FULL,source_reading=AUDIT,
        changed_definitions=['sk'],changed_meanings=['sk'],affected_statements=[4,42],
        resolved=['方法の対象となる本人と努力を担う実施者を別引数で結んだ',
            '本人の努力不要と他者の努力の有無を独立に扱える'],
        remaining=['原文に即した目的と努力の種類・方法と結果の評価範囲',
            '名詞と仕事の語義、焦点と反語の談話上の扱い',
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
        changed_definitions=['sk'],affected_statements=[4,42],automatic_equivalence_proof=False)

def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
