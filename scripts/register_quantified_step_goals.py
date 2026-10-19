"""Pin quantified goal alternatives without changing adopted source claims."""
from copy import deepcopy
import json
from noema.semantic_reviews import digest,load_reviews,validate_hashes
from scripts.check_quantified_step_goals import ROOT,INDEX as PREVIOUS,REPORT,READING,DOC

INDEX='data/semantic-review-index-v72.json'


def build():
    before=load_reviews(ROOT,PREVIOUS)
    index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'))
    report=json.loads((ROOT/REPORT).read_text(encoding='utf-8'));validate_hashes(ROOT,report['source_sha256'])
    assert report['structure']['active_manuscript_unchanged']
    assert report['norms']['countermodel']['values']==[False,True]
    assert report['undertaking']['existential_witnesses_not_sought_when_quoting_goal']
    assert not report['whole_sentence_semantically_verified'] and report['new_verified_sentence_characters']==0
    works=deepcopy(index['works'])
    for path,value in report['source_sha256'].items():
        assert path not in index['source_sha256'] or index['source_sha256'][path]==value,path
        index['source_sha256'][path]=value
    for path in (PREVIOUS,REPORT,READING,DOC,'scripts/register_quantified_step_goals.py'):
        index['source_sha256'][path]=digest((ROOT/path).read_bytes())
    assert index['works']==works and len(before['works']['kant-1784'])==11
    return json.dumps(index,ensure_ascii=False,indent=2)+'\n'


def main():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/INDEX,build())
    assert load_reviews(ROOT,PREVIOUS)['works']==load_reviews(ROOT,INDEX)['works']
    print('Quantified goals pinned; adopted manuscripts and eleven reviews unchanged',flush=True)


if __name__=='__main__':main()
