"""Register a general composition and source countermodels, retaining judgments."""
from copy import deepcopy
import json
from noema.semantic_reviews import digest, load_reviews, validate_hashes
from scripts.check_frequency_variation import ROOT, INDEX as PREVIOUS, REPORT, AUDIT, CORE, DOC, reading

INDEX='data/semantic-review-index-v83.json'


def build():
    before=load_reviews(ROOT,PREVIOUS)
    old=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'))
    report=json.loads((ROOT/REPORT).read_text(encoding='utf-8'))
    assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading()
    validate_hashes(ROOT,report['source_sha256'])
    assert report['structure']['current_selection_bound']
    assert [r['values'] for r in report['source']['independent_conditions']]==[
        [False,False],[False,True],[True,False],[True,True]]
    assert not report['whole_sentence_semantically_verified']
    assert report['new_verified_sentence_characters']==report['new_covered_characters']==0
    new=deepcopy(old)
    paths=set(report['source_sha256'])|{PREVIOUS,REPORT,AUDIT,CORE,DOC,'scripts/register_frequency_variation.py'}
    for p in sorted(paths):
        value=digest((ROOT/p).read_bytes())
        if p in new['source_sha256']: assert new['source_sha256'][p]==value,p
        new['source_sha256'][p]=value
    assert new['works']==old['works']
    assert len(before['works']['kant-1784'])==11 and before['works']['einstein-1905']==[]
    return json.dumps(new,ensure_ascii=False,indent=2)+'\n'


def main():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/INDEX,build())
    old,new=load_reviews(ROOT,PREVIOUS),load_reviews(ROOT,INDEX)
    assert old['works']==new['works']
    assert all(new['source_sha256'][p]==h for p,h in old['source_sha256'].items())
    print('General composition and four native countermodels registered; 11 judgments unchanged',flush=True)


if __name__=='__main__': main()
