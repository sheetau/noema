"""Register the comparison without revising adopted text or review decisions."""
from copy import deepcopy
import json
from noema.semantic_reviews import digest,load_reviews,validate_hashes
from scripts.check_scoped_quiet import ROOT,INDEX as PREVIOUS,REPORT,READING,DOC

INDEX='data/semantic-review-index-v74.json'


def build():
    before=load_reviews(ROOT,PREVIOUS)
    index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'))
    report=json.loads((ROOT/REPORT).read_text(encoding='utf-8'));validate_hashes(ROOT,report['source_sha256'])
    assert report['structure']['active_manuscript_unchanged'] and not report['structure']['source_adoption']
    assert report['scope']['malformed_scope_is_neither_presence_nor_absence']
    assert report['independence']['outward_and_inner_readings_independent']
    assert not report['whole_sentence_semantically_verified'] and report['new_verified_sentence_characters']==0
    works=deepcopy(index['works'])
    for path,value in report['source_sha256'].items():
        assert path not in index['source_sha256'] or index['source_sha256'][path]==value,path
        index['source_sha256'][path]=value
    for path in (PREVIOUS,REPORT,READING,DOC,'scripts/register_scoped_quiet.py'):
        index['source_sha256'][path]=digest((ROOT/path).read_bytes())
    assert index['works']==works and len(before['works']['kant-1784'])==11
    return json.dumps(index,ensure_ascii=False,indent=2)+'\n'


def main():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/INDEX,build())
    assert load_reviews(ROOT,PREVIOUS)['works']==load_reviews(ROOT,INDEX)['works']
    print('Scoped absence comparison pinned; adopted manuscript and eleven reviews unchanged',flush=True)


if __name__=='__main__':main()
