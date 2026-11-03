from functools import lru_cache
from scripts.check_kant_passage_anchor_spellings import build_report
from scripts.kant_passage_anchor_context import passage_context
from scripts.kant_reference_anchor_context import anchor_context
from scripts.kant_lexical_context import LexicalContext

report=lru_cache(maxsize=1)(build_report)


def test_all_existing_meanings_referents_and_aliases_are_retained():
    old,new=anchor_context(),passage_context()
    assert new.document==old.document
    assert new.declarations==old.declarations
    assert all(new.spellings.get(parts)==name for parts,name in old.spellings.items())
    assert len(new.declared_spellings)==len(old.declared_spellings)+11
    published=new.published()
    assert published['native']['statements']==[]
    assert LexicalContext.from_published(published).published()==published


def test_each_new_name_recovers_the_same_symbol_from_fewer_circles():
    rows=report()['words']
    assert len(rows)==11
    assert all(r['exact'] and r['circles']<r['before_circles'] for r in rows)


def test_density_comparison_covers_all_forty_sources_without_claiming_rendering():
    result=report()
    assert len(result['density'])==40
    assert result['before_predicted_circles']==2669
    assert result['predicted_circles']<2669
    assert len(result['changed_statements'])==16


def test_actual_sources_recover_with_multiple_branches_and_fewer_circles():
    rows=report()['actual_bodies']
    assert [r['statement'] for r in rows]==[5,9]
    assert all(r['exact'] and r['circles']<r['before_circles'] and r['branches']>0 for r in rows)
