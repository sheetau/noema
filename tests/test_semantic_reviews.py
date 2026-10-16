"""Review provenance must not silently certify partial or stale manuscripts."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,load_reviews,selection_binding,REQUIREMENTS
from scripts.audit_written_progress_reviewed import apply_reviews


def write(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def pin(root,name):return digest((root/name).read_bytes())


@pytest.fixture
def corpus(tmp_path):
    root=tmp_path
    (root/'text.noema').write_text('p:r aa[] c.s[k aa[]].\n',encoding='utf-8',newline='\n')
    write(root,'basis.json',dict(document='text.noema',primitives=[dict(symbol='aa',parameters=[],result='truth',arguments=[],meaning_ja='A declared condition.')],definitions={}))
    unit=dict(id='sample:u0001',kind='body',text='Source.',text_sha256=digest(b'Source.'),math_ids=[])
    write(root,'inventory.json',dict(units=[unit],math=[]))
    write(root,'evidence.json',dict(status='explicit_test_evidence',source_sha256={'text.noema':pin(root,'text.noema')}))
    (root/'reading.md').write_text('Explicit whole-unit reading with stated assumptions.\n',encoding='utf-8',newline='\n')
    active=dict(document='text.noema',meaning_basis='basis.json',identifier_annotations=None,source_inventory='inventory.json',reviews=['review.json'])
    review=dict(schema_version='noema-semantic-review-1',work='sample',unit=unit['id'],document='text.noema',meaning_basis='basis.json',identifier_annotations=None,
        source=dict(inventory='inventory.json',unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=[]),
        selection=selection_binding(load_catalog(root,'basis.json'),[0]),decision='equivalent_under_stated_reading',reviewer='assistant_review',
        interpretation=['Explicit reading.'],limits=['No automatic proof of the reading.'],unresolved=[],
        requirements=[dict(id=name,decision='satisfied',reason='Explicit reviewer reasoning.') for name in REQUIREMENTS],
        evidence=dict(source_reading=['reading.md'],formal_checks=['evidence.json'],semantic_reading=['reading.md']),
        source_sha256={p:pin(root,p) for p in ('text.noema','basis.json','inventory.json','evidence.json','reading.md')})
    write(root,'review.json',review)
    index=dict(schema_version='noema-semantic-review-index-1',works={'sample':active},source_sha256={p:pin(root,p) for p in ('text.noema','basis.json','inventory.json','review.json')})
    write(root,'index.json',index)
    return root


def change_review(root,mutation):
    review=json.loads((root/'review.json').read_text(encoding='utf-8'));mutation(review);write(root,'review.json',review)
    index=json.loads((root/'index.json').read_text(encoding='utf-8'));index['source_sha256']['review.json']=pin(root,'review.json');write(root,'index.json',index)


def test_registered_judgment_remains_a_judgment_not_automatic_proof(corpus):
    result=load_reviews(corpus,'index.json')
    assert result['works']['sample'][0]['unit']=='sample:u0001'
    assert result['semantic_equivalence_automatically_proved'] is False


@pytest.mark.parametrize('mutation,reason',[
    (lambda r:r['source'].update(range=[0,3]),'whole unit'),
    (lambda r:r['source'].update(range=[False,7]),'whole unit'),
    (lambda r:r['source'].update(text='Changed'), 'source text'),
    (lambda r:r.update(document='old.noema'),'active document'),
    (lambda r:r.update(unresolved=['Unexplained noun']), 'unresolved'),
    (lambda r:r['requirements'].pop(), 'requirements'),
    (lambda r:r['requirements'][0].update(reason=''), 'reason'),
    (lambda r:r.update(decision='tests_passed'), 'positive whole-unit'),
    (lambda r:r['selection']['statements'][0].update(sha256='0'*64), 'statements or dependency'),
    (lambda r:r['selection'].update(dependency_sha256='0'*64), 'statements or dependency'),
    (lambda r:r['source_sha256'].pop('text.noema'), 'Unpinned'),
    (lambda r:r['source_sha256'].update({'../escape.txt':'0'*64}), 'escapes root'),
])
def test_incomplete_stale_or_unreasoned_reviews_are_rejected(corpus,mutation,reason):
    change_review(corpus,mutation)
    with pytest.raises(ValueError,match=reason):load_reviews(corpus,'index.json')


def test_changed_evidence_is_rejected_even_if_review_is_unchanged(corpus):
    (corpus/'reading.md').write_text('Different interpretation.',encoding='utf-8')
    with pytest.raises(ValueError,match='input changed'):load_reviews(corpus,'index.json')


def test_changed_active_document_is_rejected(corpus):
    (corpus/'text.noema').write_text('p:r aa[] c.q[k aa[]].',encoding='utf-8')
    with pytest.raises(ValueError,match='input changed'):load_reviews(corpus,'index.json')


def test_duplicate_registered_unit_is_rejected(corpus):
    index=json.loads((corpus/'index.json').read_text(encoding='utf-8'))
    index['works']['sample']['reviews'].append('review.json');write(corpus,'index.json',index)
    with pytest.raises(ValueError,match='Duplicate reviewed unit'):load_reviews(corpus,'index.json')


def test_evidence_must_pin_its_own_dependencies_transitively(corpus):
    (corpus/'extra.txt').write_text('Input omitted by review',encoding='utf-8')
    write(corpus,'evidence.json',dict(source_sha256={'extra.txt':pin(corpus,'extra.txt')}))
    change_review(corpus,lambda r:r['source_sha256'].update({'evidence.json':pin(corpus,'evidence.json')}))
    with pytest.raises(ValueError,match='omits or changes evidence input'):load_reviews(corpus,'index.json')


def test_all_math_in_whole_unit_requires_review(corpus):
    inv=json.loads((corpus/'inventory.json').read_text(encoding='utf-8'));inv['units'][0]['math_ids']=['M0001']
    inv['math']=[dict(id='M0001',mathml='<math/>',sha256=digest(b'<math/>'))];write(corpus,'inventory.json',inv)
    change_review(corpus,lambda r:r['source_sha256'].update({'inventory.json':pin(corpus,'inventory.json')}))
    index=json.loads((corpus/'index.json').read_text(encoding='utf-8'));index['source_sha256']['inventory.json']=pin(corpus,'inventory.json');write(corpus,'index.json',index)
    with pytest.raises(ValueError,match='all unit math'):load_reviews(corpus,'index.json')


def test_aggregate_changes_only_review_counts_and_preserves_partial_ranges(corpus):
    reviewed=load_reviews(corpus,'index.json')
    partial=dict(works={'sample':dict(author_unit_count=2,verified_semantic_units=0,verified_semantic_percent=0.,
        explicit_text_range_percent=10,units=[dict(unit='sample:u0001'),dict(unit='sample:u0002')])},source_sha256={},method={})
    result=apply_reviews(partial,reviewed)
    assert partial['works']['sample']['verified_semantic_units']==0
    assert result['works']['sample']['verified_semantic_units']==1
    assert result['works']['sample']['verified_semantic_percent']==50
    assert result['works']['sample']['explicit_text_range_percent']==10
    bad=deepcopy(reviewed);bad['works']['sample'].append(bad['works']['sample'][0])
    with pytest.raises(ValueError,match='repeated reviewed'):apply_reviews(partial,bad)


def test_duplicate_json_keys_are_rejected(corpus):
    (corpus/'index.json').write_text('{"works":{},"works":{}}',encoding='utf-8')
    with pytest.raises(ValueError,match='Duplicate JSON key'):load_reviews(corpus,'index.json')


def test_registered_signature_is_bound_to_current_manuscript_and_annotations():
    root=Path(__file__).resolve().parents[1]
    result=load_reviews(root,'data/semantic-review-index-v1.json')
    assert [r['unit'] for r in result['works']['kant-1784']]==['kant-1784:u0018']
    assert result['works']['einstein-1905']==[]
    assert result['works']['kant-1784'][0]['source_nonblank_characters']==16
